from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any, Dict


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
                raise ValueError(f"Unknown character: {label}")

    def __str__(self):
        return self.value.split(".")[1].lower()


# Player is defined in the .run, does not include gold, hp, or potion info.
@dataclass
class RawPlayer:
    id: str
    character: Character
    deck: list[dict]
    max_potion_slot_count: int
    relics: list[dict]

    @classmethod
    def from_dict(cls, data: dict) -> "RawPlayer":
        valid_keys = {field.name for field in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        if "character" in filtered_data:
            filtered_data["character"] = Character.from_str(filtered_data["character"])
        return cls(**filtered_data)


@dataclass
class RawCard:
    floor_added_to_deck: int
    id: str
    enchantment: Dict[str, Any] = field(default_factory=dict)
    current_upgrade_level: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "RawCard":
        valid_keys = {field.name for field in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)



if __name__ == "__main__":
    import json

    file = json.load(open("testfiles/ironclad_a5_lose.run", "r"))
    player_data = file["players"][0]
    player = RawPlayer.from_dict(player_data)
    assert player.character == Character.IRONCLAD
    assert player.relics[0] == {"floor_added_to_deck": 1, "id": "RELIC.BURNING_BLOOD"}
    assert player.deck[0] == {"floor_added_to_deck": 1, "id": "CARD.STRIKE_IRONCLAD"}

    # relic_file = json.load(open("testfiles/necrobinder_a7_remove_relics.run", "r"))
    # relics = RelicTracker(
    #     RawMapPointHistory.from_dict(file["map_point_history"]),
    #     starting_relics=["RELIC.STARTER_RELIC"],
    # )
    # print(relics.track_act_floor(2, 5))
