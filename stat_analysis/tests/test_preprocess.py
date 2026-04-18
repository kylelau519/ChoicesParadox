import unittest
from typing import Optional, cast

import numpy as np
import sklearn
from sklearn.feature_extraction import DictVectorizer

from stat_analysis.preprocess import RunToInputConverter, build_master_schema


class TestPreprocess(unittest.TestCase):
    def test_load_data_from_file(self):
        converter = RunToInputConverter.from_file("testfiles/regent_a0_win.run")
        x_matrix, y_matrix = converter.vectorize()

    def test_schema_conversion(self):
        converter = RunToInputConverter.from_file("testfiles/ironclad_a5_lose.run")
        x_raw, y_raw = converter.vectorize()

        damage_taken_arr = np.array([3, 12, 3, 56, 37, 7])

        self.assertIsNotNone(x_raw)
        self.assertIsNotNone(y_raw)

        # Use cast to inform type checkers that x and y are no longer Optional after the assertIsNotNone checks
        x = cast(np.ndarray, x_raw)
        y = cast(np.ndarray, y_raw)

        self.assertEqual(x.shape[0], y.shape[0])
        for i in range(y.shape[0]):
            self.assertEqual(y[i], damage_taken_arr[i])

    def test_merge_curse_schema(self):
        EXPERIMENT_PANEL = {
            "group_all_curses": True,  # Flattens Injury, Ascender's Bane, etc., into "TOTAL_CURSES"
            "merge_upgrades": False,  # Treats "Strike+1" and "Strike" as the same feature
            "count_potions_as_binary": False,  # 0 if empty, 1 if holding any potion
            "ignore_starter_relic": False,  # Removes Burning Blood/Ring of Snake from features
        }
        schema = build_master_schema(EXPERIMENT_PANEL)
        vectorizer = DictVectorizer(sparse=True).fit([schema])
        self.assertEqual("TOTAL_CURSES" in vectorizer.get_feature_names_out(), True)
        self.assertEqual("CARD.INJURY" in vectorizer.get_feature_names_out(), False)

    def test_not_murge_curse_schema(self):
        EXPERIMENT_PANEL = {
            "group_all_curses": False,  # Flattens Injury, Ascender's Bane, etc., into "TOTAL_CURSES"
            "merge_upgrades": False,  # Treats "Strike+1" and "Strike" as the same feature
            "count_potions_as_binary": False,  # 0 if empty, 1 if holding any potion
            "ignore_starter_relic": False,  # Removes Burning Blood/Ring of Snake from features
        }
        schema = build_master_schema(EXPERIMENT_PANEL)
        vectorizer = DictVectorizer(sparse=True).fit([schema])
        self.assertEqual("CARD.INJURY" in vectorizer.get_feature_names_out(), True)
        self.assertEqual("TOTAL_CURSES" in vectorizer.get_feature_names_out(), False)


if __name__ == "__main__":
    _ = unittest.main()
