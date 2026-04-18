import logging
import os
import unittest

from run_preprocessor.save_reader import CurrentSaveReader
from run_preprocessor.snapshot import PlayerSnapshot
from stat_analysis.eval import Evaluator
from stat_analysis.state_vectorizer import TestCaseGenerator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestHealthEvaluation(unittest.TestCase):
    def test_health_impact_on_damage(self):
        save_path = "testfiles/current_run_test_health.save"
        if not os.path.exists(save_path):
            self.skipTest(f"Save file {save_path} not found")

        model_path = "models/hurdle_model_ignore_health.joblib"
        if not os.path.exists(model_path):
            self.skipTest(f"Model file {model_path} not found")

        logger.info(f"Using model: {model_path}")
        evaluator = Evaluator.from_file(model_path)

        reader = CurrentSaveReader.from_file(save_path)
        snapshot = PlayerSnapshot(reader)
        snapshot.run()

        generator = TestCaseGenerator(snapshot)

        # Test encounters: next normal and next elite
        current_act = reader.current_act()
        next_normal = current_act.next_normal_encounter()
        next_elite = current_act.next_elite()

        encounters = [next_normal, next_elite]
        health_values = [10, 30, 50, 70, 90]

        logger.info(f"Evaluating encounters: {encounters}")

        for hp in health_values:
            if hp > snapshot.max_hp:
                continue
            generator.set_health(hp)
            logger.info(f"\n--- Testing with HP: {hp}/{snapshot.max_hp} ---")

            cases, labels = generator.test_encounters(encounters)
            preds = evaluator.predict(cases)

            for i, label in enumerate(labels):
                if isinstance(preds, dict):
                    mean = preds["mean"][i]
                    low = preds["low"][i]
                    high = preds["high"][i]
                    logger.info(
                        f"  {label:.<30} Predicted: {mean:.2f} (80% CL: [{low:.2f}, {high:.2f}])"
                    )
                else:
                    logger.info(f"  {label:.<30} Predicted: {preds[i]:.2f}")


if __name__ == "__main__":
    unittest.main()
