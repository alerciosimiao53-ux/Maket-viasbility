from __future__ import annotations

from typing import Dict, List

from smart_market_intelligence.strategy_engine.range_detection import _atr


def detect_fvg(candles: List[Dict]) -> List[Dict]:
    fvgs = []
    for i in range(1, len(candles) - 1):
        prev_candle = candles[i - 1]
        next_candle = candles[i + 1]
        curr_atr = _atr(candles[: i + 2])

        bullish_gap = next_candle["low"] - prev_candle["high"]
        bearish_gap = prev_candle["low"] - next_candle["high"]

        if bullish_gap > 0 and bullish_gap >= 0.2 * curr_atr:
            fvgs.append({"index": i, "type": "bullish", "gap": bullish_gap})
        if bearish_gap > 0 and bearish_gap >= 0.2 * curr_atr:
            fvgs.append({"index": i, "type": "bearish", "gap": bearish_gap})

    return fvgs
