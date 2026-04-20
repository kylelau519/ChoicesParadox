# Evaluator class for evaluating the performance of a trained model and answering questions about feature importance and predictions.
import logging
import sys
from typing import Any, Protocol

import joblib
import numpy as np

import stat_analysis.train
from item_scrapper.items import *
from run_preprocessor.save_reader import CurrentSaveReader
from run_preprocessor.snapshot import PlayerSnapshot
from stat_analysis.preprocess import GLOBAL_VECTORIZER
from stat_analysis.testcase_generator import TestCaseGenerator

sys.modules["__main__"].HurdleModel = stat_analysis.train.HurdleModel
logger = logging.getLogger(__name__)


class Predictor(Protocol):
    def predict(self, X: Any) -> np.ndarray: ...


class Evaluator:
    def __init__(self, model: Predictor):
        self.model = model
        self.vectorizer = GLOBAL_VECTORIZER

    @classmethod
    def from_file(cls, model_path: str):
        model = joblib.load(model_path)
        return cls(model)

    def predict(self, x):
        y_pred = self.model.predict(x)
        if isinstance(y_pred, dict):
            return {
                k: v.flatten() if hasattr(v, "flatten") else v
                for k, v in y_pred.items()
            }
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
        remaining_elite_enc, remaining_elite_labels = generator.test_encounters(
            list(set(current_act.remaining_elite_encounters()))
        )

        # Predict damage for next encounters
        next_preds = self.predict(next_enc)
        logger.info("Predicted damage for next encounters:")
        self.print_predicted(next_preds, enc_labels)
        logger.info("")

        # Predict damage for remaining elite encounters
        logger.info("Predicted damage for remaining elite encounters:")
        elite_preds = self.predict(remaining_elite_enc)
        self.print_predicted(elite_preds, remaining_elite_labels)
        logger.info("")

        # Predict damage for remaining encounters
        logger.info("Predicted damage for remaining normal encounters:")
        remaining_preds = self.predict(remaining_enc)
        self.print_predicted(remaining_preds, remaining_labels)
        logger.info("")

        # Predict damage for boss encounter if applicable
        boss = current_act.boss()
        if boss:
            boss_enc, boss_labels = generator.test_encounters([boss])
            boss_pred = self.predict(boss_enc)
            logger.info("Predicted damage for boss encounter:")
            self.print_predicted(boss_pred, boss_labels)
        second_boss = current_act.second_boss()
        if second_boss:
            second_boss_enc, second_boss_labels = generator.test_encounters(
                [second_boss]
            )
            second_boss_pred = self.predict(second_boss_enc)
            logger.info("Predicted damage for second boss encounter:")
            self.print_predicted(second_boss_pred, second_boss_labels)
        logger.info("")

    def print_predicted(self, preds, labels):
        for i, label in enumerate(labels):
            label = label.replace("_", " ").title()
            if isinstance(preds, dict):
                logger.info(
                    f"  {label:.<30} Predicted: {preds['mean'][i]:>6.2f}, 80% CL: [{preds['low'][i]:.2f}, {preds['high'][i]:.2f}]"
                )
            else:
                logger.info(f"  {label:.<30} Predicted: {preds[i]:.2f}")

    def evaluate_game_options(self, reader: CurrentSaveReader, test_func, items):
        """
        Generic method to evaluate a set of options (cards, relics, etc.) against all remaining combats in the act.
        """
        current_act = reader.current_act()
        snapshot = PlayerSnapshot(reader)
        snapshot.run()
        generator = TestCaseGenerator(snapshot)

        # Categorize unique encounters
        unique_normals = sorted(
            list(set(c for c in current_act.remaining_normal_encounters() if c))
        )
        unique_elites = sorted(
            list(set(c for c in current_act.remaining_elite_encounters() if c))
        )
        unique_bosses = sorted(
            list(set(c for c in [current_act.boss(), current_act.second_boss()] if c))
        )

        all_unique = sorted(list(set(unique_normals + unique_elites + unique_bosses)))
        if not all_unique:
            return {}

        # Initial probe to see if model returns dict and get labels
        generator.set_encounter(all_unique[0])
        _, labels = test_func(generator, items)
        dummy_x = GLOBAL_VECTORIZER.transform([{}])
        dummy_pred = self.predict(dummy_x)
        is_dict = isinstance(dummy_pred, dict)

        # Calculate average damage for each category
        category_results = {
            "normal": {},  # label -> damage
            "elite": {},
            "boss": {},
        }

        def process_category(encounters, cat_name):
            if not encounters:
                return
            for combat in encounters:
                generator.set_encounter(combat)
                cases, labels = test_func(generator, items)
                preds = self.predict(cases)
                for idx, label in enumerate(labels):
                    if label not in category_results[cat_name]:
                        if is_dict:
                            category_results[cat_name][label] = {
                                "mean": 0.0,
                                "low": 0.0,
                                "high": 0.0,
                            }
                        else:
                            category_results[cat_name][label] = 0.0

                    if is_dict:
                        category_results[cat_name][label]["mean"] += preds["mean"][
                            idx
                        ] / len(encounters)
                        category_results[cat_name][label]["low"] += preds["low"][
                            idx
                        ] / len(encounters)
                        category_results[cat_name][label]["high"] += preds["high"][
                            idx
                        ] / len(encounters)
                    else:
                        category_results[cat_name][label] += preds[idx] / len(
                            encounters
                        )

        process_category(unique_normals, "normal")
        process_category(unique_elites, "elite")
        process_category(unique_bosses, "boss")

        # Combine using weights: 35% Boss, 35% Elite, 30% Normal
        weights = {"boss": 0.35, "elite": 0.35, "normal": 0.30}

        # Re-normalize weights if some categories are missing
        active_weight_sum = sum(
            weights[cat] for cat in weights if category_results[cat]
        )
        if active_weight_sum == 0:
            return {}

        final_results = {}
        for label in labels:
            if is_dict:
                final_results[label] = {"mean": 0.0, "low": 0.0, "high": 0.0}
            else:
                final_results[label] = 0.0

            for cat, weight in weights.items():
                if category_results[cat]:
                    norm_weight = weight / active_weight_sum
                    if is_dict:
                        final_results[label]["mean"] += (
                            category_results[cat][label]["mean"] * norm_weight
                        )
                        final_results[label]["low"] += (
                            category_results[cat][label]["low"] * norm_weight
                        )
                        final_results[label]["high"] += (
                            category_results[cat][label]["high"] * norm_weight
                        )
                    else:
                        final_results[label] += (
                            category_results[cat][label] * norm_weight
                        )

        return final_results
