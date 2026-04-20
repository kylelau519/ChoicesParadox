import unittest
from typing import Optional, cast

import numpy as np
import sklearn
from sklearn.feature_extraction import DictVectorizer

from stat_analysis.preprocess import RunToInputConverter, build_master_schema

EXPERIMENT_PANEL = {
    "group_all_curses": True,
    "correlate_upgrades": True,
    "count_potions_as_binary": False,
    "ignore_starter_relic": False,
    "ignore_health": True,
    "total_upgrades": True,
    "total_deck_size": True,
    "starter_ratio": False,
}


class TestPreprocess(unittest.TestCase):
    def test_load_data_from_file(self):
        converter = RunToInputConverter.from_file("testfiles/silent_a0_win.run")
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
        schema = build_master_schema(EXPERIMENT_PANEL)
        vectorizer = DictVectorizer(sparse=True).fit([schema])
        self.assertEqual("TOTAL_CURSES" in vectorizer.get_feature_names_out(), True)
        self.assertEqual("CARD.INJURY" in vectorizer.get_feature_names_out(), False)

    def test_not_murge_curse_schema(self):
        custom_panel = EXPERIMENT_PANEL.copy()
        custom_panel["group_all_curses"] = False
        schema = build_master_schema(custom_panel)
        vectorizer = DictVectorizer(sparse=True).fit([schema])
        self.assertEqual("CARD.INJURY" in vectorizer.get_feature_names_out(), True)
        self.assertEqual("TOTAL_CURSES" in vectorizer.get_feature_names_out(), False)

    def test_correlate_upgrades_schema(self):
        schema = build_master_schema(EXPERIMENT_PANEL)
        vectorizer = DictVectorizer(sparse=True).fit([schema])
        self.assertEqual("TOTAL_UPGRADES" in vectorizer.get_feature_names_out(), True)

    def test_correlate_upgrades_action(self):
        converter = RunToInputConverter.from_file("testfiles/silent_a0_win.run")
        # Manually inject cards into the first snapshot to test
        converter.snapshot_now.deck.cards = {
            "CARD.STRIKE_SILENT": 3,
            "CARD.STRIKE_SILENT+": 1,
        }

        # Walk until we find an encounter
        num_floors = len(converter.raw_data.map_point_history.flatten())
        while converter.snapshot_now.current_lumpsum_floor < num_floors:
            if converter.snapshot_next.is_encounter():
                input_dict, target = converter.convert_snapshot()
                if input_dict:
                    self.assertEqual(input_dict["CARD.STRIKE_SILENT"], 4)
                    self.assertEqual(input_dict["CARD.STRIKE_SILENT+"], 1)
                    self.assertEqual(input_dict["TOTAL_UPGRADES"], 1)
                    return
            converter.walk()
        self.fail("No encounter found to test conversion")


if __name__ == "__main__":
    _ = unittest.main()
