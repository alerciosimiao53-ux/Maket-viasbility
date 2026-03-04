from __future__ import annotations

from typing import Dict, List


def _atr(candles: List[Dict], period: int = 14) -> float:
    if len(candles) < period + 1:
        return 0.0
    tr_values = []
    for i in range(1, len(candles)):
        c = candles[i]
        prev_close = candles[i - 1]["close"]
        tr = max(c["high"] - c["low"], abs(c["high"] - prev_close), abs(c["low"] - prev_close))
        tr_values.append(tr)
    tail = tr_values[-period:]
    return sum(tail) / len(tail)


def _atr_mean(candles: List[Dict], period: int = 14, window: int = 20) -> float:
    if len(candles) < period + window:
        return _atr(candles, period)
    values = []
    for end in range(len(candles) - window, len(candles)):
        slice_c = candles[: end + 1]
        values.append(_atr(slice_c, period))
    return sum(values) / len(values) if values else 0.0


def detect_range(candles: List[Dict], swings: Dict, atr_window: int = 20) -> Dict:
    atr_current = _atr(candles)
    atr_mean20 = _atr_mean(candles, window=atr_window)

    highs = swings.get("swing_highs", [])
    lows = swings.get("swing_lows", [])

    cond_a = False
    if highs and lows and atr_current > 0:
        recent_swing_dist = abs(candles[highs[-1]]["high"] - candles[lows[-1]]["low"])
        cond_a = recent_swing_dist < (1.5 * atr_current)

    cond_b = atr_current < 0.7 * atr_mean20 if atr_mean20 else False
    cond_c = False
    if len(candles) >= 20 and atr_current > 0:
        slope = abs(candles[-1]["close"] - candles[-20]["close"])
        cond_c = slope < (1.2 * atr_current)

    in_range = sum([cond_a, cond_b, cond_c]) >= 2
    return {
        "in_range": in_range,
        "conditions": {"A_swing_distance": cond_a, "B_low_atr": cond_b, "C_no_progression": cond_c},
        "atr_current": atr_current,
        "atr_mean20": atr_mean20,
    }
