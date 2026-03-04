from __future__ import annotations

from typing import Dict, List

from smart_market_intelligence.strategy_engine.range_detection import _atr


def detect_mss(candles: List[Dict], swings: Dict, sweep_threshold: float = 0.15) -> Dict:
    if len(candles) < 5:
        return {"mss_valid": False, "direction": None, "reason": "insufficient_data"}

    atr = _atr(candles)
    candle = candles[-1]
    body = abs(candle["close"] - candle["open"])
    candle_range = candle["high"] - candle["low"]

    highs = swings.get("swing_highs", [])
    lows = swings.get("swing_lows", [])
    if not highs or not lows:
        return {"mss_valid": False, "direction": None, "reason": "no_swings"}

    last_high = candles[highs[-1]]["high"]
    last_low = candles[lows[-1]]["low"]
    prev = candles[-2]

    bullish_sweep = prev["low"] < (last_low - atr * sweep_threshold)
    bearish_sweep = prev["high"] > (last_high + atr * sweep_threshold)
    bullish_break = candle["close"] > last_high
    bearish_break = candle["close"] < last_low
    impulse_ok = candle_range >= 1.5 * atr if atr else False
    body_ok = (body / candle_range) >= 0.7 if candle_range else False

    bullish_valid = bullish_sweep and bullish_break and impulse_ok and body_ok
    bearish_valid = bearish_sweep and bearish_break and impulse_ok and body_ok

    return {
        "mss_valid": bullish_valid or bearish_valid,
        "direction": "bullish" if bullish_valid else ("bearish" if bearish_valid else None),
        "checks": {
            "sweep": bullish_sweep or bearish_sweep,
            "break_close": bullish_break or bearish_break,
            "candle_gte_1_5_atr": impulse_ok,
            "body_gte_70_percent": body_ok,
        },
    }
