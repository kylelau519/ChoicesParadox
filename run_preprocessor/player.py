import logging
from dataclasses import dataclass
from enum import Enum

from run_preprocessor.card import RawCard
from run_preprocessor.types import Player, Potion, Relic

logger = logging.getLogger(__name__)


class Character(Enum):
    IRONCLAD = "IRONCLAD"
    SILENT = "SILENT"
    DEFECT = "DEFECT"
    REGENT = "REGENT"
    NECROBINDER = "NECROBINDER"

    @classmethod
    def from_str(cls, label: str) -> "Character":
        match label:
            case "CHARACTER.IRONCLAD":
                return Character.IRONCLAD
            case "CHARACTER.SILENT":
                return Character.SILENT
            case "CHARACTER.DEFECT":
                return Character.DEFECT
            case "CHARACTER.REGENT":
                return Character.REGENT
            case "CHARACTER.NECROBINDER":
                return Character.NECROBINDER
            case _:
                logger.error(f"Unknown character label: {label}")
                raise ValueError(f"Unknown character: {label}")

    def __str__(self):
        return self.value.lower()


# Player is defined in the .run, does not include gold, hp, or potion info.
@dataclass
class RawPlayer:
    id: str
    character: Character
    deck: list[RawCard]
    max_potion_slot_count: int
    potions: list[Potion]
    relics: list[Relic]

    @classmethod
    def from_dict(cls, data: Player) -> "RawPlayer":
        try:
            deck: list[RawCard] = []
            for card in data["deck"]:
                deck.append(RawCard.from_dict(card))

            return cls(
                id=str(data["id"]),
                character=Character.from_str(data["character"]),
                deck=deck,
                max_potion_slot_count=data["max_potion_slot_count"],
                potions=data["potions"],
                relics=data["relics"],
            )
        except KeyError as e:
            logger.error(f"Missing required player data key: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing player data: {e}")
            raise

    @classmethod
    def generate_starter_deck(cls, character: Character):
        deck: list[RawCard] = []
        match character:
            case Character.DEFECT:
                deck.append(RawCard(1, "CARD.ZAP", None, 0))
                deck.append(RawCard(1, "CARD.DUALCAST", None, 0))
                for _ in range(4):
                    deck.append(RawCard(1, "CARD.STRIKE_DEFECT", None, 0))
                    deck.append(RawCard(1, "CARD.DEFEND_DEFECT", None, 0))

            case Character.IRONCLAD:
                deck.append(RawCard(1, "CARD.BASH", None, 0))
                for _ in range(5):
                    deck.append(RawCard(1, "CARD.STRIKE_IRONCLAD", None, 0))
                for _ in range(4):
                    deck.append(RawCard(1, "CARD.DEFEND_IRONCLAD", None, 0))

            case Character.NECROBINDER:
                deck.append(RawCard(1, "CARD.BODYGUARD", None, 0))
                deck.append(RawCard(1, "CARD.UNLEASH", None, 0))
                for _ in range(4):
                    deck.append(RawCard(1, "CARD.STRIKE_NECROBINDER", None, 0))
                    deck.append(RawCard(1, "CARD.DEFEND_NECROBINDER", None, 0))

            case Character.REGENT:
                deck.append(RawCard(1, "CARD.FALLING_STAR", None, 0))
                deck.append(RawCard(1, "CARD.VENERATE", None, 0))
                for _ in range(4):
                    deck.append(RawCard(1, "CARD.STRIKE_REGENT", None, 0))
                    deck.append(RawCard(1, "CARD.DEFEND_REGENT", None, 0))

            case Character.SILENT:
                deck.append(RawCard(1, "CARD.NEUTRALIZE", None, 0))
                deck.append(RawCard(1, "CARD.SURVIVOR", None, 0))
                for _ in range(5):
                    deck.append(RawCard(1, "CARD.STRIKE_SILENT", None, 0))
                    deck.append(RawCard(1, "CARD.DEFEND_SILENT", None, 0))

        return deck

    @classmethod
    def generate_starter_relic(cls, character: Character):
        if character == Character.DEFECT:
            return "RELIC.CRACKED_CORE"
        elif character == Character.IRONCLAD:
            return "RELIC.BURNING_BLOOD"
        elif character == Character.NECROBINDER:
            return "RELIC.BOUND_PHYLACTERY"
        elif character == Character.REGENT:
            return "RELIC.DIVINE_RIGHT"
        elif character == Character.SILENT:
            return "RELIC.RING_OF_THE_SNAKE"
