import json
import logging
from dataclasses import dataclass
from typing import Any, cast

from .mappoint import RawMapPointHistory
from .player import RawPlayer
from .types import RunHistory

logger = logging.getLogger(__name__)


@dataclass
class RunMetadata:
    acts: list[str]
    ascension: int
    build_id: str
    game_mode: str
    killed_by_encounter: str
    killed_by_event: str
    modifiers: list[str]
    seed: str
    schema_version: int
    was_abandoned: bool
    win: bool

    # taking the whole json
    @classmethod
    def from_dict(cls, data: RunHistory) -> "RunMetadata":
        try:
            return cls(
                acts=data["acts"],
                ascension=data["ascension"],
                build_id=data["build_id"],
                game_mode=data["game_mode"],
                killed_by_encounter=data["killed_by_encounter"],
                killed_by_event=data["killed_by_event"],
                modifiers=data["modifiers"],
                seed=data["seed"],
                schema_version=data["schema_version"],
                was_abandoned=data["was_abandoned"],
                win=data["win"],
            )
        except KeyError as e:
            logger.error(f"Missing required metadata key: {e}")
            raise


# reader is a collection of unprocessed data from the run. It stores simple info like the whole map_point_history and metadata, but nothing like tracking the deck.
# it can build from deserialized json or a path to a json file
@dataclass
class RawData:
    run_metadata: RunMetadata
    players: list[RawPlayer]
    map_point_history: RawMapPointHistory
    _json: RunHistory
    _file_path: str = ""

    @classmethod
    def from_file(cls, file_path: str) -> "RawData":
        try:
            with open(file_path, "r") as f:
                data = cast(RunHistory, json.load(f))
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise
        try:
            run_metadata = RunMetadata.from_dict(data)
            players = [RawPlayer(**player) for player in data["players"]]
            map_point_history = RawMapPointHistory.from_dict(data["map_point_history"])
        except Exception as e:
            logger.error(f"Error parsing run file {file_path}: {e}")
            raise

        return cls(
            run_metadata=run_metadata,
            players=players,
            map_point_history=map_point_history,
            _json=data,
            _file_path=file_path,
        )
