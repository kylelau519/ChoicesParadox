# Input format for bdt onehot:
# current HP, max hp, [deck count vectorize], [potion count vectorize], [relic onehot], [encounter onehot],
# Target: damage taken in the encounter


# Convert each encounter in a run file to a trainable point

from run_preprocessor.reader import RawData
from run_preprocessor.snapshot import PlayerSnapshot


class RunToInputConverter:
    def __init__(self, run_json, player_id: int = 1):
        self.raw_data = RawData.from_json(run_json)
        self.snapshot_now = PlayerSnapshot(self.raw_data, player_id)
        self.snapshot_next = PlayerSnapshot(self.raw_data, player_id)
        self.snapshot_next.walk()

    # This assumed snapshot_next is at an encounter, with the damage taken applied
    def convert_snapshot(self):
        input = {}
        # Player current stat
        input["current_hp"] = self.snapshot_now.current_hp
        input["max_hp"] = self.snapshot_now.max_hp
        input.update(self.snapshot_now.deck.cards)
        input.update(self.snapshot_now.potions)
        input.update(self.snapshot_now.relics)

        # Ecnounter and the damage taken in the next encounter
        map_point = self.raw_data.map_point_history.flatten()[self.snapshot_next.current_lumpsum_floor - 1]
        rooms = map_point.rooms
        encounters = {}
        for room in rooms:
            model_id = room.get("model_id", "")
            if model_id and model_id.startswith("ENCOUNTER"):
                encounters[model_id] = 1

        input.update(encounters)
        player_stat = map_point.get_player_stat (self.snapshot_next.player_id)
        target = {}
        damage_taken = player_stat.get("damage_taken", 0)
        target["damage_taken"] = damage_taken
        return input, target

    def walk(self):
        self.snapshot_now.walk()
        self.snapshot_next.walk()

    def run(self):
        print(len(self.raw_data.map_point_history.flatten()), "floors in total")
        while self.snapshot_next.current_lumpsum_floor < len(self.raw_data.map_point_history.flatten()):
            print("next_F: ", self.snapshot_next.current_lumpsum_floor)
            if self.snapshot_next.is_encounter():
                input, target = self.convert_snapshot()
                print("Encounter at floor", self.snapshot_next.current_lumpsum_floor)
                print("Encounter is ", [k for k in input.keys() if k.startswith("ENCOUNTER")])
                print("Damge taken:", target["damage_taken"])
                print("")
            self.walk()


if __name__ == "__main__":
    import json

    with open("testfiles/ironclad_a5_lose.run", "r") as f:
        run_json = json.load(f)
    converter = RunToInputConverter(run_json)
    converter.run()
