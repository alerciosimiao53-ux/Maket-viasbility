from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List
from urllib.error import URLError
from urllib.request import urlopen


DEFAULT_SYMBOLS = ["SPX", "NAS100", "US30", "DXY", "XAUUSD", "US10Y"]


@dataclass
class DemoProvider:
    def get_ticker_symbols(self) -> List[str]:
        return DEFAULT_SYMBOLS

    def fetch_quotes(self, symbols: List[str]) -> List[Dict]:
        samples = {
            "SPX": ("S&P 500", 6878.36, 61.73, 0.91),
            "NAS100": ("Nasdaq 100", 24211.15, -52.21, -0.22),
            "US30": ("Dow Jones", 44871.32, 101.06, 0.23),
            "DXY": ("US Dollar Index", 104.12, -0.16, -0.15),
            "XAUUSD": ("Gold Spot", 2349.5, 8.32, 0.36),
            "US10Y": ("US 10Y Yield", 4.18, 0.02, 0.48),
        }
        rows = []
        for sym in symbols:
            name, price, change, pct = samples.get(sym, (sym, None, None, None))
            rows.append(
                {
                    "symbol": sym,
                    "name": name,
                    "price": price,
                    "change": change,
                    "change_pct": pct,
                    "currency": "USD",
                }
            )
        return rows


@dataclass
class FinnhubProvider:
    api_key: str

    def get_ticker_symbols(self) -> List[str]:
        return DEFAULT_SYMBOLS

    def _map_symbol(self, symbol: str) -> str:
        mapping = {
            "SPX": "^GSPC",
            "NAS100": "^NDX",
            "US30": "^DJI",
            "DXY": "DXY",
            "XAUUSD": "OANDA:XAU_USD",
            "US10Y": "US10Y",
        }
        return mapping.get(symbol, symbol)

    def fetch_quotes(self, symbols: List[str]) -> List[Dict]:
        rows = []
        for symbol in symbols:
            mapped = self._map_symbol(symbol)
            try:
                url = f"https://finnhub.io/api/v1/quote?symbol={mapped}&token={self.api_key}"
                with urlopen(url, timeout=6) as response:
                    data = json.loads(response.read().decode("utf-8"))
                current = data.get("c")
                prev_close = data.get("pc")
                change = data.get("d")
                change_pct = data.get("dp")
                if current in (None, 0) and prev_close not in (None, 0):
                    current = prev_close
                rows.append(
                    {
                        "symbol": symbol,
                        "name": symbol,
                        "price": current,
                        "change": change,
                        "change_pct": change_pct,
                        "currency": "USD",
                    }
                )
            except (URLError, TimeoutError, ValueError, json.JSONDecodeError):
                rows.append(
                    {
                        "symbol": symbol,
                        "name": symbol,
                        "price": None,
                        "change": None,
                        "change_pct": None,
                        "currency": "USD",
                    }
                )
        return rows


def build_ticker_provider():
    api_key = os.getenv("FINNHUB_API_KEY", "").strip()
    if api_key:
        return FinnhubProvider(api_key=api_key)
    return DemoProvider()
