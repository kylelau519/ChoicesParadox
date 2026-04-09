from dataclasses import dataclass

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
    deck: dict[str, int]  # card id to count
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
        self.deck = {}
        for card in starter_deck:
            prev_num_card = self.deck.get(card.id)
            new_num_card = prev_num_card + 1 if prev_num_card is not None else 1
            self.deck[card.id] = new_num_card
        self.potions = []
        self.relics = []

        self.update_deck(player_stat)
        self.update_potions(player_stat)
        self.update_relics(player_stat)

    def update_deck(self, ps: PlayerStats):
        # cards_gained: list[Card] | None
        # cards_removed: list[Card] | None
        # cards_transformed: list[CardTransform] | None
        # upgraded_cards: list[str] | None
        # bought_colorless: list[str] | None
        pass

    def update_potions(self, ps: PlayerStats):
        # potion_choices: list[PotionChoice] | None
        # potion_used: list[str] | None
        # potion_discarded: list[str] | None
        # bought_potions: list[str] | None
        pass

    def update_relics(self, ps: PlayerStats):
        # relic_choices: list[RelicChoice] | None
        # bought_relics: list[str] | None
        pass

    def walk(self):
        # TODO: walk should move self to the next MapPoint and update its states
        self.current_floor += 1

    # player's state at a specific act and floor, act starts with 1, floor starts with 1 (Neow)
    def walk_to_act_floor(self, act: int, floor: int):
        act_idx = 0
        floor_idx = 0
        target_act_idx = act - 1
        target_floor_idx = floor - 1

        while act_idx <= target_act_idx:
            while floor_idx <= target_floor_idx:
                self.walk()
                floor_idx += 1
            act_idx += 1

    # lump sum floor, start with floor 1 (Neow)
    def walk_to_floor(self, floor: int):
        if floor < 1:
            raise Exception("at_floor: floor should be at least 1")

        if floor < self.current_floor:
            raise Exception("at_floor: can't walk back :)")

        if floor == self.current_floor:
            return

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
            raise Exception("at_floor: floor should be less than total floors")

        act_num = 1
        floor_num = floor
        if floor_num > num_floors_a1:
            act_num += 1
            floor_num -= num_floors_a1
        if floor_num > num_floors_a2:
            act_num += 1
            floor_num -= num_floors_a2

        self.walk_to_act_floor(act=act_num, floor=floor_num)
