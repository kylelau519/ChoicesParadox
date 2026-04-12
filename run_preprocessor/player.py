import logging
from dataclasses import dataclass
from enum import Enum

from run_preprocessor.card import Card
from run_preprocessor.types import Potion, RawPlayer, Relic

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
class Player:
    id: int
    character: Character
    deck: list[Card]
    max_potion_slot_count: int
    potions: list[Potion]
    relics: list[Relic]

    @classmethod
    def from_dict(cls, data: RawPlayer) -> "Player":
        try:
            deck: list[Card] = []
            for card in data["deck"]:
                deck.append(Card.from_dict(card))

            return cls(
                id=data["id"],
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
        deck: list[Card] = []
        match character:
            case Character.DEFECT:
                deck.append(Card("CARD.ZAP", 0, None))
                deck.append(Card("CARD.DUALCAST", 0, None))
                for _ in range(4):
                    deck.append(Card("CARD.STRIKE_DEFECT", 0, None))
                    deck.append(Card("CARD.DEFEND_DEFECT", 0, None))

            case Character.IRONCLAD:
                deck.append(Card("CARD.BASH", 0, None))
                for _ in range(5):
                    deck.append(Card("CARD.STRIKE_IRONCLAD", 0, None))
                for _ in range(4):
                    deck.append(Card("CARD.DEFEND_IRONCLAD", 0, None))

            case Character.NECROBINDER:
                deck.append(Card("CARD.BODYGUARD", 0, None))
                deck.append(Card("CARD.UNLEASH", 0, None))
                for _ in range(4):
                    deck.append(Card("CARD.STRIKE_NECROBINDER", 0, None))
                    deck.append(Card("CARD.DEFEND_NECROBINDER", 0, None))

            case Character.REGENT:
                deck.append(Card("CARD.FALLING_STAR", 0, None))
                deck.append(Card("CARD.VENERATE", 0, None))
                for _ in range(4):
                    deck.append(Card("CARD.STRIKE_REGENT", 0, None))
                    deck.append(Card("CARD.DEFEND_REGENT", 0, None))

            case Character.SILENT:
                deck.append(Card("CARD.NEUTRALIZE", 0, None))
                deck.append(Card("CARD.SURVIVOR", 0, None))
                for _ in range(5):
                    deck.append(Card("CARD.STRIKE_SILENT", 0, None))
                    deck.append(Card("CARD.DEFEND_SILENT", 0, None))

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
