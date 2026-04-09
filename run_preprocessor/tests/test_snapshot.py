import unittest

from run_preprocessor.reader import RawData
from run_preprocessor.snapshot import PlayerSnapshot


class TestSnapshot(unittest.TestCase):
    def test_simple_snapshot(self):
        raw_data = RawData.from_file("testfiles/silent_a0_win.run")
        _ = PlayerSnapshot.at_floor(data=raw_data, floor=5, player_id=1)

if __name__ == "__main__":
    _ = unittest.main()
