import logging
import unittest

import joblib

from run_preprocessor.save_reader import CurrentSaveReader
from run_preprocessor.snapshot import PlayerSnapshot
from stat_analysis.eval import Evaluator
from stat_analysis.state_vectorizer import TestCaseGenerator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

EXPERIMENT_PANEL = {
    "group_all_curses": False,  # Flattens Injury, Ascender's Bane, etc., into "TOTAL_CURSES"
    "correlate_upgrades": False,  # Treats "Strike+1" and "Strike" as the same feature
    "count_potions_as_binary": False,  # 0 if empty, 1 if holding any potion
    "ignore_starter_relic": False,  # Removes Burning Blood/Ring of Snake from features
}


class TestEval(unittest.TestCase):
    def test_showing_features(self):
        model = joblib.load("models/hurdle_model_ignore_health.joblib")
        eval = Evaluator(model)
        features = eval.important_features(
            top_n=15,
            character="*",
            show_relics=True,
            show_potions=False,
            show_colorless_cards=False,
            show_event_cards=False,
            show_encounters=False,
        )

    def test_card_choices_changes(self):
        save_path = "testfiles/current_run_test_health.save"
        model_path = "models/hurdle_model_ignore_health.joblib"

        eval = Evaluator.from_file(model_path)

        reader = CurrentSaveReader.from_file(save_path)
        snapshot = PlayerSnapshot(reader)
        snapshot.run()

        generator = TestCaseGenerator(snapshot)
        generator.set_max_health(28)
        generator.set_encounter("ENCOUNTER.SKULKING_COLONY_ELITE")
        x_original = generator.vectorize()
        pred_original = eval.predict(x_original)
        card_choices = ["CARD.POISONED_STAB"]
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

    # def test_remove_card_choices_changes(self):
    #     save_path = "testfiles/current_run_test_health.save"
    #     model_path = "models/hurdle_model_ignore_health.joblib"

    #     eval = Evaluator.from_file(model_path)
    #     reader = CurrentSaveReader.from_file(save_path)
    #     snapshot = PlayerSnapshot(reader)
    #     snapshot.run()
    #     generator = TestCaseGenerator(snapshot)
    #     generator.set_max_health(28)
    #     generator.set_encounter("ENCOUNTER.SKULKING_COLONY_ELITE")
    #     x_original = generator.vectorize()
    #     pred_original = eval.predict(x_original)

    #     card_choices = list(set(snapshot.deck.cards.keys()))
    #     test_cases, labels = generator.test_removals(card_choices)
    #     for case, label in zip(test_cases, labels):
    #         pred = eval.predict(case)
    #         if label == "Original":
    #             self.assertEqual(
    #                 pred, pred_original, "Original case should have the same prediction"
    #             )


if __name__ == "__main__":
    _ = unittest.main()
