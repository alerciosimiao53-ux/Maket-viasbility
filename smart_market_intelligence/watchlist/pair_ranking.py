from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List


def active_session() -> str:
    hour = datetime.now(timezone.utc).hour
    if 7 <= hour < 12:
        return "London"
    if 12 <= hour < 21:
        return "New York"
    return "Asia"


def rank_pairs(pairs_data: List[Dict]) -> List[Dict]:
    session = active_session()
    ranked = []
    for item in pairs_data:
        score = 0
        score += 20 if item["macro_aligned"] else 0
        score += 15 if item["micro_aligned"] else 0
        score += 15 if not item["in_range"] else 0
        score += 10 if item["volatility_ok"] else 0
        score += 20 if item["mss_valid"] else 0
        score += 10 if item["fvg_valid"] else 0
        score += 10 if not item["news_blocked"] else 0

        ranked.append({**item, "session": session, "priority_score": score})

    return sorted(ranked, key=lambda x: x["priority_score"], reverse=True)
