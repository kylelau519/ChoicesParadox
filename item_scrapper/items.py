# Parse items with ids and make them ready to convert to one-hot vectors.
# It should also able to adapt player.deck, player.potions, and player.relics.

import json

DATA_DIR = "item_scrapper"

###### ALL cards dict ######
cards_json = json.load(open(f"{DATA_DIR}/cards.json"))
import logging

logger = logging.getLogger(__name__)

COLORLESS_CARDS: dict[str, int] = {}

IRONCLAD_CARDS: dict[str, int] = {}
NECROBINDER_CARDS: dict[str, int] = {}
REGENT_CARDS: dict[str, int] = {}
SILENT_CARDS: dict[str, int] = {}
DEFECT_CARDS: dict[str, int] = {}

EVENT_CARDS: dict[str, int] = {}
CURSE_CARDS: dict[str, int] = {}

QUEST_CARDS: dict[str, int] = {}

ALL_CARDS: dict[str, int] = {}

for card_dict in cards_json:
    if card_dict["color"] == "colorless":
        COLORLESS_CARDS["CARD." + card_dict["id"]] = 0
    elif card_dict["color"] == "ironclad":
        IRONCLAD_CARDS["CARD." + card_dict["id"]] = 0
    elif card_dict["color"] == "necrobinder":
        NECROBINDER_CARDS["CARD." + card_dict["id"]] = 0
    elif card_dict["color"] == "regent":
        REGENT_CARDS["CARD." + card_dict["id"]] = 0
    elif card_dict["color"] == "silent":
        SILENT_CARDS["CARD." + card_dict["id"]] = 0
    elif card_dict["color"] == "defect":
        DEFECT_CARDS["CARD." + card_dict["id"]] = 0
    elif card_dict["color"] == "curse":
        CURSE_CARDS["CARD." + card_dict["id"]] = 0
    elif card_dict["color"] == "event":
        EVENT_CARDS["CARD." + card_dict["id"]] = 0
    elif card_dict["color"] == "quest":
        QUEST_CARDS["CARD." + card_dict["id"]] = 0


ALL_CARDS.update(COLORLESS_CARDS)
ALL_CARDS.update(IRONCLAD_CARDS)
ALL_CARDS.update(NECROBINDER_CARDS)
ALL_CARDS.update(REGENT_CARDS)
ALL_CARDS.update(SILENT_CARDS)
ALL_CARDS.update(DEFECT_CARDS)
ALL_CARDS.update(EVENT_CARDS)

upgrades = {}
for k, v in ALL_CARDS.items():
    upgrades.update({f"{k}+": 0})
ALL_CARDS.update(upgrades)
ALL_CARDS.update(CURSE_CARDS)
ALL_CARDS.update(QUEST_CARDS)

###### ALL relic list ######
RELICS: dict[str, int] = {}
relics_json = json.load(open(f"{DATA_DIR}/relics.json"))
for relic_dict in relics_json:
    RELICS["RELIC." + relic_dict["id"]] = 0
    # RELICS.append("RELIC." + relic_dict["id"])

###### ALL potion dict ######
potions_json = json.load(open(f"{DATA_DIR}/potions.json"))
POTIONS: dict[str, int] = {}
for potion_dict in potions_json:
    POTIONS["POTION." + potion_dict["id"]] = 0


##### ALL encounters list ######
encounters_json = json.load(open(f"{DATA_DIR}/encounters.json"))
ACT1_OVERGROWTH_ENCOUNTERS: dict[str, int] = {}
ACT1_UNDERDOCKS_ENCOUNTERS: dict[str, int] = {}
ACT2_ENCOUNTERS: dict[str, int] = {}
ACT3_ENCOUNTERS: dict[str, int] = {}

ALL_ENCOUNTERS: dict[str, int] = {}
for encounter_dict in encounters_json:
    if (
        encounter_dict["act"] == "Underdocks"
        or encounter_dict["act"] == "Act 1 - Underdocks"
    ):
        ACT1_UNDERDOCKS_ENCOUNTERS["ENCOUNTER." + encounter_dict["id"]] = 0
    elif (
        encounter_dict["act"] == "Overgrowth"
        or encounter_dict["act"] == "Act 1 - Overgrowth"
    ):
        ACT1_OVERGROWTH_ENCOUNTERS["ENCOUNTER." + encounter_dict["id"]] = 0
    elif encounter_dict["act"] == "Act 2 - Hive":
        ACT2_ENCOUNTERS["ENCOUNTER." + encounter_dict["id"]] = 0
    elif encounter_dict["act"] == "Act 3 - Glory":
        ACT3_ENCOUNTERS["ENCOUNTER." + encounter_dict["id"]] = 0
    ALL_ENCOUNTERS["ENCOUNTER." + encounter_dict["id"]] = 0


def validate_card_id(card_id: str) -> str:
    card_id = card_id.strip().upper()
    if not card_id.startswith("CARD."):
        card_id = "CARD." + card_id
    if card_id not in ALL_CARDS:
        logger.error(f"Invalid card ID: {card_id}")
        raise ValueError(f"Invalid card ID: {card_id}")
    return card_id


def validate_relic_id(relic_id: str) -> str:
    relic_id = relic_id.strip().upper()
    if not relic_id.startswith("RELIC."):
        relic_id = "RELIC." + relic_id
    if relic_id not in RELICS:
        logger.error(f"Invalid relic ID: {relic_id}")
        raise ValueError(f"Invalid relic ID: {relic_id}")
    return relic_id


def validate_potion_id(potion_id: str) -> str:
    potion_id = potion_id.strip().upper()
    if not potion_id.startswith("POTION."):
        potion_id = "POTION." + potion_id
    if potion_id not in POTIONS:
        logger.error(f"Invalid potion ID: {potion_id}")
        raise ValueError(f"Invalid potion ID: {potion_id}")
    return potion_id


if __name__ == "__main__":
    print(ACT2_ENCOUNTERS)
