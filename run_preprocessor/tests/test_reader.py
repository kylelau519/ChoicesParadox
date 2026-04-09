import unittest

from run_preprocessor.reader import RawData


class TestReader(unittest.TestCase):
    def test_read_data_from_file(self):
        raw_data = RawData.from_file("testfiles/silent_a0_win.run")
        self.assertEqual(raw_data.run_metadata.ascension, 0)
        self.assertEqual(raw_data.run_metadata.game_mode, "standard")

if __name__ == "__main__":
    _ = unittest.main()
