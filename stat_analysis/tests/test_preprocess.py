import unittest
from typing import Optional, cast

import numpy as np
from stat_analysis.preprocess import RunToInputConverter


class TestPreprocess(unittest.TestCase):
    def test_load_data_from_file(self):
        converter = RunToInputConverter.from_file("testfiles/ironclad_a5_lose.run")
        inputs, targets = converter.run()

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


if __name__ == "__main__":
    _ = unittest.main()
