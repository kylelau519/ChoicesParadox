# Evaluator class for evaluating the performance of a trained model and answering questions about feature importance and predictions.
import logging
from typing import Any, Protocol

import joblib
import numpy as np

from item_scrapper.items import *
from run_preprocessor.save_reader import CurrentSaveReader
from run_preprocessor.snapshot import PlayerSnapshot
from stat_analysis.preprocess import GLOBAL_VECTORIZER
from stat_analysis.state_vectorizer import TestCaseGenerator

logger = logging.getLogger(__name__)


class Predictor(Protocol):
    def predict(self, X: Any) -> np.ndarray: ...


class Evaluator:
    def __init__(self, model: Predictor):
        self.model = model
        self.vectorizer = GLOBAL_VECTORIZER

    @classmethod
    def from_file(cls, model_path: str):
        # Ensure HurdleModel is known to joblib
        # Some models were saved when train_hurdle.py was __main__
        import sys

        import stat_analysis.train_hurdle

        sys.modules["__main__"].HurdleModel = stat_analysis.train_hurdle.HurdleModel

        model = joblib.load(model_path)
        return cls(model)

    def predict(self, x):
        y_pred = self.model.predict(x)
        # Handle HurdleModel returning a dict of predictions
        if isinstance(y_pred, dict):
            return {
                k: v.flatten() if hasattr(v, "flatten") else v
                for k, v in y_pred.items()
            }
        # Handle cases where model might return something else than 1D array
        if hasattr(y_pred, "flatten"):
            y_pred = y_pred.flatten()
        return y_pred

    # Model evaluation methods
    def important_features(
        self,
        top_n=10,
        character=None,
        show_relics=True,
        show_potions=True,
        show_colorless_cards=True,
        show_event_cards=True,
        show_encounters=True,
        model_component=None,  # 'clf', 'reg_mean', 'reg_low', or 'reg_high' for HurdleModel
    ):
        model = self.model
        if model_component and hasattr(self.model, model_component):
            model = getattr(self.model, model_component)

        if not hasattr(model, "feature_importances_"):
            logger.warning(f"Model {type(model)} does not support feature importance.")
            return []

        importances = model.feature_importances_
        feature_names = self.vectorizer.get_feature_names_out()

        # Map character names to their card dictionaries
        char_card_maps = {
            "ironclad": IRONCLAD_CARDS,
            "silent": SILENT_CARDS,
            "defect": DEFECT_CARDS,
            "regent": REGENT_CARDS,
            "necrobinder": NECROBINDER_CARDS,
        }

        results = []
        for name, imp in zip(feature_names, importances):
            # 1. Filter Relics and Potions
            if name.startswith("RELIC.") and not show_relics:
                continue
            if name.startswith("POTION.") and not show_potions:
                continue
            if name.startswith("ENCOUNTER") and not show_encounters:
                continue

            # 2. Filter Cards
            if name.startswith("CARD."):
                # Remove upgrade suffix for lookup
                base_name = name.rstrip("+")

                # Colorless filter
                if base_name in COLORLESS_CARDS and not show_colorless_cards:
                    continue

                # Event card filter
                if base_name in EVENT_CARDS and not show_event_cards:
                    continue

                # Character specific filter
                if character:
                    character = character.lower()
                    # Check if this card belongs to a different character
                    is_other_character_card = False
                    for char_name, card_dict in char_card_maps.items():
                        if char_name != character and base_name in card_dict:
                            is_other_character_card = True
                            break

                    if is_other_character_card:
                        continue

            results.append((name, imp))

        # Sort by importance and return top N
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]

    # Live evaluation methods
    def predict_damage_taken(self, current_save: CurrentSaveReader):
        current_act = current_save.current_act()
        snapshot = PlayerSnapshot(current_save)
        snapshot.run()
        generator = TestCaseGenerator(snapshot)
        next_normal = current_act.next_normal_encounter()
        next_elite = current_act.next_elite()
        next_enc, enc_labels = generator.test_encounters([next_normal, next_elite])

        remaining_enc, remaining_labels = generator.test_encounters(
            current_act.remaining_normal_encounters()
        )

        # Predict damage for next encounters
        next_preds = self.predict(next_enc)
        logger.info("Predicted damage for next encounters:")
        for i, label in enumerate(enc_labels):
            if isinstance(next_preds, dict):
                logger.info(
                    f"  {label.lower()}: {next_preds['mean'][i]:.2f}, 80%CL [{next_preds['low'][i]:.2f}, {next_preds['high'][i]:.2f}]"
                )
            else:
                logger.info(f"  {label.lower()}: {next_preds[i]:.2f}")
        logger.info("")

        # Predict damage for remaining encounters
        logger.info("Predicted damage for remaining normal encounters:")
        remaining_preds = self.predict(remaining_enc)
        for i, label in enumerate(remaining_labels):
            if isinstance(remaining_preds, dict):
                logger.info(
                    f"  {label.lower()}: {remaining_preds['mean'][i]:.2f}, 80%CL [{remaining_preds['low'][i]:.2f}, {remaining_preds['high'][i]:.2f}]"
                )
            else:
                logger.info(f"  {label.lower()}: {remaining_preds[i]:.2f}")
        logger.info("")

        # Predict damage for boss encounter if applicable
        boss = current_act.boss()
        if boss:
            boss_enc, boss_labels = generator.test_encounters([boss])
            boss_pred = self.predict(boss_enc)
            logger.info(f"Predicted damage for boss encounter:")
            if isinstance(boss_pred, dict):
                logger.info(
                    f"  {boss.removeprefix('ENCOUNTER.').lower()}: {boss_pred['mean'][0]:.2f}, 80%CL [{boss_pred['low'][0]:.2f}, {boss_pred['high'][0]:.2f}]"
                )
            else:
                logger.info(
                    f"  {boss.removeprefix('ENCOUNTER.').lower()}: {boss_pred[0]:.2f}"
                )
        second_boss = current_act.second_boss()
        if second_boss:
            second_boss_enc, second_boss_labels = generator.test_encounters(
                [second_boss]
            )
            second_boss_pred = self.predict(second_boss_enc)
            logger.info(f"Predicted damage for second boss encounter:")
            if isinstance(second_boss_pred, dict):
                logger.info(
                    f"  {second_boss.removeprefix('ENCOUNTER.').lower()}: {second_boss_pred['mean'][0]:.2f}, 80%CL [{second_boss_pred['low'][0]:.2f}, {second_boss_pred['high'][0]:.2f}]"
                )
            else:
                logger.info(
                    f"  {second_boss.removeprefix('ENCOUNTER.').lower()}: {second_boss_pred[0]:.2f}"
                )
        logger.info("")

    def evaluate_game_options(self, reader: CurrentSaveReader, test_func, items):
        """
        Generic method to evaluate a set of options (cards, relics, etc.) against all remaining combats in the act.
        """
        current_act = reader.current_act()
        snapshot = PlayerSnapshot(reader)
        snapshot.run()
        generator = TestCaseGenerator(snapshot)

        remaining_combats = set(
            current_act.remaining_normal_encounters()
            + current_act.remaining_elite_encounters()
        )
        if current_act.boss():
            remaining_combats.add(current_act.boss())
        if current_act.second_boss():
            remaining_combats.add(current_act.second_boss())

        unique_combats = sorted([c for c in remaining_combats if c])

        # label -> {mean: sum, low: sum, high: sum} OR label -> total_damage
        results = {}

        if not unique_combats:
            return {}

        generator.set_encounter(unique_combats[0])
        _, labels = test_func(generator, items)

        # Initial probe to see if model returns dict
        dummy_x = GLOBAL_VECTORIZER.transform([{}])
        dummy_pred = self.predict(dummy_x)
        is_dict = isinstance(dummy_pred, dict)

        for label in labels:
            if is_dict:
                results[label] = {"mean": 0.0, "low": 0.0, "high": 0.0}
            else:
                results[label] = 0.0

        for combat in unique_combats:
            generator.set_encounter(combat)
            cases, labels = test_func(generator, items)
            preds = self.predict(cases)
            for idx, label in enumerate(labels):
                if is_dict:
                    results[label]["mean"] += preds["mean"][idx]
                    results[label]["low"] += preds["low"][idx]
                    results[label]["high"] += preds["high"][idx]
                else:
                    results[label] += preds[idx]

        return results
