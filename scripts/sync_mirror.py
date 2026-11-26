"""Validate the public outage-data-ua feed, without contacting DTEK."""
import json
import sys
from datetime import datetime, timezone, timedelta
from scripts.collect import get, parse, OUT

MIRROR = "https://raw.githubusercontent.com/Baskerville42/outage-data-ua/main/data/kyiv-region.json"
MAX_AGE = timedelta(hours=2)

def timestamp(value):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Missing timezone")
    return dt

def validate(raw, now=None):
    now = now or datetime.now(timezone.utc)
    if raw.get("regionId") != "kyiv-region":
        raise ValueError("Incorrect region")
    status = raw["lastUpdateStatus"]
    if status.get("ok") is not True:
        raise ValueError("Upstream reports a collection error")
    checked = timestamp(status["at"])
    updated = timestamp(raw["lastUpdated"])
    for dt in (checked, updated):
        if dt > now + timedelta(minutes=5) or now - dt > MAX_AGE:
            raise ValueError("Upstream data or check is stale")
    # Reuse the existing strict schedule validator, never execute source code.
    parse("DisconSchedule.fact = " + json.dumps(raw["fact"]) +
          "; DisconSchedule.preset = " + json.dumps(raw["preset"]), now)
    notice = raw.get("attention")
    if notice is not None and (not isinstance(notice, dict) or not isinstance(notice.get("text"), str)):
        raise ValueError("Invalid notice")
    # Preserve source timestamps; downloading an old file cannot make it fresh.
    return {**raw, "source": MIRROR,
            "sourceProject": "https://github.com/Baskerville42/outage-data-ua",
            "sourceProvider": "https://www.dtek-krem.com.ua/ua/shutdowns"}

def main():
    data = validate(json.loads(get(MIRROR)))
    if OUT.exists():
        previous = json.loads(OUT.read_text(encoding="utf-8"))
        if previous.get("lastUpdated") and timestamp(previous["lastUpdated"]) > timestamp(data["lastUpdated"]):
            raise ValueError("Refusing an older version")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    tmp.replace(OUT)
    print("Validated mirror schedule:", data["fact"]["update"])

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Mirror sync stopped; previous data preserved:", error, file=sys.stderr)
        sys.exit(1)
