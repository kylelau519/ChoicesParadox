import unittest

from run_preprocessor.reader import RawData
from run_preprocessor.snapshot import PlayerSnapshot


class TestSnapshot(unittest.TestCase):
    def test_init_snapshot(self):
        raw_data = RawData.from_file("testfiles/silent_a0_win.run")
        snapshot = PlayerSnapshot(raw_data)

        self.assertEqual(snapshot.current_hp, 70)
        self.assertEqual(snapshot.current_gold, 99)
        self.assertEqual(snapshot.deck.get("CARD.STRIKE_SILENT"), 5)
        self.assertEqual(snapshot.deck.get("CARD.ZAP"), None)

    def test_simple_walk(self):
        raw_data = RawData.from_file("testfiles/silent_a0_win.run")
        snapshot = PlayerSnapshot(raw_data)

        snapshot.walk_to_floor(floor=5)
        self.assertEqual(snapshot.current_hp, 64)
        self.assertEqual(snapshot.deck.get("CARD.STRIKE_SILENT"), 5)
        self.assertEqual(snapshot.deck.get("CARD.FLECHETTES+"), 1)
        self.assertEqual(snapshot.deck.get("CARD.FLECHETTES"), None)

        snapshot.walk_to_floor(floor=7)
        self.assertEqual(snapshot.deck.get("CARD.STRIKE_SILENT"), 4)

        snapshot.walk_to_floor(floor=44)
        self.assertEqual(snapshot.deck.get("CARD.LEADING_STRIKE"), 1)
        self.assertEqual(snapshot.deck.get("CARD.STRIKE_SILENT+"), 1)

        snapshot.walk_to_floor(floor=48)
        self.assertEqual(snapshot.deck.get("CARD.THINKING_AHEAD+"), 1)
        self.assertEqual(snapshot.deck.get("CARD.PROLONG+"), 1)
        self.assertEqual(len(snapshot.relics), 18)

    def test_walk_to_end(self):
        raw_data = RawData.from_file("testfiles/necrobinder_a7_remove_relics.run")
        snapshot = PlayerSnapshot(raw_data)
        snapshot.walk_to_floor(floor=48)

        end_relics_list = [
            "RELIC.PHYLACTERY_UNBOUND",
            "RELIC.PRECARIOUS_SHEARS",
            "RELIC.REPTILE_TRINKET",
            "RELIC.BIG_HAT",
            "RELIC.FESTIVE_POPPER",
            "RELIC.STRAWBERRY",
            "RELIC.TOUCH_OF_OROBAS",
            "RELIC.VAJRA",
            "RELIC.HAPPY_FLOWER",
            "RELIC.ART_OF_WAR",
            "RELIC.JEWELED_MASK",
            "RELIC.BAG_OF_PREPARATION",
            "RELIC.GREMLIN_HORN",
            "RELIC.GORGET",
            "RELIC.BELLOWS",
        ]
        self.assertEqual(snapshot.relics.sort(), end_relics_list.sort())

        end_potion_list = ["POTION.CLARITY"]
        self.assertEqual(snapshot.potions, end_potion_list)

        self.assertEqual(snapshot.deck.get("CARD.DEFEND_NECROBINDER"), 3)
        self.assertEqual(snapshot.deck.get("CARD.BODYGUARD"), 1)
        self.assertEqual(snapshot.deck.get("CARD.UNLEASH"), 1)
        self.assertEqual(snapshot.deck.get("CARD.ASCENDERS_BANE"), 1)
        self.assertEqual(snapshot.deck.get("CARD.COUNTDOWN"), 1)
        self.assertEqual(snapshot.deck.get("CARD.DEATHS_DOOR"), 1)  # Nimble enchanted
        self.assertEqual(snapshot.deck.get("CARD.ENFEEBLING_TOUCH"), 1)
        self.assertEqual(snapshot.deck.get("CARD.LETHALITY+"), 1)
        self.assertEqual(snapshot.deck.get("CARD.GRAVE_WARDEN"), 2)
        self.assertEqual(snapshot.deck.get("CARD.NEGATIVE_PULSE"), 2)
        self.assertEqual(snapshot.deck.get("CARD.PAGESTORM+"), 2)
        self.assertEqual(snapshot.deck.get("CARD.NO_ESCAPE+"), 1)
        self.assertEqual(snapshot.deck.get("CARD.DIRGE"), 1)
        self.assertEqual(snapshot.deck.get("CARD.FRIENDSHIP"), 1)
        self.assertEqual(snapshot.deck.get("CARD.NEUROSURGE"), 1)
        self.assertEqual(snapshot.deck.get("CARD.BORROWED_TIME+"), 1)
        self.assertEqual(snapshot.deck.get("CARD.DEFY+"), 1)
        self.assertEqual(snapshot.deck.get("CARD.BANSHEES_CRY"), 1)
        self.assertEqual(snapshot.deck.get("CARD.DANSE_MACABRE"), 1)
        self.assertEqual(snapshot.deck.get("CARD.SCOURGE+"), 2)
        self.assertEqual(snapshot.deck.get("CARD.DEMESNE+"), 1)
        self.assertEqual(snapshot.deck.get("CARD.PARSE"), 1)
        self.assertEqual(snapshot.deck.get("CARD.SEANCE"), 2)
        self.assertEqual(snapshot.deck.get("CARD.PRODUCTION+"), 1)

    def test_walk_back(self):
        raw_data = RawData.from_file("testfiles/silent_a0_win.run")
        snapshot = PlayerSnapshot(raw_data)

        snapshot.walk_to_floor(floor=20)
        with self.assertRaises(Exception):
            snapshot.walk_to_floor(floor=5)


if __name__ == "__main__":
    _ = unittest.main()
