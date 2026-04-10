# Parse items with ids and make them ready to convert to one-hot vectors.
# It should also able to adapt player.deck, player.potions, and player.relics.

import json

###### ALL cards dict ######
cards_json = json.load(open("item_scrapper/cards.json"))

COLORLESS_CARDS: dict[str, int] = {}

IRONCLAD_CARDS: dict[str, int] = {}
NECROBINDER_CARDS: dict[str, int] = {}
REGENT_CARDS: dict[str, int] = {}
SILENT_CARDS: dict[str, int] = {}
DEFACT_CARDS: dict[str, int] = {}

CURSE_CARDS: dict[str, int] = {}

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
    elif card_dict["color"] == "defact":
        DEFACT_CARDS["CARD." + card_dict["id"]] = 0
    elif card_dict["color"] == "curse":
        CURSE_CARDS["CARD." + card_dict["id"]] = 0

ALL_CARDS: dict[str, int] = {}
ALL_CARDS.update(COLORLESS_CARDS)
ALL_CARDS.update(IRONCLAD_CARDS)
ALL_CARDS.update(NECROBINDER_CARDS)
ALL_CARDS.update(REGENT_CARDS)
ALL_CARDS.update(SILENT_CARDS)
ALL_CARDS.update(DEFACT_CARDS)

upgrades = {}
for k, v in ALL_CARDS.items():
    upgrades.update({f"{k}+": 0})
ALL_CARDS.update(upgrades)
ALL_CARDS.update(CURSE_CARDS)


###### ALL relic list ######
RELICS: list[str] = []
relics_json = json.load(open("item_scrapper/relics.json"))
for relic_dict in relics_json:
    RELICS.append("RELIC." + relic_dict["id"])

###### ALL potion dict ######
potions_json = json.load(open("item_scrapper/potions.json"))
POTIONS: dict[str, int] = {}
for potion_dict in potions_json:
    POTIONS["POTION." + potion_dict["id"]] = 0


##### ALL encounters list ######
encounters_json = json.load(open("item_scrapper/encounters.json"))
ACT1_OVERGROWTH_ENCOUNTERS: list[str] = []
ACT1_UNDERDOCKS_ENCOUNTERS: list[str] = []
ACT2_ENCOUNTERS: list[str] = []
ACT3_ENCOUNTERS: list[str] = []

ALL_ENCOUNTERS: list[str] = []
for encounter_dict in encounters_json:
    if (
        encounter_dict["act"] == "Underdocks"
        or encounter_dict["act"] == "Act 1 - Underdocks"
    ):
        ACT1_UNDERDOCKS_ENCOUNTERS.append("ENCOUNTER." + encounter_dict["id"])
    elif (
        encounter_dict["act"] == "Overgrowth"
        or encounter_dict["act"] == "Act 1 - Overgrowth"
    ):
        ACT1_OVERGROWTH_ENCOUNTERS.append("ENCOUNTER." + encounter_dict["id"])
    elif encounter_dict["act"] == "Act 2 - Hive":
        ACT2_ENCOUNTERS.append("ENCOUNTER." + encounter_dict["id"])
    elif encounter_dict["act"] == "Act 3 - Glory":
        ACT3_ENCOUNTERS.append("ENCOUNTER." + encounter_dict["id"])
    ALL_ENCOUNTERS.append("ENCOUNTER." + encounter_dict["id"])

if __name__ == "__main__":
    print("act1 overgrowth encounters: ", ACT1_OVERGROWTH_ENCOUNTERS)
