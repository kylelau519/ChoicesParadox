import json
from dataclasses import dataclass, fields
from enum import Enum
from typing import List


class RoomType(Enum):
    ELITE = "ELITE"
    MONSTER = "MONSTER"
    EVENT = "EVENT"
    BOSS = "BOSS"
    SHOP = "SHOP"
    TREASURE = "TREASURE"


class Room:
    def __init__(self, room_type: RoomType, floor: int):
        self.room_type = room_type
        self.floor = floor


@dataclass
class Encounter:
    model_id: str
    monster_ids: List[str]


class Event:
    pass


@dataclass
class RawMapPoint:
    map_point_type: str
    player_stats: dict
    rooms: List[dict]
    turns_taken: int = 0

    # taking only the relevant dict
    @classmethod
    def from_dict(cls, data: dict) -> "RawMapPoint":
        valid_keys = {field.name for field in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)


@dataclass
class RawMapPointHistory:
    map_point_history: List[List[RawMapPoint]]  # each act is an element

    # taking list of acts
    @classmethod
    def from_dict(cls, data: list) -> "RawMapPointHistory":
        map_point_history = []
        for act in data:
            act_history = []
            for map_point in act:
                act_history.append(RawMapPoint.from_dict(map_point))
            map_point_history.append(act_history)
        return cls(map_point_history=map_point_history)


if __name__ == "__main__":
    with open("testfiles/ironclad_a5_lose.run", "r", encoding="utf-8") as f:
        data = json.load(f)
    map_point_history = RawMapPointHistory.from_dict(data["map_point_history"])
    first_node = map_point_history.map_point_history[0][0]
    assert first_node.map_point_type == "ancient"
