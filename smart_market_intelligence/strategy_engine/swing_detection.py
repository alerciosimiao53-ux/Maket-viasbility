from __future__ import annotations

from typing import Dict, List


def detect_swings(candles: List[Dict], fractal: int = 2) -> Dict[str, List[int]]:
    highs, lows = [], []
    for i in range(fractal, len(candles) - fractal):
        high = candles[i]["high"]
        low = candles[i]["low"]

        left_high = max(c["high"] for c in candles[i - fractal : i])
        right_high = max(c["high"] for c in candles[i + 1 : i + fractal + 1])
        left_low = min(c["low"] for c in candles[i - fractal : i])
        right_low = min(c["low"] for c in candles[i + 1 : i + fractal + 1])

        if high > left_high and high > right_high:
            highs.append(i)
        if low < left_low and low < right_low:
            lows.append(i)

    return {"swing_highs": highs, "swing_lows": lows}
