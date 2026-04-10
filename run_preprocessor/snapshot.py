from dataclasses import dataclass

from run_preprocessor.deck import Deck
from run_preprocessor.mappoint import RawMapPoint
from run_preprocessor.types import PlayerStats

from .player import Character, RawPlayer
from .reader import RawData


# Player Snapshot is a snapshot of the player's state
# When a choice is given,this should contain all the info needed to do stat analysis
# This is constructed from reader
@dataclass
class PlayerSnapshot:
    data: RawData
    current_floor: int
    player_id: int

    character: Character
    current_hp: int
    max_hp: int
    current_gold: int
    deck: Deck  # card id to count
    max_potion_slot_count: int
    potions: list[str]  # potion ids
    relics: list[str]

    def __init__(self, data: RawData, player_id: int = 1):
        self.data = data
        self.current_floor = 1
        self.player_id = player_id

        player: RawPlayer | None = None
        for p in data.players:
            if p.id == str(player_id):
                player = p
        if player == None:
            raise Exception("__init__: player not found in data")
        self.character = player.character
        self.max_potion_slot_count = 3 if data.run_metadata.ascension < 4 else 2

        if (
            len(data.map_point_history.map_point_history) == 0
            or len(data.map_point_history.map_point_history[0]) == 0
        ):
            raise Exception("__init__: first floor not found in data")
        first_mp: RawMapPoint = data.map_point_history.map_point_history[0][0]

        player_stat: PlayerStats | None = None
        for ps in first_mp.player_stats:
            if ps["player_id"] == player_id:
                player_stat = ps
        if player_stat == None:
            raise Exception("__init__: player not found in map point")

        self.current_hp = player_stat["current_hp"]
        self.max_hp = player_stat["max_hp"]
        self.current_gold = player_stat["current_gold"]

        starter_deck = RawPlayer.generate_starter_deck(self.character)
        self.deck = Deck(starter_deck)
        if data.run_metadata.ascension >= 5:
            self.deck.add("CARD.ASCENDERS_BANE")
        self.potions = []
        starter_relic = RawPlayer.generate_starter_relic(self.character)
        self.relics = []
        self.relics.append(starter_relic)

        self.update_deck(player_stat)
        self.update_potions(player_stat)
        self.update_relics(player_stat)

        self.current_floor += 1

    def update_deck(self, ps: PlayerStats):
        cards_gained = ps.get("cards_gained")
        if cards_gained != None:
            for card in cards_gained:
                # TODO: add enchantmented card logic
                self.deck.add_card(card)

        cards_removed = ps.get("cards_removed")
        if cards_removed != None:
            for card in cards_removed:
                # TODO: add remove enchantmented card logic
                self.deck.remove_card(card)

        cards_transformed = ps.get("cards_transformed")
        if cards_transformed != None:
            for card in cards_transformed:
                # TODO: add transform enchantmented card logic
                self.deck.remove_card(card["original_card"])
                self.deck.add_card(card["final_card"])

        upgraded_cards = ps.get("upgraded_cards")
        if upgraded_cards != None:
            for id in upgraded_cards:
                self.deck.remove(id)
                self.deck.add(f"{id}+")

        downgraded_cards = ps.get("downgraded_cards")
        if downgraded_cards != None:
            for id in downgraded_cards:
                self.deck.remove(id)
                downgraded = id.removesuffix("+")
                self.deck.add(downgraded)

    def update_potions(self, ps: PlayerStats):
        potion_choices = ps.get("potion_choices")
        if potion_choices != None:
            for potion in potion_choices:
                if potion["was_picked"]:
                    self.potions.append(potion["choice"])

        potion_used = ps.get("potion_used")
        if potion_used != None:
            for potion in potion_used:
                _ = self.potions.index(potion)
                self.potions.remove(potion)

        potion_discarded = ps.get("potion_discarded")
        if potion_discarded != None:
            for potion in potion_discarded:
                _ = self.potions.index(potion)
                self.potions.remove(potion)

    def update_relics(self, ps: PlayerStats):
        relic_choices = ps.get("relic_choices")
        if relic_choices != None:
            for relic in relic_choices:
                if relic.get("was_picked"):
                    self.relics.append(relic.get("choice"))
                    if relic == "RELIC.POTION_BELT":
                        self.max_potion_slot_count += 2

        relics_removed = ps.get("relics_removed")
        if relics_removed != None:
            for relic in relics_removed:
                _ = self.relics.index(relic)
                self.relics.remove(relic)
                if relic == "RELIC.POTION_BELT":
                    self.max_potion_slot_count -= 2

    # player's state at a specific act and floor, act starts with 1, floor starts with 1 (Neow)
    def walk_to_act_floor(
        self, from_act: int, from_floor: int, to_act: int, to_floor: int
    ):
        act_idx = from_act - 1
        floor_idx = from_floor - 1
        to_act_idx = to_act - 1
        to_floor_idx = to_floor - 1

        while act_idx <= to_act_idx:
            current_act_len = len(
                self.data.map_point_history.map_point_history[act_idx]
            )
            while (act_idx < to_act_idx and floor_idx < current_act_len) or (
                floor_idx <= to_floor_idx
            ):
                mp: RawMapPoint = self.data.map_point_history.map_point_history[
                    act_idx
                ][floor_idx]
                player_stat: PlayerStats | None = None
                for ps in mp.player_stats:
                    if ps["player_id"] == self.player_id:
                        player_stat = ps
                if player_stat == None:
                    raise Exception("__init__: player not found in map point")

                self.current_hp = player_stat["current_hp"]
                self.max_hp = player_stat["max_hp"]
                self.current_gold = player_stat["current_gold"]

                self.update_deck(player_stat)
                self.update_potions(player_stat)
                self.update_relics(player_stat)

                self.current_floor += 1
                floor_idx += 1
            floor_idx = 0
            act_idx += 1

    def floor_to_act_floor(self, floor: int):
        if floor < 1:
            raise Exception("floor_to_act_floor: floor should be at least 1")

        num_acts = len(self.data.map_point_history.map_point_history)
        num_floors_a1 = (
            len(self.data.map_point_history.map_point_history[0]) if num_acts > 0 else 0
        )
        num_floors_a2 = (
            len(self.data.map_point_history.map_point_history[1]) if num_acts > 1 else 0
        )
        num_floors_a3 = (
            len(self.data.map_point_history.map_point_history[2]) if num_acts > 2 else 0
        )

        if floor > num_floors_a1 + num_floors_a2 + num_floors_a3:
            raise Exception(
                "floor_to_act_floor: floor should be less than total floors"
            )

        act_num = 1
        floor_num = floor
        if floor_num > num_floors_a1:
            act_num += 1
            floor_num -= num_floors_a1
        if floor_num > num_floors_a2:
            act_num += 1
            floor_num -= num_floors_a2

        return act_num, floor_num

    # lump sum floor, start with floor 1 (Neow)
    def walk_to_floor(self, floor: int):
        if floor < 1:
            raise Exception("at_floor: floor should be at least 1")

        if floor < self.current_floor:
            raise Exception("at_floor: can't walk back :)")

        if floor == self.current_floor:
            return

        from_act_num, from_floor_num = self.floor_to_act_floor(self.current_floor)
        to_act_num, to_floor_num = self.floor_to_act_floor(floor)

        self.walk_to_act_floor(
            from_act=from_act_num,
            from_floor=from_floor_num,
            to_act=to_act_num,
            to_floor=to_floor_num,
        )
