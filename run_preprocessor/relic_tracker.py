import logging

from .mappoint import RawMapPointHistory

logger = logging.getLogger(__name__)


class RelicTracker:
    def __init__(
        self, data: RawMapPointHistory, starting_relics: list[str] | None = None
    ):
        self.data: RawMapPointHistory = data
        self.starting_relics: list[str] = starting_relics or []
        self.relic_history: set[str] = set()

    # not working yet
    def track_act_floor(self, act: int, floor: int, player_id: int = 1) -> list[str]:
        # first check if rawMapPointHistory has that floor
        self.relic_history = set(self.starting_relics)

        if act >= len(self.data.map_point_history):
            logger.warning(
                f"Requested act {act} is greater than or equal to total acts {len(self.data.map_point_history)}."
            )
            return sorted(list(self.relic_history))

        # iterate over the history:
        for a in range(act + 1):
            nodes = self.data.map_point_history[a]
            limit = floor + 1 if a == act else len(nodes)

            for f in range(min(limit, len(nodes))):
                map_point = nodes[f]
                # get player_stats, get the correct stat with player_id.
                for stats in map_point.player_stats:
                    if stats.get("player_id") == player_id:
                        # check if keyword relic_choices is there, if so check if was_picked is true, if so add to relic_history
                        relic_choices = stats.get("relic_choices") or []
                        for choice in relic_choices:
                            if choice.get("was_picked"):
                                self.relic_history.add(choice["choice"])

                        # check if keyword bought_relics is there, if so add all relics in that list to relic_history
                        bought_relics = stats.get("bought_relics") or []
                        for relic in bought_relics:
                            self.relic_history.add(relic)

                        # check if keyword relics_removed is there, if so remove that relic from relic_history
                        relics_removed = stats.get("relics_removed") or []
                        for relic in relics_removed:
                            self.relic_history.discard(relic)

        return sorted(list(self.relic_history))
