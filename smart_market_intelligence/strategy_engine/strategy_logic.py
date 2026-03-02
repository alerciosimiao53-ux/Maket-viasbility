from __future__ import annotations

from typing import Dict, List

from smart_market_intelligence.strategy_engine.fvg_detection import detect_fvg
from smart_market_intelligence.strategy_engine.mss_detection import detect_mss
from smart_market_intelligence.strategy_engine.premium_discount import calculate_pd_zones
from smart_market_intelligence.strategy_engine.range_detection import detect_range
from smart_market_intelligence.strategy_engine.swing_detection import detect_swings


def evaluate_structure(candles_h4: List[Dict], fractal: int = 2) -> Dict:
    swings = detect_swings(candles_h4, fractal=fractal)
    range_state = detect_range(candles_h4, swings)
    mss_state = detect_mss(candles_h4, swings)
    fvgs = detect_fvg(candles_h4)
    pd_state = calculate_pd_zones(candles_h4, swings)
    return {
        "swings": swings,
        "range_state": range_state,
        "mss_state": mss_state,
        "fvg_count": len(fvgs),
        "latest_fvg": fvgs[-1] if fvgs else None,
        "pd_state": pd_state,
        "trade_blocked_by_range": range_state["in_range"],
    }


def compute_setup_score(macro_ok: bool, micro_ok: bool, structure: Dict, session_active: bool, news_ok: bool) -> int:
    score = 0
    score += 20 if macro_ok else 0
    score += 15 if micro_ok else 0
    score += 15 if not structure["range_state"]["in_range"] else 0
    score += 20 if structure["mss_state"].get("mss_valid") else 0
    score += 10 if structure["fvg_count"] > 0 else 0
    score += 10 if session_active else 0
    score += 10 if news_ok else 0
    return max(0, min(100, score))
