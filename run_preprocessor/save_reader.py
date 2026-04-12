import json
import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Callable, cast

from run_preprocessor.types import CurrentSaveHistory, SaveAct, SaveMap

from .mappoint import RawMapPointHistory

logger = logging.getLogger(__name__)

from typing import Any


@dataclass
class ActDetails:
    id: str
    ancient_id: str | None
    boss_id: str | None
    elite_encounter_ids: list[str]
    elite_encounters_visited: int
    event_ids: list[str]
    events_visited: int
    normal_encounter_ids: list[str]
    normal_encounters_visited: int
    saved_map: SaveMap | None  # Later can make map object to parse the field
    second_boss_id: str | None

    @classmethod
    def from_dict(cls, data: SaveAct) -> "ActDetails":
        rooms = data["rooms"]
        try:
            return cls(
                id=data["id"],
                ancient_id=rooms["ancient_id"],
                boss_id=rooms.get("boss_id", ""),
                second_boss_id=rooms.get("second_boss_id"),
                elite_encounter_ids=rooms["elite_encounter_ids"],
                elite_encounters_visited=rooms["elite_encounters_visited"],
                event_ids=rooms["event_ids"],
                events_visited=rooms["events_visited"],
                normal_encounter_ids=rooms["normal_encounter_ids"],
                normal_encounters_visited=rooms["normal_encounters_visited"],
                saved_map=data.get("saved_map"),
            )
        except KeyError as e:
            logger.error(f"Missing required act details key: {e}")
            raise

    def next_normal_encounter(self) -> str:
        return self.normal_encounter_ids[self.normal_encounters_visited]

    def get_normals(self) -> list[str]:
        return list(set(self.normal_encounter_ids))

    def remaining_normal_encounters(self) -> list[str]:
        return self.normal_encounter_ids[self.normal_encounters_visited :]

    def next_elite(self) -> str:
        return self.elite_encounter_ids[self.elite_encounters_visited]

    def get_elites(self) -> list[str]:
        return list(set(self.elite_encounter_ids))

    def boss(self) -> str | None:
        return self.boss_id

    def second_boss(self) -> str | None:
        return self.second_boss_id


from .player import RawPlayer


@dataclass
class SaveMetadata:
    ascension: int
    game_mode: str
    map_drawings: str
    seed: str

    @classmethod
    def from_dict(cls, data: CurrentSaveHistory) -> "SaveMetadata":
        try:
            return cls(
                ascension=data["ascension"],
                game_mode=data["game_mode"],
                map_drawings=data["map_drawings"],
                seed=data["rng"]["seed"],
            )
        except KeyError as e:
            logger.error(f"Missing required save metadata key: {e}")
            raise


@dataclass
class CurrentSaveReader:
    acts: list[ActDetails]
    current_act_index: int
    events_seen: list[str]
    map_point_history: RawMapPointHistory
    run_metadata: SaveMetadata
    players: list[RawPlayer]
    file_path: str

    @classmethod
    def from_file(cls, file_path: str) -> "CurrentSaveReader":
        logger.info(f"Loading current save file: {file_path}")
        try:
            with open(file_path, "r") as f:
                data = cast(CurrentSaveHistory, json.load(f))
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to read current save file {file_path}: {e}")
            raise

        acts = []
        try:
            for act_data in data["acts"]:
                acts.append(ActDetails.from_dict(act_data))
            current_act_index = data["current_act_index"]
            events_seen = data["events_seen"]
            run_metadata = SaveMetadata.from_dict(data)
            players = []
            for player in data["players"]:
                players.append(
                    {
                        "character": player["character_id"],
                        "deck": player["deck"],
                        "id": player["net_id"],
                        "max_potion_slot_count": player["max_potion_slot_count"],
                        "potions": player["potions"],
                        "relics": player["relics"],
                    }
                )
            map_point_history = RawMapPointHistory.from_dict(data["map_point_history"])
        except KeyError as e:
            logger.error(f"Missing required current save data key: {e}")
            raise

        return cls(
            acts=acts,
            current_act_index=current_act_index,
            events_seen=events_seen,
            map_point_history=map_point_history,
            run_metadata=run_metadata,
            players=players,
            file_path=file_path,
        )


class SaveFileListener:
    def __init__(
        self,
        file_path: str,
        callback: Callable[[CurrentSaveReader], None],
        interval: float = 1.0,
    ):
        self.file_path = file_path
        self.callback = callback
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._last_mtime = 0

    def start(self):
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()

    def _run(self):
        file_seen = False
        while not self._stop_event.is_set():
            try:
                if os.path.exists(self.file_path):
                    file_seen = True
                    current_mtime = os.path.getmtime(self.file_path)
                    if current_mtime > self._last_mtime:
                        self._last_mtime = current_mtime
                        reader = CurrentSaveReader.from_file(self.file_path)
                        self.callback(reader)
                elif file_seen:
                    logger.info("Save file deleted, stopping listener.")
                    self._stop_event.set()
                    break
            except Exception as e:
                logger.error(f"Error in SaveFileListener: {e}")
            time.sleep(self.interval)
