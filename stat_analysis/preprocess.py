# Input format for bdt onehot:
# current HP, max hp, [deck count vectorize], [potion count vectorize], [relic onehot], [encounter onehot],
# Target: damage taken in the encounter


# Convert each encounter in a run file to a trainable point

import logging
from typing import Any

import numpy as np
import scipy.sparse as sp
import sklearn
from item_scrapper.items import ALL_CARDS, ALL_ENCOUNTERS, POTIONS, RELICS
from run_preprocessor.reader import RawData
from run_preprocessor.snapshot import PlayerSnapshot
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            logger.error("Snapshot walk attempt exceeded total floors.")
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


class LoadRuns:
    def __init__(
        self,
        character: str,
        ascension: list[int],
        build_id: str,
        data_dir: str = "../data/runs/",
    ):
        self.character = character
        self.ascension = ascension
        self.build_id = build_id
        self.data_dir = data_dir
        self.runs_path = []

    def get_runs_path(self):
        import glob
        import os

        for a in self.ascension:
            data_dir = f"{self.data_dir}/{self.build_id}/{self.character}/a{a}/"
            abs_data_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), data_dir)
            )
            paths = glob.glob(f"{abs_data_dir}/**/*.run", recursive=True)
            if not paths:
                logger.warning(f"No run files found in {abs_data_dir}")
            self.runs_path.extend(paths)
        return self.runs_path

    def get_train_test_set(self, test_size: float = 0.2, random_state: int = 42):
        all_X_matrices = []
        all_y_arrays = []
        runs = self.get_runs_path()
        if not runs:
            logger.error("No run files to process.")
            return None, None, None, None

        for run in runs:
            logger.info(f"Processing run file: {run}")
            try:
                converter = RunToInputConverter.from_file(run)
                x, y = converter.vectorize()
                if x is not None and y is not None:
                    all_X_matrices.append(x)
                    all_y_arrays.append(y)
            except Exception as e:
                logger.error(f"Failed to process run file {run}: {e}")
                continue

        if not all_X_matrices:
            logger.error("No valid data extracted from run files.")
            return None, None, None, None

        # 2. Stack into your master dataset
        x_total = sp.vstack(all_X_matrices, format="csr")
        y_total = np.concatenate(all_y_arrays)

        logger.info(f"Total dataset shape: X={x_total.shape}, y={y_total.shape}")

        # shuffled already
        x_train, x_test, y_train, y_test = train_test_split(
            x_total, y_total, test_size=test_size, random_state=random_state
        )
        return x_train, x_test, y_train, y_test
