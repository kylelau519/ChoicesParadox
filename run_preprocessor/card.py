from dataclasses import dataclass

from run_preprocessor.types import Card, Enchantment

@dataclass
class RawCard:
    floor_added_to_deck: int
    id: str
    enchantment: Enchantment | None
    current_upgrade_level: int

    @classmethod
    def from_dict(cls, data: Card) -> "RawCard":
        return cls(
            id=data["id"],
            floor_added_to_deck=data["floor_added_to_deck"],
            enchantment=data.get("enchantment"),
            current_upgrade_level=data.get("current_upgrade_level") or 0,
        )


