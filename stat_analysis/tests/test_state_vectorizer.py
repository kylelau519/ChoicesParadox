import unittest

from stat_analysis.preprocess import GLOBAL_VECTORIZER
from stat_analysis.state_vectorizer import TestCaseGenerator


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
        self.deck = MockDeck()
        self.potions = {"POTION.ASHWATER": 1, "POTION.ATTACK_POTION": 1}
        self.relics = {}


class TestStateVectorizer(unittest.TestCase):
    def test_test_potions(self):
        snapshot = MockSnapshot()
        # Cast MockSnapshot to MasterSchema-like object for the constructor
        generator = TestCaseGenerator(snapshot)  # type: ignore
        generator.set_encounter("ENCOUNTER.AXEBOTS_NORMAL")

        results, labels = generator.test_potions()
        non_zero_idx = results.nonzero()[1]

        features_name = GLOBAL_VECTORIZER.get_feature_names_out()

        # for result, label in zip(results, labels):
        #     non_zero_idx = result.nonzero()[1]
        #     print(f"Combination: {label}, Features: {features_name[non_zero_idx]}")
        #
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


if __name__ == "__main__":
    unittest.main()
