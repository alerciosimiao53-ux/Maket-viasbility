from __future__ import annotations

from typing import Dict, List, Tuple

from smart_market_intelligence.micro_engine.regime_detection import detect_regime
from smart_market_intelligence.utils.helpers import clamp


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


def calculate_micro_score(h4: List[Dict], d1: List[Dict]) -> Tuple[float, Dict]:
    if len(h4) < 21 or len(d1) < 2:
        return 0.0, {"setup_friendly": False, "regime": "range", "structure_direction_h4": "neutral", "atr_relative": 0.0}

    ret_1d = (d1[-1]["close"] - d1[-2]["close"]) / d1[-2]["close"] if d1[-2]["close"] else 0.0
    ret_4h = (h4[-1]["close"] - h4[-2]["close"]) / h4[-2]["close"] if h4[-2]["close"] else 0.0

    atr = _atr(h4)
    atr_rel = atr / h4[-1]["close"] if h4[-1]["close"] else 0.0

    regime_info = detect_regime(h4)
    ma20 = sum(c["close"] for c in h4[-20:]) / 20
    structure_dir = "bullish" if h4[-1]["close"] > ma20 else "bearish"

    score = (ret_1d * 2000) + (ret_4h * 1500) + (atr_rel * 600) + (15 if regime_info["regime"] == "trend" else -10)
    micro_strength = round(clamp(score, -100, 100), 2)
    setup_friendly = regime_info["regime"] == "trend" and abs(ret_4h) > 0.001

    return micro_strength, {
        "ret_1d": ret_1d,
        "ret_4h": ret_4h,
        "atr_relative": atr_rel,
        "regime": regime_info["regime"],
        "structure_direction_h4": structure_dir,
        "setup_friendly": setup_friendly,
    }
