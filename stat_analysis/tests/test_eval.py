import unittest

import joblib
from stat_analysis.eval import Evaluator


class TestEval(unittest.TestCase):
    def test_showing_features(self):
        eval = Evaluator("testfiles/xgb_model.joblib")
        features = eval.important_features(
            top_n=15,
            character="necrobinder",
            show_relics=False,
            show_potions=False,
            show_colorless_cards=False,
            show_event_cards=False,
            show_encounters=False,
        )
        print("Top 50 Important Features:")
        for feature, importance in features:
            print(f"{feature}: {importance:.4f}")


if __name__ == "__main__":
    _ = unittest.main()
