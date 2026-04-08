import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class Character(Enum):
    IRONCLAD = "IRONCLAD"
    SILENT = "SILENT"
    DEFECT = "DEFECT"
    REGENT = "REGENT"
    NECROBINDER = "NECROBINDER"


@dataclass
class PlayerSnapshot:
    character: Character
    current_hp: int
    max_hp: int
    current_gold: int
    deck: List[str]
    potions: List[str]
    relics: List[str]


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
    was_victory: bool


class MapPointTracker:
    pass
