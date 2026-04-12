import logging
from dataclasses import dataclass

from run_preprocessor.types import Enchantment, RawCard

logger = logging.getLogger(__name__)


@dataclass
class Card:
    id: str
    current_upgrade_level: int
    enchantment: Enchantment | None

    @classmethod
    def from_dict(cls, data: RawCard) -> "Card":
        try:
            return cls(
                id=data["id"],
                enchantment=data.get("enchantment"),
                current_upgrade_level=data.get("current_upgrade_level") or 0,
            )
        except KeyError as e:
            logger.error(f"Missing required card data key: {e}")
            raise
