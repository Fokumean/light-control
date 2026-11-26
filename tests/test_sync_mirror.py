import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from scripts.collect import GROUPS
from scripts.sync_mirror import validate

class MirrorTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 26, 22, 30, tzinfo=ZoneInfo("Europe/Kyiv"))
        day = str(int(self.now.replace(hour=0, minute=0).timestamp()))
        stamp = (self.now - timedelta(minutes=15)).isoformat()
        self.raw = {"regionId":"kyiv-region", "lastUpdated":stamp,
                    "lastUpdateStatus":{"ok":True,"at":stamp},
                    "fact":{"today":int(day),"update":"26.11.2026 22:05",
                            "data":{day:{g:{str(h):"yes" for h in range(1,25)} for g in GROUPS}}},
                    "preset":{"data":{}}, "attention":None}
    def test_valid_preserves_timestamp(self):
        self.assertEqual(validate(self.raw, self.now)["lastUpdated"], self.raw["lastUpdated"])
    def test_stale(self):
        self.raw["lastUpdated"] = (self.now - timedelta(hours=3)).isoformat()
        with self.assertRaises(ValueError):
            validate(self.raw, self.now)
    def test_error_status(self):
        self.raw["lastUpdateStatus"]["ok"] = False
        with self.assertRaises(ValueError):
            validate(self.raw, self.now)
    def test_wrong_region(self):
        self.raw["regionId"] = "kyiv"
        with self.assertRaises(ValueError):
            validate(self.raw, self.now)
