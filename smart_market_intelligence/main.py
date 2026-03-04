from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Dict, List

from smart_market_intelligence.data_providers.news_provider import NewsProvider
from smart_market_intelligence.data_providers.price_provider import PriceProvider
from smart_market_intelligence.macro_engine.macro_score import calculate_macro_score
from smart_market_intelligence.market_data.ticker_provider import build_ticker_provider
from smart_market_intelligence.macro_engine.news_filter import evaluate_news_block
from smart_market_intelligence.micro_engine.micro_score import calculate_micro_score
from smart_market_intelligence.reporting.report_builder import build_report, build_report_payload
from smart_market_intelligence.strategy_engine.strategy_logic import compute_setup_score, evaluate_structure
from smart_market_intelligence.utils.helpers import load_config
from smart_market_intelligence.utils.logger import setup_logger
from smart_market_intelligence.watchlist.pair_ranking import active_session, rank_pairs


def _resolve_date(date_arg: str | None) -> str:
    if not date_arg or date_arg == "today":
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return date_arg


def run(report_date: str | None = None) -> str:
    logger = setup_logger()
    config = load_config("smart_market_intelligence/config.yaml")

    pairs: List[str] = config["instruments"]["pairs"]
    watched_currencies = config["instruments"]["currencies"]

    price_provider = PriceProvider(seed=config["runtime"].get("seed", 42))
    news_provider = NewsProvider()

    events = news_provider.get_events()
    ticker_provider = build_ticker_provider()
    ticker_symbols = ticker_provider.get_ticker_symbols()
    ticker_quotes = ticker_provider.fetch_quotes(ticker_symbols)
    macro_strength = calculate_macro_score(events)
    news_state = evaluate_news_block(events, watched_currencies)

    pair_rows: List[Dict] = []
    technical_details: List[Dict] = []
    micro_meta_by_pair: Dict[str, Dict] = {}

    for pair in pairs:
        base = pair[:3]
        quote = pair[3:]

        h4 = price_provider.get_ohlc(pair, timeframe="H4", periods=250)
        d1 = price_provider.get_ohlc(pair, timeframe="D1", periods=120)
        w1 = price_provider.get_ohlc(pair, timeframe="W1", periods=80)

        micro_strength, micro_meta = calculate_micro_score(h4, d1)
        micro_meta_by_pair[pair] = micro_meta

        structure = evaluate_structure(h4, fractal=config["strategy"]["swing_fractal"])

        pair_macro = macro_strength.get(base, 0) - macro_strength.get(quote, 0)
        direction = "buy" if pair_macro + micro_strength >= 0 else "sell"

        macro_aligned = (pair_macro >= 0 and direction == "buy") or (pair_macro < 0 and direction == "sell")
        micro_aligned = micro_meta["setup_friendly"]
        volatility_ok = micro_meta["atr_relative"] >= config["micro"]["min_atr_relative"]
        news_blocked = news_state["block_new_entries"] and (base in watched_currencies or quote in watched_currencies)

        setup_score = compute_setup_score(
            macro_ok=macro_aligned,
            micro_ok=micro_aligned,
            structure=structure,
            session_active=True,
            news_ok=not news_blocked,
        )

        structure_h4 = "Range" if structure["range_state"]["in_range"] else "Trend"

        pair_rows.append(
            {
                "pair": pair,
                "direction": direction,
                "macro_aligned": macro_aligned,
                "micro_aligned": micro_aligned,
                "in_range": structure["range_state"]["in_range"],
                "volatility_ok": volatility_ok,
                "mss_valid": structure["mss_state"].get("mss_valid", False),
                "fvg_valid": structure["fvg_count"] > 0,
                "news_blocked": news_blocked,
                "setup_score": setup_score,
                "structure_h4": structure_h4,
                "regime": micro_meta.get("regime", "range").title(),
            }
        )

        w1_bias = "Bullish" if w1[-1]["close"] > w1[-2]["close"] else "Bearish"
        d1_bias = "Bullish" if d1[-1]["close"] > d1[-2]["close"] else "Bearish"
        technical_details.append(
            {
                "pair": pair,
                "context_w1": w1_bias,
                "context_d1": d1_bias,
                "structure_h4": structure_h4,
                "mss_status": "Validated" if structure["mss_state"].get("mss_valid") else "Not validated",
                "fvg_status": "Valid" if structure["fvg_count"] > 0 else "No valid FVG",
                "premium_discount": structure["pd_state"].get("status", "unknown").title(),
                "rr_projected": "1:2.5" if setup_score >= 60 else "1:1.2",
                "score_final": setup_score,
                "bias": direction,
            }
        )

    watchlist = rank_pairs(pair_rows)
    session = active_session()
    regime = "Trend" if any(x.get("regime") == "Trend" for x in watchlist[:3]) else "Range"

    payload = build_report_payload(
        report_date=_resolve_date(report_date),
        session=session,
        regime=regime,
        macro_strength=macro_strength,
        micro_meta_by_pair=micro_meta_by_pair,
        watchlist=watchlist,
        news_events=events,
        technical_details=technical_details,
        ticker_quotes=ticker_quotes,
        ticker_last_update=datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
    )

    report_path = build_report(payload, output_root="reports", report_date=_resolve_date(report_date))
    logger.info("Relatório gerado em: %s", report_path)
    print("Report generated successfully")
    return str(report_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smart Market Intelligence daily report")
    parser.add_argument("--date", default="today", help="Report date in YYYY-MM-DD or 'today'")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.date)
