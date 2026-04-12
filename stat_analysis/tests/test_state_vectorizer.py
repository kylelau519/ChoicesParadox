import unittest

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

        results = generator.test_potions()

        # There should be 4 results for 2 potions (None, A, B, A+B)
        self.assertEqual(len(results), 4)

        labels = [r[0] for r in results]
        self.assertIn("None", labels)
        self.assertIn("POTION.ASHWATER", labels)
        self.assertIn("POTION.ATTACK_POTION", labels)
        self.assertIn("POTION.ASHWATER + POTION.ATTACK_POTION", labels)

        # Verify that each result is a tuple of (label, scipy.sparse.csr_matrix)
        for label, vector in results:
            self.assertIsInstance(label, str)
            # vectorizer.transform returns a sparse matrix
            self.assertTrue(hasattr(vector, "shape"))
            self.assertEqual(vector.shape[0], 1)

        # Check if original state is restored
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

        results = generator.test_potions()

        # 2^3 = 8 combinations
        self.assertEqual(len(results), 8)


if __name__ == "__main__":
    unittest.main()
