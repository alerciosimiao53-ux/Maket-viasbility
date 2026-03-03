from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from random import Random
from typing import Dict, List


@dataclass
class PriceProvider:
    seed: int = 42

    def get_ohlc(self, symbol: str, timeframe: str = "H1", periods: int = 300) -> List[Dict]:
        rng = Random(hash((symbol, timeframe, self.seed)) & 0xFFFFFFFF)
        candles: List[Dict] = []
        price = 100.0 + rng.uniform(-2, 2)
        step = self._to_timedelta(timeframe)
        ts = datetime.now(timezone.utc) - step * periods

        for _ in range(periods):
            open_ = price
            drift = rng.uniform(-1.2, 1.2)
            close = open_ + drift
            wick = abs(rng.uniform(0.15, 0.85))
            high = max(open_, close) + wick
            low = min(open_, close) - wick
            candles.append({"timestamp": ts.isoformat(), "open": open_, "high": high, "low": low, "close": close})
            price = close
            ts += step
        return candles

    def batch_get(self, symbols: List[str], timeframe: str = "H1", periods: int = 300) -> Dict[str, List[Dict]]:
        return {symbol: self.get_ohlc(symbol, timeframe, periods) for symbol in symbols}

    @staticmethod
    def _to_timedelta(timeframe: str) -> timedelta:
        mapping = {"M15": timedelta(minutes=15), "H1": timedelta(hours=1), "H4": timedelta(hours=4), "D1": timedelta(days=1), "W1": timedelta(weeks=1)}
        return mapping.get(timeframe, timedelta(hours=1))
