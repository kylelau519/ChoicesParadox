import unittest

from run_preprocessor.run_reader import RawData
from run_preprocessor.save_reader import CurrentSaveReader
from run_preprocessor.snapshot import PlayerSnapshot


class TestReader(unittest.TestCase):
    def test_read_data_from_file(self):
        raw_data = RawData.from_file("testfiles/silent_a0_win.run")
        self.assertEqual(raw_data.run_metadata.ascension, 0)
        self.assertEqual(raw_data.run_metadata.game_mode, "standard")

    def test_read_save_data_from_file(self):
        save_reader = CurrentSaveReader.from_file("testfiles/current_run.save")
        self.assertEqual(save_reader.run_metadata.ascension, 0)
        self.assertEqual(
            save_reader.events_seen, ["EVENT.TEA_MASTER", "EVENT.TRASH_HEAP"]
        )

    def test_save_convert_to_snapshot(self):
        save_reader = CurrentSaveReader.from_file("testfiles/current_run.save")
        snapshot = PlayerSnapshot(save_reader)
        self.assertEqual(str(snapshot.character), "ironclad")

    def test_early_save(self):
        # no error = ok
        save_reader = CurrentSaveReader.from_file("testfiles/early_run.save")
        _ = PlayerSnapshot(save_reader)


if __name__ == "__main__":
    _ = unittest.main()
