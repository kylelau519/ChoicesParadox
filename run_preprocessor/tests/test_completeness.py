import unittest

from run_preprocessor.mappoint import RawMapPoint, RawMapPointHistory


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

    def test_history_stripping(self):
        # Create a mock history with an incomplete point at the end
        complete_data = {
            "map_point_type": "monster",
            "player_stats": [{"player_id": 1, "max_hp": 70, "current_hp": 50}],
            "rooms": [{"room_type": "monster"}],
        }
        incomplete_data = {
            "map_point_type": "monster",
            "player_stats": [{"player_id": 1, "max_hp": 0, "current_hp": 0}],
            "rooms": [{"room_type": "monster"}],
        }

        history_data = [[complete_data, incomplete_data]]
        history = RawMapPointHistory.from_dict(history_data)

        # Should only have the complete one
        flattened = history.flatten()
        self.assertEqual(len(flattened), 1)
        self.assertEqual(flattened[0].player_stats[0]["max_hp"], 70)


if __name__ == "__main__":
    unittest.main()
