import json
from dataclasses import dataclass, field, fields
from typing import List

from .mappoint import RawMapPointHistory
from .player import RawPlayer


@dataclass
class RunMetadata:
    acts: List[str]
    ascension: int
    build_id: str
    game_mode: str
    killed_by_encounter: str
    killed_by_event: str
    modifiers: List[str]
    seed: str
    schema_version: int
    was_abandoned: bool
    win: bool

    # taking the whole json
    @classmethod
    def from_dict(cls, data: dict) -> "RunMetadata":
        valid_keys = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)


# reader is a collection of unprocessed data from the run. It stores simple info like the whole map_point_history and metadata, but nothing like tracking the deck.
# it can build from deserialized json or a path to a json file
@dataclass
class RawData:
    run_metadata: RunMetadata
    players: List[RawPlayer]
    map_point_history: RawMapPointHistory
    _json: dict = field(default_factory=dict)
    _file_path: str = ""

    @classmethod
    def from_json(cls, json):
        data = json.loads(json)
        run_metadata = RunMetadata.from_dict(data)
        players = [RawPlayer.from_dict(player) for player in data["players"]]
        map_point_history = RawMapPointHistory.from_dict(data["map_point_history"])
        return cls(
            run_metadata=run_metadata,
            players=players,
            map_point_history=map_point_history,
            _json=data,
        )

    @classmethod
    def from_file(cls, file_path):
        with open(file_path, "r") as f:
            data = json.load(f)
        run_metadata = RunMetadata.from_dict(data)
        players = [RawPlayer.from_dict(player) for player in data["players"]]
        map_point_history = RawMapPointHistory.from_dict(data["map_point_history"])
        return cls(
            run_metadata=run_metadata,
            players=players,
            map_point_history=map_point_history,
            _json=data,
            _file_path=file_path,
        )

    def update():
        pass


if __name__ == "__main__":
    raw_data = RawData.from_file("testfiles/ironclad_a5_lose.run")
    assert raw_data.run_metadata.ascension == 5
    assert raw_data.run_metadata.game_mode == "standard"
