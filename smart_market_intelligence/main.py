from __future__ import annotations

from typing import Dict, List

from smart_market_intelligence.data_providers.news_provider import NewsProvider
from smart_market_intelligence.data_providers.price_provider import PriceProvider
from smart_market_intelligence.macro_engine.macro_score import calculate_macro_score
from smart_market_intelligence.macro_engine.news_filter import evaluate_news_block
from smart_market_intelligence.micro_engine.micro_score import calculate_micro_score
from smart_market_intelligence.reporting.report_builder import build_report, make_technical_block
from smart_market_intelligence.strategy_engine.strategy_logic import compute_setup_score, evaluate_structure
from smart_market_intelligence.utils.helpers import load_config
from smart_market_intelligence.utils.logger import setup_logger
from smart_market_intelligence.watchlist.pair_ranking import rank_pairs


def run() -> str:
    logger = setup_logger()
    config = load_config("smart_market_intelligence/config.yaml")

    pairs: List[str] = config["instruments"]["pairs"]
    watched_currencies = config["instruments"]["currencies"]

    price_provider = PriceProvider(seed=config["runtime"].get("seed", 42))
    news_provider = NewsProvider()

    events = news_provider.get_events()
    macro_strength = calculate_macro_score(events)
    news_state = evaluate_news_block(events, watched_currencies)

    pair_rows: List[Dict] = []
    technical_rows: List[Dict] = []
    micro_ranking: List[tuple] = []

    for pair in pairs:
        base = pair[:3]
        quote = pair[3:]

        h4 = price_provider.get_ohlc(pair, timeframe="H4", periods=250)
        d1 = price_provider.get_ohlc(pair, timeframe="D1", periods=120)

        micro_strength, micro_meta = calculate_micro_score(h4, d1)
        micro_ranking.append((pair, micro_strength))

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
            }
        )

        technical_rows.append(make_technical_block(pair, structure, setup_score, direction))

    watchlist = rank_pairs(pair_rows)

    report_data = {
        "executive": {
            "environment": "Tendência seletiva com filtros de risco por notícia e range.",
            "macro_ranking": sorted(macro_strength.items(), key=lambda x: x[1], reverse=True),
            "micro_ranking": sorted(micro_ranking, key=lambda x: x[1], reverse=True),
            "watchlist": watchlist,
            "news_state": news_state["message"],
        },
        "technical": technical_rows,
    }

    report_path = build_report(report_data)
    logger.info("Relatório gerado em: %s", report_path)
    return str(report_path)


if __name__ == "__main__":
    run()
