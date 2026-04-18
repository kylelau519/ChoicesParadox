import logging
import unittest

from run_preprocessor.run_reader import RawData
from stat_analysis.preprocess import LoadRuns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestLoader(unittest.TestCase):
    def test_load_runs(self):
        suffix = "v2"
        loader = LoadRuns("*", [3, 4, 5, 6, 7, 8, 9, 10], "v0.102.0", suffix=suffix)
        loader.show_damage_taken_hist()

    def test_count_0_damage(self):
        loader = LoadRuns("*", [3, 4, 5, 6, 7, 8, 9, 10], "v0.102.0")
        count = 0
        runs = loader.get_runs_path()
        for run in runs:
            raw = RawData.from_file(run)
            map_point_history = raw.map_point_history.flatten()
            for map_point in map_point_history:
                for room in map_point.rooms:
                    if room.get("model_id") and room.get("model_id").startswith(
                        "ENCOUNTER"
                    ):
                        ps = map_point.player_stats[0]
                        damage_taken = ps["damage_taken"]
                        if damage_taken == 1:
                            count += 1
        logger.info(f"Total encounters with 1 damage taken: {count}")


if __name__ == "__main__":
    _ = unittest.main()
