import json
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from scripts.collect import parse, GROUPS

class CollectorTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 26, 22, 30, tzinfo=ZoneInfo("Europe/Kyiv"))
        self.day = str(int(self.now.replace(hour=0, minute=0).timestamp()))
        self.fact = {"today": int(self.day), "update": "26.11.2026 22:05",
                     "data": {self.day: {g: {str(h): "yes" for h in range(1, 25)} for g in GROUPS}}}
    def html(self):
        return ('<div class="m-attention__text"><p>Test notice</p></div>'
                + 'DisconSchedule.fact = ' + json.dumps(self.fact) + ';'
                + 'DisconSchedule.preset = {"data":{}};')
    def test_valid(self):
        self.fact["data"][self.day]["GPV5.2"]["9"] = "no"
        result = parse(self.html(), self.now)
        self.assertEqual(result["fact"]["data"][self.day]["GPV5.2"]["9"], "no")
        self.assertEqual(result["attention"]["text"], "Test notice")
    def test_missing_hour(self):
        del self.fact["data"][self.day]["GPV5.2"]["9"]
        with self.assertRaises(ValueError):
            parse(self.html(), self.now)
    def test_stale_day(self):
        with self.assertRaises(ValueError):
            parse(self.html(), self.now.replace(day=27))
    def test_invalid_html(self):
        with self.assertRaises(ValueError):
            parse("<html>Access denied</html>", self.now)
    def test_unknown_status(self):
        self.fact["data"][self.day]["GPV5.2"]["9"] = "bad"
        with self.assertRaises(ValueError):
            parse(self.html(), self.now)

if __name__ == "__main__":
    unittest.main()
