"""Read public DTEK schedules without authentication or bypassing access controls."""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.robotparser import RobotFileParser
from zoneinfo import ZoneInfo
from html.parser import HTMLParser

URL = "https://www.dtek-krem.com.ua/ua/shutdowns"
ROBOTS = "https://www.dtek-krem.com.ua/robots.txt"
AGENT = "LightControl/0.1"
OUT = Path("data/kyiv-region.json")
GROUPS = {f"GPV{i}.{j}" for i in range(1, 7) for j in (1, 2)}
HOURS = {str(i) for i in range(1, 25)}

def get(url):
    with urlopen(Request(url, headers={"User-Agent": AGENT}), timeout=30) as response:
        if response.geturl() != url:
            raise ValueError("Unexpected redirect")
        raw = response.read(8_000_001)
        if len(raw) > 8_000_000:
            raise ValueError("Response too large")
        return raw.decode("utf-8-sig")

def check_robots():
    try:
        rules = get(ROBOTS)
    except HTTPError as e:
        if e.code == 404:
            return
        raise
    if "<html" in rules.lower() or not rules.strip():
        raise ValueError("Cannot verify robots.txt")
    parser = RobotFileParser()
    parser.parse(rules.splitlines())
    if not parser.can_fetch(AGENT, URL):
        raise PermissionError("robots.txt disallows collection")
    delay = parser.crawl_delay(AGENT)
    rate = parser.request_rate(AGENT)
    if (delay and delay > 900) or (rate and rate.seconds / rate.requests > 900):
        raise PermissionError("Site crawl rules require a longer interval")

def extract(html, key):
    match = re.search(r"\bDisconSchedule\." + re.escape(key) + r"\s*=\s*", html)
    if not match:
        raise ValueError(f"Missing {key} in public page")
    value, _ = json.JSONDecoder().raw_decode(html[match.end():])
    if not isinstance(value, dict):
        raise ValueError(f"Invalid {key}")
    return value

class Attention(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag == "div":
            if self.depth:
                self.depth += 1
            elif "m-attention__text" in dict(attrs).get("class", "").split():
                self.depth = 1
    def handle_endtag(self, tag):
        if tag == "div" and self.depth:
            self.depth -= 1
    def handle_data(self, data):
        if self.depth and data.strip():
            self.parts.append(data.strip())

def parse(html, now=None):
    now = now or datetime.now(timezone.utc)
    fact = extract(html, "fact")
    preset = extract(html, "preset")
    today = str(fact["today"])
    if not today.isdigit() or len(today) != 10:
        raise ValueError("Unexpected day format")
    current_date = now.astimezone(ZoneInfo("Europe/Kyiv")).date()
    if datetime.fromtimestamp(int(today), ZoneInfo("Europe/Kyiv")).date() != current_date:
        raise ValueError("Source schedule does not cover today's date")
    data = fact["data"]
    if today not in data:
        raise ValueError("Missing today's schedule")
    for day, groups in data.items():
        if not str(day).isdigit() or not isinstance(groups, dict):
            raise ValueError("Unexpected schedule structure")
        if not GROUPS.issubset(groups):
            raise ValueError("Missing groups")
        for group in GROUPS:
            hours = groups[group]
            if not isinstance(hours, dict) or set(hours) != HOURS:
                raise ValueError("Incomplete hourly schedule")
            if not set(hours.values()).issubset({"yes", "no", "first", "second", "maybe", "unknown"}):
                raise ValueError("Unrecognized schedule state")
    update = datetime.strptime(fact["update"], "%d.%m.%Y %H:%M").replace(tzinfo=ZoneInfo("Europe/Kyiv"))
    if (update - now).total_seconds() > 300:
        raise ValueError("Source timestamp is in the future")
    if not isinstance(preset.get("data"), dict):
        raise ValueError("Missing weekly template")
    notice = Attention()
    notice.feed(html)
    return {"regionId":"kyiv-region", "source":URL,
            "lastUpdated":now.isoformat(), "fact":fact, "preset":preset,
            "attention":{"text":"\n".join(notice.parts)} if notice.parts else None,
            "lastUpdateStatus":{"ok":True,"at":now.isoformat()}}

def main():
    check_robots()
    payload = parse(get(URL))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    tmp.replace(OUT)
    print("Validated public schedule:", payload["fact"]["update"])

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Collection stopped; previous data preserved:", error, file=sys.stderr)
        sys.exit(1)
