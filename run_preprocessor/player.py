from dataclasses import dataclass
from enum import Enum

from run_preprocessor.card import RawCard
from run_preprocessor.types import Card, Player, Potion, Relic


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
    deck: list[RawCard]
    max_potion_slot_count: int
    potions: list[Potion]
    relics: list[Relic]

    @classmethod
    def from_dict(cls, data: Player) -> "RawPlayer":
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
