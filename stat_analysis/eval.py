# Evaluator class for evaluating the performance of a trained model and answering questions about feature importance and predictions.
import logging

import joblib
import numpy as np
from item_scrapper.items import *
from run_preprocessor.save_reader import CurrentSaveReader
from run_preprocessor.snapshot import PlayerSnapshot
from stat_analysis.preprocess import GLOBAL_VECTORIZER
from stat_analysis.state_vectorizer import TestCaseGenerator

logger = logging.getLogger(__name__)


class Evaluator:
    def __init__(self, model_path: str, current_save_path: str = ""):
        self.model = joblib.load(model_path)
        self.vectorizer = GLOBAL_VECTORIZER

    def predict(self, x):
        y_pred = self.model.predict(x)
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
    ):
        if not hasattr(self.model, "feature_importances_"):
            raise NotImplementedError("Model does not support feature importance.")

        importances = self.model.feature_importances_
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
        for label, pred in zip(enc_labels, next_preds):
            logger.info(f"  {label.lower()}: {pred:.2f}")
        logger.info("")

        # Predict damage for remaining encounters
        logger.info("Predicted damage for remaining normal encounters:")
        remaining_preds = self.predict(remaining_enc)
        for label, pred in zip(remaining_labels, remaining_preds):
            logger.info(f"  {label.lower()}: {pred:.2f}")
        logger.info("")

        # Predict damage for boss encounter if applicable
        boss = current_act.boss()
        generator.test_encounters([boss] if boss else [])
        if boss:
            boss_enc, boss_labels = generator.test_encounters([boss])
            boss_pred = self.predict(boss_enc)
            logger.info(f"Predicted damage for boss encounter:")
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
            logger.info(
                f"  {second_boss.removeprefix('ENCOUNTER.').lower()}: {second_boss_pred[0]:.2f}"
            )
        logger.info("")
