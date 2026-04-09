from dataclasses import dataclass, field, fields
from enum import Enum
from typing import Any, Dict

from .mappoint import RawMapPointHistory


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


class RelicTracker:
    def __init__(self, data: RawMapPointHistory, starting_relics: list[str] = None):
        self.data = data
        self.starting_relics = starting_relics or []
        self.relic_history = set()

    # not working yet
    def track_act_floor(self, act: int, floor: int, player_id: int = 1) -> list[str]:
        # first check if rawmapPointHistory has that floor
        self.relic_history = set(self.starting_relics)

        if act >= len(self.data.map_point_history):
            return sorted(list(self.relic_history))

        # iterate over the history:
        for a in range(act + 1):
            nodes = self.data.map_point_history[a]
            limit = floor + 1 if a == act else len(nodes)

            for f in range(min(limit, len(nodes))):
                map_point = nodes[f]
                # get player_stats, get the correct stat with player_id.
                for stats in map_point.player_stats:
                    if stats.get("player_id") == player_id:
                        # check if keyword relic_choices is there, if so check if was_picked is true, if so add to relic_history
                        if "relic_choices" in stats:
                            for choice in stats["relic_choices"]:
                                if choice.get("was_picked"):
                                    self.relic_history.add(choice["choice"])

                        # check if keyword bought_relics is there, if so add all relics in that list to relic_history
                        if "bought_relics" in stats:
                            for relic in stats["bought_relics"]:
                                self.relic_history.add(relic)

                        # check if keyword relics_removed is there, if so remove that relic from relic_history
                        if "relics_removed" in stats:
                            for relic in stats["relics_removed"]:
                                self.relic_history.discard(relic)

                        if "relic_removed" in stats:
                            relic = stats["relic_removed"]
                            if isinstance(relic, list):
                                for r in relic:
                                    self.relic_history.discard(r)
                            else:
                                self.relic_history.discard(relic)

        return sorted(list(self.relic_history))


if __name__ == "__main__":
    import json

    file = json.load(open("testfiles/ironclad_a5_lose.run", "r"))
    player_data = file["players"][0]
    player = RawPlayer.from_dict(player_data)
    assert player.character == Character.IRONCLAD
    assert player.relics[0] == {"floor_added_to_deck": 1, "id": "RELIC.BURNING_BLOOD"}
    assert player.deck[0] == {"floor_added_to_deck": 1, "id": "CARD.STRIKE_IRONCLAD"}

    relic_file = json.load(open("testfiles/necrobinder_a7_remove_relics.run", "r"))
    relics = RelicTracker(
        RawMapPointHistory.from_dict(file["map_point_history"]),
        starting_relics=["RELIC.STARTER_RELIC"],
    )
    print(relics.track_act_floor(2, 5))
