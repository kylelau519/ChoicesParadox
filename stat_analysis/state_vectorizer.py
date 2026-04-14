# A helper class to vectorize snapshot and able to modify the state for case study
import itertools

import scipy.sparse as sp
from item_scrapper.items import ALL_CARDS, ALL_ENCOUNTERS, POTIONS, RELICS
from run_preprocessor.deck import validate_card_id
from stat_analysis.preprocess import GLOBAL_VECTORIZER, MASTER_SCHEMA, MasterSchema


class TestCaseGenerator:
    def __init__(self, snapshot: MasterSchema):
        self.current_hp = snapshot.current_hp
        self.max_hp = snapshot.max_hp
        self.deck = snapshot.deck
        self.potions = snapshot.potions
        self.relics = snapshot.relics
        self.encounter = None

    def set_encounter(self, encounter_id: str):
        encounter_id = encounter_id.strip().upper()
        if not encounter_id.startswith("ENCOUNTER."):
            encounter_id = "ENCOUNTER." + encounter_id
        if encounter_id not in ALL_ENCOUNTERS:
            raise ValueError(f"Encounter ID '{encounter_id}' is not valid.")
        self.encounter = {encounter_id: 1}

    def set_health(self, hp: int):
        self.current_hp = hp

    def set_max_health(self, max_hp: int):
        self.max_hp = max_hp

    def remove_card(self, card_id: str):
        # self.deck.remove already handles normalization and validation
        self.deck.remove(card_id)

    def add_card(self, card_id: str):
        # self.deck.add already handles normalization and validation
        self.deck.add(card_id)

    def upgrade_card(self, card_id: str):
        # card_id should be something like "CARD.STRIKE_R"
        if card_id.endswith("+"):
            raise ValueError(f"Card {card_id} is already upgraded.")

        if not self.deck.correlated:
            self.remove_card(card_id)
        upgraded_id = card_id + "+"
        self.add_card(upgraded_id)

    def add_potion(self, potion_id: str):
        potion_id = potion_id.strip().upper()
        if not potion_id.startswith("POTION."):
            potion_id = "POTION." + potion_id
        if potion_id not in POTIONS:
            raise ValueError(f"Potion ID '{potion_id}' is not valid.")
        self.potions[potion_id] = self.potions.get(potion_id, 0) + 1

    def remove_potion(self, potion_id: str):
        potion_id = potion_id.strip().upper()
        if not potion_id.startswith("POTION."):
            potion_id = "POTION." + potion_id
        if self.potions.get(potion_id, 0) <= 0:
            raise ValueError(
                f"Attempted to use potion '{potion_id}', but none are in inventory."
            )
        self.potions[potion_id] -= 1

    def add_relic(self, relic_id: str):
        relic_id = relic_id.strip().upper()
        if not relic_id.startswith("RELIC."):
            relic_id = "RELIC." + relic_id
        if relic_id not in RELICS:
            raise ValueError(f"Relic ID '{relic_id}' is not valid.")
        self.relics[relic_id] = self.relics.get(relic_id, 0) + 1

    def remove_relic(self, relic_id: str):
        relic_id = relic_id.strip().upper()
        if not relic_id.startswith("RELIC."):
            relic_id = "RELIC." + relic_id
        if self.relics.get(relic_id, 0) <= 0:
            raise ValueError(
                f"Attempted to remove relic '{relic_id}', but none are in inventory."
            )
        self.relics[relic_id] -= 1

    def vectorize(self):
        if self.encounter is None:
            raise ValueError("Encounter must be set before vectorizing.")
        input_dict = {
            "current_hp": self.current_hp,
            "max_hp": self.max_hp,
            **self.deck.cards,
            **self.potions,
            **self.relics,
            **self.encounter,
        }
        return GLOBAL_VECTORIZER.transform([input_dict])

    def test_potions(self):
        potion_ids = list(self.potions.keys())
        original_potions = self.potions.copy()

        results = []
        labels = []
        # Generate all combinations of using or not using each potion (0 = stay in inventory, 1 = used/removed)
        for combination in itertools.product([0, 1], repeat=len(potion_ids)):
            # Inventory contains potions where combination[i] == 0
            remaining_potions = [
                potion_ids[i] for i, used in enumerate(combination) if used == 0
            ]
            remaining_labels = [p.replace("POTION.", "") for p in remaining_potions]
            label = "None" if not remaining_labels else " + ".join(remaining_labels)

            # Temporarily modify self.potions to reflect the remaining potions
            temp_potions = original_potions.copy()
            for i, used in enumerate(combination):
                if used == 1:
                    potion_id = potion_ids[i]
                    temp_potions[potion_id] -= 1
                    if temp_potions[potion_id] <= 0:
                        del temp_potions[potion_id]

            self.potions = temp_potions
            labels.append(label)
            results.append(self.vectorize())

        self.potions = original_potions  # restore original state
        results = sp.vstack(results)
        return results, labels

    def test_encounters(self, encounters: list[str]):
        original_encounter = self.encounter
        results = []
        labels = []
        for encounter in encounters:
            self.set_encounter(encounter)
            label = encounter.replace("ENCOUNTER.", "")
            results.append(self.vectorize())
            labels.append(label)
        self.encounter = original_encounter  # restore original encounter
        results = sp.vstack(results)
        return results, labels

    def test_adding_cards(self, card_ids: list[str], pick: int = 1):
        original_deck_cards = self.deck.cards.copy()
        results = []
        labels = []

        # Generate combinations of adding 0 up to 'pick' cards from the pool
        for r in range(pick + 1):
            for combination in itertools.combinations(card_ids, r):
                # Normalize card IDs first
                valid_combination = [validate_card_id(c) for c in combination]
                added_labels = [c.replace("CARD.", "") for c in valid_combination]
                label = "Original" if not added_labels else " + ".join(added_labels)

                # Temporarily modify self.deck.cards
                self.deck.cards = original_deck_cards.copy()
                for card_id in valid_combination:
                    self.deck.add(card_id)

                labels.append(label)
                results.append(self.vectorize())

        self.deck.cards = original_deck_cards  # restore
        results = sp.vstack(results)
        return results, labels

    def test_adding_relics(self, relic_ids: list[str], pick: int = 1):
        original_relics = self.relics.copy()
        results = []
        labels = []

        # Generate combinations of adding 0 up to 'pick' relics from the pool
        for r in range(pick + 1):
            for combination in itertools.combinations(relic_ids, r):
                valid_combination = [c.strip().upper() for c in combination]
                valid_combination = [
                    f"RELIC.{c}" if not c.startswith("RELIC.") else c
                    for c in valid_combination
                ]
                for relic_id in valid_combination:
                    if relic_id not in RELICS:
                        raise ValueError(f"Relic ID '{relic_id}' is not valid.")
                added_labels = [c.replace("RELIC.", "") for c in valid_combination]
                label = "Original" if not added_labels else " + ".join(added_labels)

                # Temporarily modify self.relics
                temp_relics = original_relics.copy()
                for relic_id in valid_combination:
                    temp_relics[relic_id] = temp_relics.get(relic_id, 0) + 1

                self.relics = temp_relics
                labels.append(label)
                results.append(self.vectorize())

        self.relics = original_relics  # restore
        results = sp.vstack(results)
        return results, labels

    def test_remove_card(self, card_id: str):
        original_deck_cards = self.deck.cards.copy()
        self.remove_card(card_id)
        result = self.vectorize()
        label = f"Removed {card_id.replace('CARD.', '')}"
        self.deck.cards = original_deck_cards  # restore
        return result, label

    def test_removals(self, card_ids: list[str]):
        results = [self.vectorize()]
        labels = ["Original"]
        for card_id in card_ids:
            res, label = self.test_remove_card(card_id)
            results.append(res)
            labels.append(label)
        return sp.vstack(results), labels

    def test_upgrade_card(self, card_id: str):
        original_deck_cards = self.deck.cards.copy()
        if card_id.endswith("+"):
            return None, None
        try:
            self.upgrade_card(card_id)
            result = self.vectorize()
            label = f"Upgraded {card_id.replace('CARD.', '')}"
        except Exception:
            return None, None
        finally:
            self.deck.cards = original_deck_cards  # restore
        return result, label

    def test_upgrades(self, card_ids: list[str]):
        results = [self.vectorize()]
        labels = ["Original"]
        for card_id in card_ids:
            res, label = self.test_upgrade_card(card_id)
            if res is not None:
                results.append(res)
                labels.append(label)
        return sp.vstack(results), labels
