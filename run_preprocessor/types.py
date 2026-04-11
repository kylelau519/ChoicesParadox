from typing import Any, TypedDict


class Enchantment(TypedDict):
    id: str
    amount: int


class Card(TypedDict):
    id: str
    floor_added_to_deck: int
    current_upgrade_level: int | None
    enchantment: Enchantment | None


class CardTransform(TypedDict):
    final_card: Card
    original_card: Card


class Relic(TypedDict):
    id: str
    floor_added_to_deck: int


class Potion(TypedDict):
    id: str
    slot_index: int


class Player(TypedDict):
    character: str
    deck: list[Card]
    id: int
    max_potion_slot_count: int
    potions: list[Potion]
    relics: list[Relic]


class Room(TypedDict):
    model_id: str | None
    room_type: str
    turns_taken: int
    monster_ids: list[str] | None


class CardChoice(TypedDict):
    card: Card
    was_picked: bool


class Title(TypedDict):
    key: str
    table: str


class AncientChoice(TypedDict):
    TextKey: str
    title: Title
    was_chosen: bool


class Variable(TypedDict):
    type: str
    decimal_value: int
    bool_value: bool
    string_value: str


class EventChoice(TypedDict):
    title: Title
    variables: dict[str, Variable] | None


class RelicChoice(TypedDict):
    choice: str
    was_picked: bool


class PotionChoice(TypedDict):
    choice: str
    was_picked: bool


class PlayerStats(TypedDict):
    current_gold: int
    current_hp: int
    damage_taken: int
    gold_gained: int
    gold_lost: int
    gold_spent: int
    gold_stolen: int
    hp_healed: int
    max_hp: int
    max_hp_gained: int
    max_hp_lost: int
    player_id: int
    ancient_choice: list[AncientChoice] | None
    event_choices: list[EventChoice] | None
    card_choices: list[CardChoice] | None
    cards_gained: list[Card] | None
    cards_removed: list[Card] | None
    cards_transformed: list[CardTransform] | None
    potion_choices: list[PotionChoice] | None
    potion_used: list[str] | None
    potion_discarded: list[str] | None
    relic_choices: list[RelicChoice] | None
    relics_removed: list[str] | None
    bought_colorless: list[str] | None
    bought_relics: list[str] | None
    bought_potions: list[str] | None
    rest_site_choices: list[str] | None
    upgraded_cards: list[str] | None
    downgraded_cards: list[str] | None


class MapPoint(TypedDict):
    map_point_type: str
    player_stats: list[PlayerStats]
    rooms: list[Room]


class RunHistory(TypedDict):
    acts: list[str]
    ascension: int
    build_id: str
    game_mode: str
    killed_by_encounter: str
    killed_by_event: str
    map_point_history: list[list[MapPoint]]
    modifiers: list[str]
    platform_type: str
    players: list[Player]
    run_time: int
    schema_version: int
    seed: str
    starttime: int
    was_abandoned: bool
    win: bool


class SaveRooms(TypedDict):
    ancient_id: str | None
    boss_encounters_visited: int
    boss_id: str | None
    elite_encounter_ids: list[str]
    elite_encounters_visited: int
    event_ids: list[str]
    events_visited: int
    normal_encounter_ids: list[str]
    normal_encounters_visited: int
    second_boss_id: str | None


class SaveCoord(TypedDict):
    col: int
    row: int


class SaveMapPoint(TypedDict):
    can_modify: bool
    children: list[SaveCoord]
    coord: SaveCoord
    type: str


class SaveMapBoss(TypedDict):
    can_modify: bool
    coord: SaveCoord
    type: str


class SaveMap(TypedDict):
    boss: SaveMapBoss
    height: int
    points: list[SaveMapPoint]


class SaveAct(TypedDict):
    id: str
    rooms: SaveRooms
    saved_map: SaveMap | None


class SaveRelicPropsItem(TypedDict):
    name: str
    value: int | str | bool


class SaveRelicProps(TypedDict):
    ints: list[SaveRelicPropsItem] | None
    strings: list[SaveRelicPropsItem] | None
    bools: list[SaveRelicPropsItem] | None


class SaveRelic(TypedDict):
    id: str
    floor_added_to_deck: int
    props: SaveRelicProps | None


class SaveRelicGrabBag(TypedDict):
    relic_id_lists: dict[str, list[str]]


class SavePlayerOdds(TypedDict):
    card_rarity_odds_value: float
    potion_reward_odds_value: float


class SavePlayerRNG(TypedDict):
    counters: dict[str, int]
    seed: int


class SaveRNG(TypedDict):
    counters: dict[str, int]
    seed: str


class CurrentSaveHistory(TypedDict):
    acts: list[SaveAct]
    ascension: int
    current_act_index: int
    events_seen: list[str]
    extra_fields: dict[str, Any] | None
    game_mode: str
    map_drawings: str
    map_point_history: list[list[MapPoint]]
    modifiers: list[str]
    odds: dict[str, Any] | None
    platform_type: str
    players: list[Player]
    pre_finished_room: dict[str, Any] | None
    rng: SaveRNG
    run_time: int
    save_time: int
    schema_version: int
    shared_relic_grab_bag: SaveRelicGrabBag
    start_time: int
    visited_map_coords: list[SaveCoord]
    win_time: int | None
