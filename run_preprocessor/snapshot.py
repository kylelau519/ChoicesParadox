import logging
import os
from dataclasses import dataclass
from typing import Any, Protocol

from item_scrapper.items import POTIONS, RELICS
from run_preprocessor.card import Card
from run_preprocessor.deck import Deck
from run_preprocessor.mappoint import RawMapPoint, RawMapPointHistory
from run_preprocessor.types import RawPlayer, RawPlayerStats

from .player import Character, Player

logger = logging.getLogger(__name__)


def validate_relic_id(relic_id: str) -> str:
    relic_id = relic_id.strip().upper()
    if not relic_id.startswith("RELIC."):
        relic_id = "RELIC." + relic_id
    if relic_id not in RELICS:
        logger.error(f"Invalid relic ID: {relic_id}")
        raise ValueError(f"Invalid relic ID: {relic_id}")
    return relic_id


def validate_potion_id(potion_id: str) -> str:
    potion_id = potion_id.strip().upper()
    if not potion_id.startswith("POTION."):
        potion_id = "POTION." + potion_id
    if potion_id not in POTIONS:
        logger.error(f"Invalid potion ID: {potion_id}")
        raise ValueError(f"Invalid potion ID: {potion_id}")
    return potion_id


class RunDataCommon(Protocol):
    players: list[RawPlayer]
    run_metadata: Any  # Must have .ascension
    map_point_history: RawMapPointHistory


# Player Snapshot is a snapshot of the player's state
# When a choice is given,this should contain all the info needed to do stat analysis
# This is constructed from reader


@dataclass
class PlayerSnapshot:
    data: RunDataCommon

    player_id: int
    character: Character
    current_hp: int
    max_hp: int
    current_gold: int
    deck: Deck  # card id to count
    max_potion_slot_count: int
    potions: dict[str, int]  # potion ids
    relics: dict[str, int]

    current_act_floor: int = 1
    current_act: int = 1
    current_lumpsum_floor: int = 1

    def __init__(self, data: RunDataCommon, player_id: int = 1):
        self.data = data
        self.player_id = player_id

        player: Player | None = None
        for p in data.players:
            if p["id"] == player_id:
                player = Player.from_dict(p)
        if player is None:
            logger.error(f"Player ID {player_id} not found in data.")
            raise Exception
        self.character = player.character
        self.max_potion_slot_count = 3 if data.run_metadata.ascension < 4 else 2

        flattened_history = data.map_point_history.flatten()
        if len(flattened_history) == 0:
            logger.warning(
                "Run history is empty; cannot create PlayerSnapshot. Assuming at Neow."
            )
            return self.default()
        first_mp: RawMapPoint = data.map_point_history.map_point_history[0][0]

        try:
            player_stat: RawPlayerStats = first_mp.get_player_stat(player_id)
        except Exception as e:
            logger.error(
                f"Failed to get player stats for player {player_id} at floor 0: {e}"
            )
            raise

        self.current_hp = player_stat["current_hp"]
        self.max_hp = player_stat["max_hp"]
        self.current_gold = player_stat["current_gold"]
        self.potions = {}
        self.relics = {}

        starter_deck = Player.generate_starter_deck(self.character)
        starter_relic = Player.generate_starter_relic(self.character)
        self.deck = Deck(starter_deck)
        if data.run_metadata.ascension >= 5:
            self.deck.add("CARD.ASCENDERS_BANE")
        self.relics[starter_relic] = 1

        self.update_deck(player_stat)
        self.update_potions(player_stat)
        self.update_relics(player_stat)

    def default(self):
        self.current_hp = 0
        self.max_hp = 0
        self.current_gold = 0
        self.deck = Deck([])
        self.potions = {}
        self.relics = {}
        self.current_act_floor = 0
        self.current_act = 1
        self.current_lumpsum_floor = 0

    def update_deck(self, ps: RawPlayerStats):
        cards_gained = ps.get("cards_gained")
        if cards_gained is not None:
            for card in cards_gained:
                self.deck.add_card(Card.from_dict(card))

        cards_removed = ps.get("cards_removed")
        if cards_removed is not None:
            for card in cards_removed:
                self.deck.remove_card(Card.from_dict(card))

        cards_transformed = ps.get("cards_transformed")
        if cards_transformed is not None:
            for transform in cards_transformed:
                self.deck.remove_card(Card.from_dict(transform["original_card"]))
                self.deck.add_card(Card.from_dict(transform["final_card"]))

        downgraded_cards = ps.get("downgraded_cards")
        if downgraded_cards is not None:
            for id in downgraded_cards:
                upgraded = id + "+"
                self.deck.remove(upgraded)
                downgraded = id.removesuffix("+")
                self.deck.add(downgraded)

        upgraded_cards = ps.get("upgraded_cards")
        if upgraded_cards is not None:
            for id in upgraded_cards:
                self.deck.remove(id)
                self.deck.add(f"{id}+")

    def update_potions(self, ps: RawPlayerStats):
        potion_choices = ps.get("potion_choices")
        if potion_choices is not None:
            for potion in potion_choices:
                if potion["was_picked"]:
                    self.potions[potion["choice"]] = (
                        self.potions.get(potion["choice"], 0) + 1
                    )

        potion_used = ps.get("potion_used")
        if potion_used is not None:
            for potion in potion_used:
                self.potions[potion] = self.potions.get(potion, 0) - 1

        potion_discarded = ps.get("potion_discarded")
        if potion_discarded is not None:
            for potion in potion_discarded:
                self.potions[potion] = self.potions.get(potion, 0) - 1

    def update_relics(self, ps: RawPlayerStats):
        relic_choices = ps.get("relic_choices")
        if relic_choices is not None:
            for relic in relic_choices:
                if relic.get("was_picked"):
                    self.relics[relic["choice"]] = (
                        self.relics.get(relic["choice"], 0) + 1
                    )

        relics_removed = ps.get("relics_removed")
        if relics_removed is not None:
            for relic in relics_removed:
                self.relics[relic] = self.relics.get(relic, 0) - 1

    def update_attributes(self, ps: RawPlayerStats):
        self.current_hp = ps["current_hp"]
        self.max_hp = ps["max_hp"]
        self.current_gold = ps["current_gold"]

    def walk(self):
        next_floor = self.current_lumpsum_floor + 1
        flatten_map = self.data.map_point_history.flatten()
        if next_floor > len(flatten_map):
            logging.warning("walk: already at the end of run, can't walk anymore")
            return  # already at the end of the run, can't walk anymore
        mp: RawMapPoint = self.data.map_point_history.flatten()[next_floor - 1]
        player_stat: RawPlayerStats = mp.get_player_stat(self.player_id)

        self.update_attributes(player_stat)
        self.update_deck(player_stat)
        self.update_potions(player_stat)
        self.update_relics(player_stat)
        self.current_lumpsum_floor = next_floor
        self.update_floor()

    # lump sum floor, start with floor 1 (Neow)
    def walk_to_floor(self, floor: int):
        if floor < 1:
            logger.error(f"Requested floor {floor} is less than 1.")
            raise Exception("walk_to_floor: floor should be at least 1")

        if floor < self.current_lumpsum_floor:
            logger.error(
                f"Cannot walk backward from floor {self.current_lumpsum_floor} to {floor}."
            )
            raise Exception("walk_to_floor: can't walk back :)")

        if floor == self.current_lumpsum_floor:
            return

        while self.current_lumpsum_floor < floor:
            self.walk()

    # player's state at a specific act and floor, act starts with 1, floor starts with 1 (Neow)
    def walk_to_act_floor(self, act: int, floor_in_act: int):
        act_num_floors = self.data.map_point_history.act_num_floors
        if act < 1 or act > len(act_num_floors):
            logger.error(
                f"Requested act {act} is out of range (1-{len(act_num_floors)})."
            )
            raise Exception("walk_to_act_floor: act should be between 1 and num acts")
        if floor_in_act < 1 or floor_in_act > act_num_floors[act - 1]:
            logger.error(
                f"Requested floor {floor_in_act} is out of range for act {act} (1-{act_num_floors[act - 1]})."
            )
            raise Exception(
                "walk_to_act_floor: floor_in_act should be between 1 and num floors in act"
            )
        lump_sum_floor = sum(act_num_floors[: act - 1]) + floor_in_act
        self.walk_to_floor(lump_sum_floor)

    def update_floor(self):
        act_num_floors = self.data.map_point_history.act_num_floors
        floor = self.current_lumpsum_floor
        act = 0
        while act < len(act_num_floors) and floor > act_num_floors[act]:
            floor -= act_num_floors[act]
            act += 1
        self.current_act = act + 1
        self.current_act_floor = floor

    def is_encounter(self):
        mp: RawMapPoint = self.data.map_point_history.flatten()[
            self.current_lumpsum_floor - 1
        ]
        rooms = mp.rooms
        for room in rooms:
            model_id = room.get("model_id", "")
            if model_id and model_id.startswith("ENCOUNTER"):
                return True
        return False

    def run(self):
        while self.current_lumpsum_floor < len(self.data.map_point_history.flatten()):
            self.walk()
