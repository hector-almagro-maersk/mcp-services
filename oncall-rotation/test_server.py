import unittest
import os
import json
from datetime import datetime
from server import (
    get_rotation_config, _engineer_for_date, _parse_date, mcp
)


class TestRotationConfig(unittest.TestCase):

    def setUp(self):
        os.environ.pop("MCP_ROTATION_CONFIG", None)

    def test_get_oncall_ad_hoc_override_new_format_single(self):
        from server import get_oncall
        result = json.loads(get_oncall("2025-09-19", overrides="Zed:2025-09-18"))
        self.assertEqual(result["engineer"], "Zed")
        self.assertEqual(result["source"], "override")

    def test_get_oncall_ad_hoc_override_new_format_multiple(self):
        from server import get_oncall
        # Later override should apply for later date, earlier for earlier date
        multi = "Zed:2025-09-18,Quinn:2025-09-25"
        r1 = json.loads(get_oncall("2025-09-19", overrides=multi))
        self.assertEqual(r1["engineer"], "Zed")
        r2 = json.loads(get_oncall("2025-09-26", overrides=multi))
        self.assertEqual(r2["engineer"], "Quinn")

    def test_invalid_override_format(self):
        from server import get_oncall
        bad = json.loads(get_oncall("2025-09-05", overrides="NoDatePair"))
        self.assertIn("error", bad)

    def test_invalid_override_bad_date(self):
        from server import get_oncall
        bad_date = json.loads(get_oncall("2025-09-05", overrides="Alice:2025-99-99"))
        self.assertIn("error", bad_date)
        # Temporarily rename config.json if present to simulate absence
        service_dir = os.path.dirname(__file__)
        cfg_path = os.path.join(service_dir, 'config.json')
        temp_path = None
        if os.path.exists(cfg_path):
            temp_path = cfg_path + '.bak_test'
            os.rename(cfg_path, temp_path)
        try:
            with self.assertRaises(Exception):
                get_rotation_config()
        finally:
            if temp_path and os.path.exists(temp_path):
                os.rename(temp_path, cfg_path)


class TestRotationLogic(unittest.TestCase):

    def setUp(self):
        self.cfg = {
            "engineers": ["Alice", "Bob", "Carol"],
            "start_date": "2025-08-25",
            "rotation_days": 7
        }

    def test_baseline_same_week(self):
        r = _engineer_for_date(self.cfg, "2025-08-25", None)
        self.assertEqual(r["engineer_index"], 0)  # Alice

    def test_second_slot(self):
        r = _engineer_for_date(self.cfg, "2025-09-02", None)  # 8 days later -> slot 1
        self.assertEqual(r["slot_index"], 1)
        self.assertEqual(r["engineer_index"], 1)  # Bob

    def test_wraparound(self):
        # After 21 days -> slot 3 -> engineer index 0 again
        r = _engineer_for_date(self.cfg, "2025-09-15", None)
        self.assertEqual(r["engineer_index"], 0)

    def test_before_start(self):
        # 3 days before start should still compute deterministically
        r = _engineer_for_date(self.cfg, "2025-08-22", None)
        self.assertIn(r["engineer_index"], [0,1,2])  # Just ensure no crash


class TestGetOncallPublic(unittest.TestCase):

    def setUp(self):
        os.environ["MCP_ROTATION_CONFIG"] = json.dumps({
            "engineers": ["Alice", "Bob", "Carol"],
            "start_date": "2025-08-25",
            "rotation_days": 7,
            "overrides": [
                {"date": "2025-09-10", "engineer": "Eve"}
            ]
        })

    def tearDown(self):
        os.environ.pop("MCP_ROTATION_CONFIG", None)

    def test_get_oncall_schedule(self):
        from server import get_oncall
        result = json.loads(get_oncall("2025-08-28"))
        self.assertEqual(result["engineer"], "Alice")
        self.assertEqual(result["source"], "schedule")

    def test_get_oncall_override(self):
        from server import get_oncall
        # Date within override effective week (before next slot boundary)
        result = json.loads(get_oncall("2025-09-12"))
        self.assertEqual(result["engineer"], "Eve")
        self.assertEqual(result["source"], "override")




if __name__ == "__main__":
    unittest.main()
