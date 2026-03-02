from __future__ import annotations

from typing import Dict, List


def calculate_pd_zones(candles: List[Dict], swings: Dict) -> Dict:
    highs = swings.get("swing_highs", [])
    lows = swings.get("swing_lows", [])
    if not highs or not lows:
        return {"status": "unknown", "midpoint": None, "entry_zone": None}

    swing_high = candles[highs[-1]]["high"]
    swing_low = candles[lows[-1]]["low"]
    high, low = (swing_high, swing_low) if swing_high > swing_low else (swing_low, swing_high)
    midpoint = (high + low) / 2
    price = candles[-1]["close"]
    status = "premium" if price > midpoint else "discount"

    range_size = high - low
    entry_zone = {"lower": low + 0.72 * range_size, "upper": low + 0.81 * range_size}

    return {"status": status, "midpoint": midpoint, "range_high": high, "range_low": low, "entry_zone": entry_zone}
