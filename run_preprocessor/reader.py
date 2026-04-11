import json
import logging
from dataclasses import dataclass, field, fields
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
    def from_file(cls, file_path: str):
        logger.info(f"Loading run file: {file_path}")
        try:
            with open(file_path, "r") as f:
                data = cast(RunHistory, json.load(f))
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to read run file {file_path}: {e}")
            raise

        try:
            run_metadata = RunMetadata.from_dict(data)
            players = [RawPlayer.from_dict(player) for player in data["players"]]
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


@dataclass
class ActDetails:
    id: str
    ancient_id: str
    boss_id: str  # not sure about this
    elite_encounters_ids: list[str]
    elite_encounters_visited: int
    event_ids: list[str]
    event_visited: int
    normal_encounters_ids: list[str]
    normal_encounters_visited: int
    second_boss_id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActDetails":
        rooms = data.get("rooms", [])
        try:
            return cls(
                id=data["id"],
                ancient_id=data["ancient_id"],
                boss_id=rooms["boss_id"],
                second_boss_id=rooms.get("second_boss_id", ""),
                elite_encounters_ids=rooms["elite_encounters_ids"],
                elite_encounters_visited=rooms["elite_encounters_visited"],
                event_ids=rooms["event_ids"],
                event_visited=rooms["event_visited"],
                normal_encounters_ids=rooms["normal_encounters_ids"],
                normal_encounters_visited=rooms["normal_encounters_visited"],
            )
        except KeyError as e:
            logger.error(f"Missing required act details key: {e}")
            raise


@dataclass
class CurrentSaveReader:
    acts: list[ActDetails]
    current_act_index: int
    events_seen: list[str]
    map_point_history: RawMapPointHistory
    file_path: str = ""

    @classmethod
    def from_file(cls, file_path: str) -> "CurrentSaveReader":
        acts = []
        logger.info(f"Loading current save file: {file_path}")
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to read current save file {file_path}: {e}")
            raise

        try:
            for act_data in data["acts"]:
                acts.append(ActDetails.from_dict(act_data))
            current_act_index = data["current_act_index"]
            events_seen = data["events_seen"]
            map_point_history = RawMapPointHistory.from_dict(data["map_point_history"])
        except KeyError as e:
            logger.error(f"Missing required current save data key: {e}")
            raise

        return cls(
            acts=acts,
            current_act_index=current_act_index,
            events_seen=events_seen,
            map_point_history=map_point_history,
            file_path=file_path,
        )
