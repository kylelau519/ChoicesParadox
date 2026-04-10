import unittest

from run_preprocessor.reader import RawData
from run_preprocessor.snapshot import PlayerSnapshot


class TestSnapshot(unittest.TestCase):
    def test_init_snapshot(self):
        raw_data = RawData.from_file("testfiles/silent_a0_win.run")
        snapshot = PlayerSnapshot(raw_data)

        self.assertEqual(snapshot.current_hp, 70)
        self.assertEqual(snapshot.current_gold, 99)
        self.assertEqual(snapshot.deck.get("CARD.STRIKE_SILENT"), 5)
        self.assertEqual(snapshot.deck.get("CARD.ZAP"), None)

    def test_simple_walk(self):
        raw_data = RawData.from_file("testfiles/silent_a0_win.run")
        snapshot = PlayerSnapshot(raw_data)

        snapshot.walk_to_floor(floor=5)
        self.assertEqual(snapshot.current_hp, 64)
        self.assertEqual(snapshot.deck.get("CARD.STRIKE_SILENT"), 5)
        self.assertEqual(snapshot.deck.get("CARD.FLECHETTES+"), 1)
        self.assertEqual(snapshot.deck.get("CARD.FLECHETTES"), None)

        snapshot.walk_to_floor(floor=7)
        self.assertEqual(snapshot.deck.get("CARD.STRIKE_SILENT"), 4)

        snapshot.walk_to_floor(floor=44)
        self.assertEqual(snapshot.deck.get("CARD.LEADING_STRIKE"), 1)
        self.assertEqual(snapshot.deck.get("CARD.STRIKE_SILENT+"), 1)

        snapshot.walk_to_floor(floor=48)
        self.assertEqual(snapshot.deck.get("CARD.THINKING_AHEAD+"), 1)
        self.assertEqual(snapshot.deck.get("CARD.PROLONG+"), 1)
        self.assertEqual(len(snapshot.relics), 18)


if __name__ == "__main__":
    _ = unittest.main()
