# A helper class to vectorize snapshot and able to modify the state for case study
import itertools

from item_scrapper.items import ALL_CARDS, ALL_ENCOUNTERS, POTIONS, RELICS
from run_preprocessor.snapshot import PlayerSnapshot
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
        if encounter_id not in ALL_ENCOUNTERS:
            raise ValueError(f"Encounter ID '{encounter_id}' is not valid.")
        self.encounter = {encounter_id: 1}

    def set_health(self, hp: int):
        self.current_hp = hp

    def set_max_health(self, max_hp: int):
        self.max_hp = max_hp

    def remove_card(self, card_id: str):
        self.deck.remove(card_id)

    def add_card(self, card_id: str):
        if card_id not in ALL_CARDS:
            raise ValueError(f"Card ID '{card_id}' is not valid.")
        self.deck.add(card_id)

    def add_potion(self, potion_id: str):
        if potion_id not in POTIONS:
            raise ValueError(f"Potion ID '{potion_id}' is not valid.")
        self.potions[potion_id] = self.potions.get(potion_id, 0) + 1

    def remove_potion(self, potion_id: str):
        if self.potions.get(potion_id, 0) <= 0:
            raise ValueError(
                f"Attempted to use potion '{potion_id}', but none are in inventory."
            )
        self.potions[potion_id] -= 1

    def add_relic(self, relic_id: str):
        if relic_id not in RELICS:
            raise ValueError(f"Relic ID '{relic_id}' is not valid.")
        self.relics[relic_id] = self.relics.get(relic_id, 0) + 1

    def remove_relic(self, relic_id: str):
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
        # Generate all combinations of using or not using each potion (0 = not used, 1 = used)
        for combination in itertools.product([0, 1], repeat=len(potion_ids)):
            # Create a label for this case
            used_potions = [
                potion_ids[i] for i, used in enumerate(combination) if used == 1
            ]
            label = "None" if not used_potions else " + ".join(used_potions)

            # Temporarily modify self.potions to reflect the used potions
            temp_potions = original_potions.copy()
            for i, used in enumerate(combination):
                if used == 1:
                    potion_id = potion_ids[i]
                    temp_potions[potion_id] -= 1
                    if temp_potions[potion_id] <= 0:
                        del temp_potions[potion_id]

            self.potions = temp_potions
            results.append((label, self.vectorize()))

        self.potions = original_potions  # restore original state
        return results

    def test_encounters(self, encounters: list[str]):
        current = self.encounter
        results = []
        for encounter in encounters:
            self.set_encounter(encounter)
            vectorized_input = self.vectorize()
            results.append((encounter, vectorized_input))
        self.encounter = current
        return results

    def test_adding_cards(self, card_ids: list[str]):
        current_deck = self.deck.cards.copy()
        results = []
        for card_id in card_ids:
            self.add_card(card_id)
            vectorized_input = self.vectorize()
            results.append((f"{card_id}", vectorized_input))
            self.deck.cards = current_deck.copy()  # restore original deck
        return results
