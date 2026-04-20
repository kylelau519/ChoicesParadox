import logging
import os
import unittest

from item_scrapper.items import ALL_CARDS
from run_preprocessor.save_reader import CurrentSaveReader
from run_preprocessor.snapshot import PlayerSnapshot
from stat_analysis.eval import Evaluator
from stat_analysis.testcase_generator import TestCaseGenerator

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestHealthEvaluation(unittest.TestCase):
    def test_health_impact_on_damage(self):
        save_path = "testfiles/current_run_test_health.save"
        if not os.path.exists(save_path):
            self.skipTest(f"Save file {save_path} not found")

        model_path = "models/hurdle_model_testfile.joblib"
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

        logger.debug(f"Evaluating encounters: {encounters}")

        for hp in health_values:
            if hp > snapshot.max_hp:
                continue
            generator.set_health(hp)
            logger.debug(f"\n--- Testing with HP: {hp}/{snapshot.max_hp} ---")

            cases, labels = generator.test_encounters(encounters)
            preds = evaluator.predict(cases)

            for i, label in enumerate(labels):
                if isinstance(preds, dict):
                    mean = preds["mean"][i]
                    low = preds["low"][i]
                    high = preds["high"][i]
                    logger.debug(
                        f"  {label:.<30} Predicted: {mean:.2f} (80% CL: [{low:.2f}, {high:.2f}])"
                    )
                else:
                    logger.debug(f"  {label:.<30} Predicted: {preds[i]:.2f}")

    def test_upgrade_impact_on_damage(self):
        save_path = "testfiles/current_run_test_health.save"
        if not os.path.exists(save_path):
            self.skipTest(f"Save file {save_path} not found")

        model_path = "models/hurdle_model_testfile.joblib"
        if not os.path.exists(model_path):
            self.skipTest(f"Model file {model_path} not found")

        evaluator = Evaluator.from_file(model_path)
        reader = CurrentSaveReader.from_file(save_path)
        snapshot = PlayerSnapshot(reader)
        snapshot.run()

        generator = TestCaseGenerator(snapshot)

        # Test encounter: next normal encounter
        current_act = reader.current_act()
        boss = current_act.boss()
        generator.set_encounter(boss)

        # Identify upgradeable cards in deck (not ending with +)
        upgradeable_cards = [
            c
            for c in snapshot.deck.cards.keys()
            if (not c.endswith("+") and c + "+" in ALL_CARDS)
        ]

        logger.info(f"\n--- Testing Upgrade Impact for Encounter: {boss} ---")

        results, labels = generator.test_upgrades(upgradeable_cards)
        preds = evaluator.predict(results)

        if isinstance(preds, dict):
            means = preds["mean"]
        else:
            means = preds

        original_damage = means[0]
        logger.info(f"Original: {original_damage:.2f}")

        better_count = 0
        worse_count = 0
        for i in range(1, len(labels)):
            damage = means[i]
            diff = damage - original_damage
            status = "BETTER" if diff < 0 else "WORSE" if diff > 0 else "SAME"
            logger.info(
                f"  {labels[i]:.<40} Predicted: {damage:.2f} ({diff:+.2f}) -> {status}"
            )
            if diff <= 0:
                better_count += 1
            else:
                worse_count += 1

        logger.info(f"Summary: {better_count} better/same, {worse_count} worse.")
        # We expect most upgrades to be better or same
        # self.assertEqual(worse_count, 0, f"{worse_count} upgrades predicted to increase damage!")

    def test_remove_impact_on_damage(self):
        save_path = "testfiles/current_run_test_health.save"
        if not os.path.exists(save_path):
            self.skipTest(f"Save file {save_path} not found")

        model_path = "models/hurdle_model_testfile.joblib"
        if not os.path.exists(model_path):
            self.skipTest(f"Model file {model_path} not found")

        evaluator = Evaluator.from_file(model_path)
        reader = CurrentSaveReader.from_file(save_path)
        snapshot = PlayerSnapshot(reader)
        snapshot.run()

        generator = TestCaseGenerator(snapshot)

        # Test encounter: next normal encounter
        current_act = reader.current_act()
        boss = current_act.boss()
        generator.set_encounter(boss)

        # Identify cards in deck to remove
        cards_to_remove = list(snapshot.deck.cards.keys())

        logger.info(f"\n--- Testing Removal Impact for Encounter: {boss} ---")

        results, labels = generator.test_removals(cards_to_remove)
        preds = evaluator.predict(results)

        if isinstance(preds, dict):
            means = preds["mean"]
        else:
            means = preds

        original_damage = means[0]
        logger.info(f"Original: {original_damage:.2f}")

        better_count = 0
        worse_count = 0
        for i in range(1, len(labels)):
            damage = means[i]
            diff = damage - original_damage
            status = "BETTER" if diff < 0 else "WORSE" if diff > 0 else "SAME"
            logger.info(
                f"  {labels[i]:.<40} Predicted: {damage:.2f} ({diff:+.2f}) -> {status}"
            )
            if diff <= 0:
                better_count += 1
            else:
                worse_count += 1

        logger.info(f"Summary: {better_count} better/same, {worse_count} worse.")


if __name__ == "__main__":
    unittest.main()
