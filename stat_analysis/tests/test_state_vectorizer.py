import unittest

import numpy as np
import sklearn
from sklearn.feature_extraction import DictVectorizer

from run_preprocessor.deck import Deck
from stat_analysis.preprocess import GLOBAL_VECTORIZER, build_master_schema
from stat_analysis.state_vectorizer import TestCaseGenerator

EXPERIMENT_PANEL = {
    "group_all_curses": False,  # Flattens Injury, Ascender's Bane, etc., into "TOTAL_CURSES"
    "correlate_upgrades": False,  # Treats "Strike+1" and "Strike" as the same feature
    "count_potions_as_binary": False,  # 0 if empty, 1 if holding any potion
    "ignore_starter_relic": False,  # Removes Burning Blood/Ring of Snake from features
}


class MockDeck:
    def __init__(self, cards=None):
        self.cards = cards or {}

    def remove(self, card_id):
        pass

    def add(self, card_id):
        pass


class MockSnapshot:
    def __init__(self):
        self.current_hp = 50
        self.max_hp = 100
        self.deck = Deck([])
        self.potions = {"POTION.ASHWATER": 1, "POTION.ATTACK_POTION": 1}
        self.relics = {}


class TestStateVectorizer(unittest.TestCase):
    def test_test_potions(self):
        snapshot = MockSnapshot()
        # Cast MockSnapshot to MasterSchema-like object for the constructor
        generator = TestCaseGenerator(snapshot)  # type: ignore
        generator.set_encounter("ENCOUNTER.AXEBOTS_NORMAL")

        results, labels = generator.test_potions()
        vectorizer = DictVectorizer(sparse=True).fit(
            [build_master_schema(EXPERIMENT_PANEL)]
        )
        features_name = vectorizer.get_feature_names_out()
        for name in features_name[results[3].nonzero()[1]]:
            self.assertNotEqual(name.startswith("POTION."), True)

        self.assertEqual(
            generator.potions, {"POTION.ASHWATER": 1, "POTION.ATTACK_POTION": 1}
        )

    def test_test_potions_three(self):
        snapshot = MockSnapshot()
        snapshot.potions = {"A": 1, "B": 1, "C": 1}
        # We need to use valid potion IDs if the vectorizer checks them,
        # but TestCaseGenerator only checks them in add_potion.
        # vectorize uses whatever is in self.potions.
        generator = TestCaseGenerator(snapshot)  # type: ignore
        generator.set_encounter("ENCOUNTER.AXEBOTS_NORMAL")

        results, _ = generator.test_potions()
        # 2^3 = 8 combinations
        self.assertEqual(results.shape[0], 8)

    def test_test_adding_wrong_card(self):
        snapshot = MockSnapshot()
        generator = TestCaseGenerator(snapshot)  # type: ignore
        generator.set_encounter("ENCOUNTER.AXEBOTS_NORMAL")
        with self.assertRaises(ValueError):
            generator.add_card("CARD.NonExistent")

    def test_test_adding_cards(self):
        snapshot = MockSnapshot()
        generator = TestCaseGenerator(snapshot)  # type: ignore
        generator.set_encounter("ENCOUNTER.AXEBOTS_NORMAL")
        generator.add_card("CARD.Strike_Regent")

        pool = ["CARD.Strike_Silent", "Defend_silent", "CARD.Bash"]

        # Test with pick=2
        # Should have 1 (Original) + 3 (single) + 3 (pairs) = 7 cases
        results, labels = generator.test_adding_cards(pool, 2)

        self.assertEqual(len(labels), 7)
        self.assertIn("Original", labels)
        self.assertIn("STRIKE_SILENT", labels)
        self.assertIn("STRIKE_SILENT + DEFEND_SILENT", labels)

        # Verify each result has different non-zero features or counts
        original_idx = results[0].nonzero()[1]
        strike_silent_idx = labels.index("STRIKE_SILENT")
        strike_silent_vector = results[strike_silent_idx]

        # STRIKE_SILENT should have a different vector than Original
        self.assertFalse(
            np.array_equal(results[0].toarray(), strike_silent_vector.toarray())
        )

        non_zero_idx = results[4].nonzero()[1]
        features_name = GLOBAL_VECTORIZER.get_feature_names_out()
        self.assertEqual(features_name[non_zero_idx[0]], "CARD.DEFEND_SILENT")
        self.assertEqual(features_name[non_zero_idx[1]], "CARD.STRIKE_REGENT")
        self.assertEqual(features_name[non_zero_idx[2]], "CARD.STRIKE_SILENT")

        # Verify restoration of original deck (which had Strike_Regent)
        self.assertEqual(generator.deck.cards, {"CARD.STRIKE_REGENT": 1})


if __name__ == "__main__":
    unittest.main()
