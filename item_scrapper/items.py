# Parse items with ids and make them ready to convert to one-hot vectors.
# It should also able to adapt player.deck, player.potions, and player.relics.

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Global definition of versions to use across the project
SUPPORTED_BUILD_IDS = ["0.102", "0.103"]

# Base directory for the project (root)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_ITEMS_DIR = BASE_DIR / "data" / "items"
SCRAPPER_DIR = BASE_DIR / "item_scrapper"


def load_all_versions(filename):
    all_items = {}

    # 1. Load from all version directories in data/items/v*
    if DATA_ITEMS_DIR.exists():
        # Get all directories starting with 'v' and sort them
        version_dirs = sorted(
            [
                d
                for d in DATA_ITEMS_DIR.iterdir()
                if d.is_dir()
                and d.name.startswith("v")
                and any(v in d.name for v in SUPPORTED_BUILD_IDS)
            ]
        )

        for v_dir in version_dirs:
            filepath = v_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, "r") as f:
                        items = json.load(f)
                        for item in items:
                            # Use ID as key to merge versions, keeping latest version of the same ID
                            all_items[item["id"]] = item
                except Exception as e:
                    logger.error(f"Error loading {filepath}: {e}")

    # 2. Load from item_scrapper directory as fallback/additional
    scrapper_file = SCRAPPER_DIR / filename
    if scrapper_file.exists():
        try:
            with open(scrapper_file, "r") as f:
                items = json.load(f)
                for item in items:
                    if item["id"] not in all_items:
                        all_items[item["id"]] = item
        except Exception as e:
            logger.error(f"Error loading {scrapper_file}: {e}")

    return list(all_items.values())


###### ALL cards dict ######
cards_json = load_all_versions("cards.json")

COLORLESS_CARDS: dict[str, int] = {}
IRONCLAD_CARDS: dict[str, int] = {}
NECROBINDER_CARDS: dict[str, int] = {}
REGENT_CARDS: dict[str, int] = {}
SILENT_CARDS: dict[str, int] = {}
DEFECT_CARDS: dict[str, int] = {}

EVENT_CARDS: dict[str, int] = {}
CURSE_CARDS: dict[str, int] = {}
QUEST_CARDS: dict[str, int] = {}
STATUS_CARDS: dict[str, int] = {}
TOKEN_CARDS: dict[str, int] = {}
UNKNOWN_CARDS: dict[str, int] = {}

ALL_CARDS: dict[str, int] = {}

for card_dict in cards_json:
    card_id = "CARD." + card_dict["id"]
    color = card_dict.get("color")

    if color == "colorless":
        COLORLESS_CARDS[card_id] = 0
    elif color == "ironclad":
        IRONCLAD_CARDS[card_id] = 0
    elif color == "necrobinder":
        NECROBINDER_CARDS[card_id] = 0
    elif color == "regent":
        REGENT_CARDS[card_id] = 0
    elif color == "silent":
        SILENT_CARDS[card_id] = 0
    elif color == "defect":
        DEFECT_CARDS[card_id] = 0
    elif color == "curse":
        CURSE_CARDS[card_id] = 0
    elif color == "event":
        EVENT_CARDS[card_id] = 0
    elif color == "quest":
        QUEST_CARDS[card_id] = 0
    elif color == "status":
        STATUS_CARDS[card_id] = 0
    elif color == "token":
        TOKEN_CARDS[card_id] = 0
    elif color == "unknown":
        UNKNOWN_CARDS[card_id] = 0


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
ALL_CARDS.update(STATUS_CARDS)
ALL_CARDS.update(TOKEN_CARDS)
ALL_CARDS.update(UNKNOWN_CARDS)

###### ALL relic list ######
relics_json = load_all_versions("relics.json")
RELICS: dict[str, int] = {}
for relic_dict in relics_json:
    RELICS["RELIC." + relic_dict["id"]] = 0

###### ALL potion dict ######
potions_json = load_all_versions("potions.json")
POTIONS: dict[str, int] = {}
for potion_dict in potions_json:
    POTIONS["POTION." + potion_dict["id"]] = 0


##### ALL encounters list ######
encounters_json = load_all_versions("encounters.json")
ACT1_OVERGROWTH_ENCOUNTERS: dict[str, int] = {}
ACT1_UNDERDOCKS_ENCOUNTERS: dict[str, int] = {}
ACT2_ENCOUNTERS: dict[str, int] = {}
ACT3_ENCOUNTERS: dict[str, int] = {}

ALL_ENCOUNTERS: dict[str, int] = {}
for encounter_dict in encounters_json:
    eid = "ENCOUNTER." + encounter_dict["id"]
    act = encounter_dict.get("act", "")
    if act in ["Underdocks", "Act 1 - Underdocks"]:
        ACT1_UNDERDOCKS_ENCOUNTERS[eid] = 0
    elif act in ["Overgrowth", "Act 1 - Overgrowth"]:
        ACT1_OVERGROWTH_ENCOUNTERS[eid] = 0
    elif act == "Act 2 - Hive":
        ACT2_ENCOUNTERS[eid] = 0
    elif act == "Act 3 - Glory":
        ACT3_ENCOUNTERS[eid] = 0
    ALL_ENCOUNTERS[eid] = 0


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
    print(f"Total cards: {len(ALL_CARDS)}")
    print(f"Total relics: {len(RELICS)}")
    print(f"Total potions: {len(POTIONS)}")
    print(f"Total encounters: {len(ALL_ENCOUNTERS)}")
    print(f"Act 2 encounters: {len(ACT2_ENCOUNTERS)}")
