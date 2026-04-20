import logging
import unittest

import joblib

from run_preprocessor.save_reader import CurrentSaveReader
from run_preprocessor.snapshot import PlayerSnapshot
from stat_analysis.eval import Evaluator
from stat_analysis.testcase_generator import TestCaseGenerator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

EXPERIMENT_PANEL = {
    "group_all_curses": True,
    "correlate_upgrades": True,
    "count_potions_as_binary": False,
    "ignore_starter_relic": False,
    "ignore_health": True,
    "total_upgrades": True,
    "total_deck_size": True,
    "starter_ratio": False,
}


class TestEval(unittest.TestCase):
    def test_card_choices_changes(self):
        save_path = "testfiles/current_run_test_health.save"
        model_path = "models/hurdle_model_silent.joblib"

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
