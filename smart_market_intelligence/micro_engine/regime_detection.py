from __future__ import annotations

from typing import Dict, List


def detect_regime(candles: List[Dict], lookback: int = 20) -> Dict:
    closes = [c["close"] for c in candles]
    if len(closes) < lookback + 1:
        return {"regime": "range", "trend_strength": 0.0, "realized_vol": 0.0}

    returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes)) if closes[i - 1] != 0]
    recent = returns[-lookback:]
    mean = sum(recent) / len(recent)
    variance = sum((x - mean) ** 2 for x in recent) / len(recent)
    realized_vol = variance**0.5
    trend_strength = abs(closes[-1] - closes[-lookback]) / abs(closes[-lookback]) if closes[-lookback] else 0.0

    regime = "trend" if trend_strength > 0.01 and realized_vol > 0.003 else "range"
    return {"regime": regime, "trend_strength": trend_strength, "realized_vol": realized_vol}
