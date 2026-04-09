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

        player: RawPlayer | None = None
        for p in data.players:
            if p.id == str(player_id):
                player = p
        if player == None:
            raise Exception("__init__: player not found in data")
        self.character = player.character
        self.max_potion_slot_count = 3 if data.run_metadata.ascension < 4 else 2

        if (
            len(data.map_point_history.map_point_history) == 0 or
            len(data.map_point_history.map_point_history[0]) == 0
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

        # TODO: generate starter decks
        # TODO: populate deck, potions, relics
        self.deck = {}
        self.potions = []
        self.relics = []


    @classmethod
    def last(cls, player_id: int = 1):
        pass

    def walk(self):
        pass

    # player's state at a specific act and floor, act starts with 1, floor starts with 1 (Neow)
    def walk_to_act_floor(self, act: int, floor: int, player_id: int = 1):
        act_idx = 0
        floor_idx = 0
        target_act_idx = act - 1
        target_floor_idx = floor - 1

        while act_idx <= target_act_idx:
            while floor_idx <= target_floor_idx:
                self.walk()
                floor_idx += 1
            act_idx += 1

        # map_point = data.map_point_history.map_point_history[act_idx][floor_idx]
        # player_stat = map_point.player_stats[
        #     player_id - 1
        # ]  # assumed player stats are listed in order of id
        # current_hp = player_stat["current_hp"]
        # max_hp = player_stat["max_hp"]
        # current_gold = player_stat["current_gold"]
        #
        # player = data.players[player_id - 1]
        # character = player.character
        # max_potion_slot_count = player.max_potion_slot_count

        # deck = deck_tracker.get_deck_at_floor(act, floor, player_id)
        # potions = potion_tracker.get_potions_at_floor(act, floor, player_id)
        # relics = relic_tracker.get_relics_at_floor(act, floor, player_id)

    # lump sum floor, start with floor 1 (Neow)
    def walk_to_floor(self, floor: int, player_id: int = 1):
        if floor < 1:
            raise Exception("at_floor: floor should be at least 1")

        num_acts = len(data.map_point_history.map_point_history)
        num_floors_a1 = len(data.map_point_history.map_point_history[0]) if num_acts > 0 else 0
        num_floors_a2 = len(data.map_point_history.map_point_history[1]) if num_acts > 1 else 0
        num_floors_a3 = len(data.map_point_history.map_point_history[2]) if num_acts > 2 else 0

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

        self.walk_to_act_floor(act=act_num, floor=floor_num, player_id=player_id)


if __name__ == "__main__":
    data = RawData.from_file("testfiles/regent_a0_win.run")
    print(data.map_point_history[1][12])
