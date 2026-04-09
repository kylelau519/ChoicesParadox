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

    def test_simple_snapshot(self):
        raw_data = RawData.from_file("testfiles/silent_a0_win.run")
        snapshot = PlayerSnapshot(raw_data)
        snapshot.walk_to_floor(floor=5)
        self.assertEqual(snapshot.current_hp, 64)

if __name__ == "__main__":
    _ = unittest.main()
