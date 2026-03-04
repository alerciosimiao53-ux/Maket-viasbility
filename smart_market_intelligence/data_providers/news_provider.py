from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, List

from smart_market_intelligence.utils.helpers import utc_now


@dataclass
class NewsProvider:
    """Mock provider returning structured economic calendar events."""

    def get_events(self) -> List[Dict]:
        now = utc_now()
        return [
            {
                "timestamp_utc": (now + timedelta(minutes=20)).isoformat(),
                "currency": "USD",
                "impact": "high",
                "event_name": "US CPI YoY",
                "actual": None,
                "forecast": 3.1,
                "previous": 3.3,
                "tags": ["inflation"],
            },
            {
                "timestamp_utc": (now + timedelta(hours=3)).isoformat(),
                "currency": "EUR",
                "impact": "medium",
                "event_name": "ECB Speech",
                "actual": None,
                "forecast": None,
                "previous": None,
                "tags": ["rates"],
            },
            {
                "timestamp_utc": (now - timedelta(minutes=5)).isoformat(),
                "currency": "GBP",
                "impact": "high",
                "event_name": "UK Jobs Data",
                "actual": 1.8,
                "forecast": 1.5,
                "previous": 1.2,
                "tags": ["jobs"],
            },
        ]
