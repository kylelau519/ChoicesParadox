import unittest

from stat_analysis.preprocess import RunToInputConverter


class TestPreprocess(unittest.TestCase):
    def test_load_data_from_file(self):
        converter = RunToInputConverter.from_file("testfiles/ironclad_a5_lose.run")
        converter.run()


if __name__ == "__main__":
    _ = unittest.main()
