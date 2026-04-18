import unittest

from run_preprocessor.mappoint import RawMapPoint


class TestCompleteness(unittest.TestCase):
    def test_raw_map_point_is_complete(self):
        # Complete case
        complete_mp = RawMapPoint(
            map_point_type="monster",
            player_stats=[{"player_id": 1, "max_hp": 70, "current_hp": 50}],
            rooms=[{"room_type": "monster"}],
        )
        self.assertTrue(complete_mp.is_complete())

        # Incomplete case (max_hp is 0)
        incomplete_mp = RawMapPoint(
            map_point_type="monster",
            player_stats=[{"player_id": 1, "max_hp": 0, "current_hp": 0}],
            rooms=[{"room_type": "monster"}],
        )
        self.assertFalse(incomplete_mp.is_complete())

        # Missing player_stats
        no_stats_mp = RawMapPoint(
            map_point_type="monster", player_stats=[], rooms=[{"room_type": "monster"}]
        )
        self.assertFalse(no_stats_mp.is_complete())


if __name__ == "__main__":
    unittest.main()
