import json
from dataclasses import dataclass
from enum import Enum

from run_preprocessor.types import MapPoint, PlayerStats, Room


@dataclass
class RawMapPoint:
    map_point_type: str
    player_stats: list[PlayerStats]
    rooms: list[Room]
    turns_taken: int = 0

    @classmethod
    def from_dict(cls, data: MapPoint) -> "RawMapPoint":
        return cls(
            map_point_type=data["map_point_type"],
            player_stats=data["player_stats"],
            rooms=data["rooms"],
            turns_taken=data["rooms"][0]["turns_taken"],
        )


@dataclass
class RawMapPointHistory:
    map_point_history: list[list[RawMapPoint]]  # each act is an element
    act_num_floors: list[int]  # the floor number of the first floor of each act

    @classmethod
    def from_dict(cls, data: list[list[MapPoint]]) -> "RawMapPointHistory":
        map_point_history: list[list[RawMapPoint]] = []
        act_num_floors: list[int] = []
        for act in data:
            act_history: list[RawMapPoint] = []
            for map_point in act:
                act_history.append(RawMapPoint.from_dict(map_point))
            act_num_floors.append(len(act_history))
            map_point_history.append(act_history)

        return cls(map_point_history=map_point_history, act_num_floors=act_num_floors)

    def __getitem__(self, index: int):
        return self.map_point_history[index]

    def flatten(self) -> list[RawMapPoint]:
        return [mp for act in self.map_point_history for mp in act]


if __name__ == "__main__":
    with open("testfiles/ironclad_a5_lose.run", "r", encoding="utf-8") as f:
        data = json.load(f)
    map_point_history = RawMapPointHistory.from_dict(data["map_point_history"])
    first_node = map_point_history.map_point_history[0][0]
    assert first_node.map_point_type == "ancient"
