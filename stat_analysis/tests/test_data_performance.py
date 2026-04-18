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


if __name__ == "__main__":
    _ = unittest.main()
