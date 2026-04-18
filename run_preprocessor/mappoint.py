import logging
from dataclasses import dataclass

from run_preprocessor.types import MapPoint, RawPlayerStats, Room

logger = logging.getLogger(__name__)


@dataclass
class RawMapPoint:
    map_point_type: str
    player_stats: list[RawPlayerStats]
    rooms: list[Room]
    turns_taken: int = 0

    @classmethod
    def from_dict(cls, data: MapPoint) -> "RawMapPoint":
        try:
            if not data["rooms"]:
                logger.warning("MapPoint has no rooms data.")
                turns_taken = 0
            else:
                turns_taken = data["rooms"][0].get("turns_taken", 0)

            return cls(
                map_point_type=data["map_point_type"],
                player_stats=data["player_stats"],
                rooms=data["rooms"],
                turns_taken=turns_taken,
            )
        except KeyError as e:
            logger.error(f"Missing required map point data key: {e}")
            raise

    def get_player_stat(self, player_id: int) -> RawPlayerStats:
        for ps in self.player_stats:
            if ps["player_id"] == player_id:
                return ps
        logger.error(f"player_id {player_id} not found in player_stats")
        raise Exception(
            f"get_player_stat: player_id {player_id} not found in player_stats"
        )

    def is_complete(self) -> bool:
        """Check if the map point has complete player stats."""
        if not self.player_stats:
            return False
        for ps in self.player_stats:
            if ps.get("max_hp", 0) <= 0:
                return False
        return True


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

            # Strip trailing incomplete map points
            while act_history and not act_history[-1].is_complete():
                logger.debug("Stripping incomplete map point from end of act.")
                act_history.pop()

            if act_history:
                act_num_floors.append(len(act_history))
                map_point_history.append(act_history)

        return cls(map_point_history=map_point_history, act_num_floors=act_num_floors)

    def __getitem__(self, index: int):
        return self.map_point_history[index]

    def flatten(self) -> list[RawMapPoint]:
        return [mp for act in self.map_point_history for mp in act]

    def is_complete(self) -> bool:
        """Check if the last map point in history is complete."""
        flattened = self.flatten()
        if not flattened:
            return True  # No history yet (e.g., just started)
        return flattened[-1].is_complete()
