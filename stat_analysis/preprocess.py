# Input format for bdt onehot:
# current HP, max hp, [deck count vectorize], [potion count vectorize], [relic onehot], [encounter onehot],
# Target: damage taken in the encounter


# Convert each encounter in a run file to a trainable point

from typing import Any

import numpy as np
import sklearn
from item_scrapper.items import ALL_CARDS, ALL_ENCOUNTERS, POTIONS, RELICS
from run_preprocessor.reader import RawData
from run_preprocessor.snapshot import PlayerSnapshot
from sklearn.feature_extraction import DictVectorizer

MASTER_SCHEMA = {
    "current_hp": 0,
    "max_hp": 0,
    **ALL_CARDS,
    **POTIONS,
    **RELICS,
    **ALL_ENCOUNTERS,
}


class RunToInputConverter:
    def __init__(self, run_json: RawData, player_id: int = 1):
        self.raw_data: RawData = run_json
        self.snapshot_now: PlayerSnapshot = PlayerSnapshot(self.raw_data, player_id)
        self.snapshot_next: PlayerSnapshot = PlayerSnapshot(self.raw_data, player_id)
        self.snapshot_next.walk()

    @classmethod
    def from_file(cls, path: str, player_id: int = 1):
        raw_data: RawData = RawData.from_file(path)
        return cls(raw_data, player_id)

    # This assumed snapshot_next is at an encounter, with the damage taken applied
    def convert_snapshot(self):
        input: dict[str, int] = {}
        # Player current stat
        input["current_hp"] = self.snapshot_now.current_hp
        input["max_hp"] = self.snapshot_now.max_hp
        input.update(self.snapshot_now.deck.cards)
        input.update(self.snapshot_now.potions)
        input.update(self.snapshot_now.relics)

        # Ecnounter and the damage taken in the next encounter
        map_point = self.raw_data.map_point_history.flatten()[
            self.snapshot_next.current_lumpsum_floor - 1
        ]
        rooms = map_point.rooms
        encounters: dict[str, int] = {}
        for room in rooms:
            model_id = room.get("model_id", "")
            if model_id and model_id.startswith("ENCOUNTER"):
                encounters[model_id] = 1

        input.update(encounters)
        player_stat = map_point.get_player_stat(self.snapshot_next.player_id)
        target: dict[str, int] = {}
        damage_taken = player_stat.get("damage_taken", 0)
        target["damage_taken"] = damage_taken
        return input, target

    def walk(self):
        num_total_floors = len(self.raw_data.map_point_history.flatten())
        if self.snapshot_now.current_lumpsum_floor < num_total_floors:
            self.snapshot_now.walk()
        else:
            raise Exception("walk: snapshot_now walking too much")
        if self.snapshot_next.current_lumpsum_floor < num_total_floors:
            self.snapshot_next.walk()

    def run(self):
        inputs = []
        targets = []
        num_total_floors = len(self.raw_data.map_point_history.flatten())
        while self.snapshot_now.current_lumpsum_floor < num_total_floors:
            if self.snapshot_next.is_encounter():
                input, target = self.convert_snapshot()
                inputs.append(input)
                targets.append(target)
            self.walk()
        return inputs, targets

    def vectorize(self):
        master_vec = DictVectorizer(sparse=True).fit([MASTER_SCHEMA])
        inputs, targets = self.run()
        if len(inputs) == 0:
            return None, None
        x_run_matrix = master_vec.transform(inputs)
        y_run_array = np.array([t["damage_taken"] for t in targets])
        return x_run_matrix, y_run_array
