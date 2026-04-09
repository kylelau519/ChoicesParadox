import json
from dataclasses import dataclass
from typing import Dict, List

from .player import Character
from .reader import RawData


# Player Snapshot is a snapshot of the player's state
# When a choice is given,this should contain all the info needed to do stat analysis
# This is constructed from reader
@dataclass
class PlayerSnapshot:
    character: Character
    current_hp: int
    max_hp: int
    current_gold: int
    deck: Dict[str, int]  # card id to count
    max_potion_slot_count: int
    potions: List[str]  # potion ids
    relics: List[str]

    @classmethod
    def last(self, player_id: int = 1):
        pass

    # player's state at a specific act and floor, act starts with 1, floor starts with 1 (Neow)
    @classmethod
    def at_act_floor(cls, data: RawData, act: int, floor: int, player_id: int = 1):
        map_point = data.map_point_history[act - 1][floor - 1]
        player_stat = map_point.player_stats[
            player_id - 1
        ]  # assumed player stats are listed in order of id
        current_hp = player_stat["current_hp"]
        max_hp = player_stat["max_hp"]
        current_gold = player_stat["current_gold"]

        player = data.players[player_id - 1]
        character = player.character
        max_potion_slot_count = player.max_potion_slot_count

        # deck = deck_tracker.get_deck_at_floor(act, floor, player_id)
        # potions = potion_tracker.get_potions_at_floor(act, floor, player_id)
        # relics = relic_tracker.get_relics_at_floor(act, floor, player_id

    # lump sum floor, start with floor 1 (Neow)
    @classmethod
    def at_floor(self, floor: int, player_id: int = 1):
        pass


if __name__ == "__main__":
    data = RawData.from_file("testfiles/regent_a0_win.run")
    print(data.map_point_history[1][12])
