from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List


def _parse_utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts).astimezone(timezone.utc)


def evaluate_news_block(events: List[Dict], watch_currencies: List[str], before_min: int = 30, after_min: int = 10) -> Dict:
    now = datetime.now(timezone.utc)
    relevant = [e for e in events if e.get("currency") in watch_currencies and e.get("impact") == "high"]

    block_new_entries = False
    recent_event_cooldown = False
    active_events: List[Dict] = []

    for event in relevant:
        event_time = _parse_utc(event["timestamp_utc"])
        delta_min = (event_time - now).total_seconds() / 60
        if 0 <= delta_min <= before_min:
            block_new_entries = True
            active_events.append(event)
        if -after_min <= delta_min < 0:
            recent_event_cooldown = True
            active_events.append(event)

    return {
        "block_new_entries": block_new_entries or recent_event_cooldown,
        "recent_event_cooldown": recent_event_cooldown,
        "active_events": active_events,
        "message": "News lock active" if active_events else "No high-impact lock",
    }
