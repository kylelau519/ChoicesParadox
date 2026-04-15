import unittest

import joblib

from run_preprocessor.save_reader import CurrentSaveReader
from run_preprocessor.snapshot import PlayerSnapshot
from stat_analysis.eval import Evaluator
from stat_analysis.preprocess import GLOBAL_VECTORIZER, build_master_schema
from stat_analysis.state_vectorizer import TestCaseGenerator

EXPERIMENT_PANEL = {
    "group_all_curses": False,  # Flattens Injury, Ascender's Bane, etc., into "TOTAL_CURSES"
    "merge_upgrades": False,  # Treats "Strike+1" and "Strike" as the same feature
    "count_potions_as_binary": False,  # 0 if empty, 1 if holding any potion
    "ignore_starter_relic": False,  # Removes Burning Blood/Ring of Snake from features
}


class TestEval(unittest.TestCase):
    def test_showing_features(self):
        model = joblib.load("testfiles/xgb_model_dont_touch.joblib")
        eval = Evaluator(model)
        features = eval.important_features(
            top_n=15,
            character="necrobinder",
            show_relics=False,
            show_potions=False,
            show_colorless_cards=False,
            show_event_cards=False,
            show_encounters=False,
        )

    def test_card_choices_changes(self):
        model = joblib.load("testfiles/xgb_model_dont_touch.joblib")
        eval = Evaluator(model)
        run = CurrentSaveReader.from_file("testfiles/current_run.save")
        snapshot = PlayerSnapshot(run)
        generator = TestCaseGenerator(snapshot)
        generator.set_max_health(28)
        print(snapshot.deck.cards)
        generator.set_encounter("ENCOUNTER.SKULKING_COLONY_ELITE")
        x_original = generator.vectorize()
        pred_original = eval.predict(x_original)
        # print(
        #     f"Original prediction against skulking colony elite: {pred_original[0]:.2f}"
        # )

        card_choices = ["CARD.TWIN_STRIKE", "CARD.FLAME_BARRIER"]
        test_cases, labels = generator.test_adding_cards(card_choices)
        for case, label in zip(test_cases, labels):
            pred = eval.predict(case)
            if label == "Original":
                self.assertEqual(
                    pred, pred_original, "Original case should have the same prediction"
                )
            else:
                self.assertNotEqual(
                    pred,
                    pred_original,
                    f"Prediction should change after taking {label}",
                )
        # for case, label in zip(test_cases, labels):
        #     print(f"Test case for taking {label}: Non-zero features:")
        #     non_zero_idx = case.nonzero()[1]
        #     features_name = eval.vectorizer.get_feature_names_out()
        #     for idx in non_zero_idx:
        #         print(f"  {features_name[idx]}")

        #     print(f"prediction: {eval.predict(case)[0]}")

        #     print("\n")
        #     print(case)

        # predictions = eval.predict(test_cases)
        # for pred, label in zip(predictions, labels):
        #     print(
        #         f"Predicted damage taken against skulking colony elite after taking {label}:\n {pred:.2f}"
        #     )


if __name__ == "__main__":
    _ = unittest.main()
