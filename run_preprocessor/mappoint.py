import json
from dataclasses import dataclass
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


if __name__ == "__main__":
    with open("testfiles/ironclad_a5_lose.run", "r", encoding="utf-8") as f:
        data = json.load(f)
        print(data["map_point_history"][0])
