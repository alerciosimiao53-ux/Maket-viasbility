from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from smart_market_intelligence.utils.helpers import clamp

EVENT_WEIGHTS = {
    "cpi": 1.8,
    "nfp": 2.0,
    "fomc": 2.0,
    "inflation": 1.5,
    "jobs": 1.4,
    "rates": 1.6,
    "growth": 1.2,
}


def _surprise(event: Dict) -> float:
    actual = event.get("actual")
    forecast = event.get("forecast")
    previous = event.get("previous")

    if actual is None or forecast is None:
        return 0.0

    denom = abs(forecast) if forecast else (abs(previous) if previous else 1.0)
    denom = denom if denom > 1e-9 else 1.0
    return (actual - forecast) / denom


def _event_weight(event: Dict) -> float:
    name = str(event.get("event_name", "")).lower()
    weight = 1.0
    for key, value in EVENT_WEIGHTS.items():
        if key in name:
            weight *= value
    for tag in event.get("tags", []):
        weight *= EVENT_WEIGHTS.get(str(tag).lower(), 1.0)
    if event.get("impact") == "high":
        weight *= 1.5
    elif event.get("impact") == "medium":
        weight *= 1.1
    return weight


def calculate_macro_score(events: List[Dict]) -> Dict[str, float]:
    raw_scores = defaultdict(float)
    for event in events:
        score = _surprise(event) * _event_weight(event) * 40
        raw_scores[event["currency"]] += score

    return {currency: round(clamp(score, -100, 100), 2) for currency, score in raw_scores.items()}
