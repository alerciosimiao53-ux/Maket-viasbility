from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from smart_market_intelligence.utils.helpers import ensure_dir


def _badge_class(kind: str) -> str:
    return {"good": "good", "warn": "warn", "risk": "risk", "neutral": "neutral"}.get(kind, "neutral")


def _status_from_score(score: float) -> str:
    if score >= 30:
        return "Forte"
    if score <= -30:
        return "Fraca"
    return "Neutra"


def _setup_badge(score: int) -> str:
    if score >= 80:
        return "<span class='score-badge good'>SETUP ELITE</span>"
    if score >= 60:
        return "<span class='score-badge warn'>SETUP VÁLIDO</span>"
    return "<span class='score-badge neutral'>AGUARDAR</span>"


def _risk_level(news_events: List[Dict]) -> str:
    high_count = len([e for e in news_events if e.get("impact") == "high"])
    if high_count >= 3:
        return "High"
    if high_count >= 1:
        return "Medium"
    return "Low"


def _minutes_to_event(ts: str) -> int:
    event_dt = datetime.fromisoformat(ts).astimezone(timezone.utc)
    now = datetime.now(timezone.utc)
    return int((event_dt - now).total_seconds() // 60)


def _render_template(template_str: str, values: Dict[str, str]) -> str:
    html = template_str
    for key, value in values.items():
        html = html.replace(f"{{{{{key}}}}}", value)
    return html


def build_report(report_data: Dict, output_root: str = "reports", report_date: str | None = None) -> Path:
    if report_date is None or report_date == "today":
        report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    report_dir = ensure_dir(Path(output_root) / report_date)
    output_path = report_dir / "report.html"

    template_path = Path("smart_market_intelligence/reporting/html_template.html")
    template_str = template_path.read_text(encoding="utf-8")

    session = report_data["session"]
    regime = report_data["regime"]
    news_risk = report_data["news_risk"]

    header_badges = (
        f"<span class='badge good'>Session: {session}</span>"
        f"<span class='badge {'good' if regime == 'Trend' else 'warn' if regime == 'Range' else 'risk'}'>Regime: {regime}</span>"
        f"<span class='badge {'good' if news_risk == 'Low' else 'warn' if news_risk == 'Medium' else 'risk'}'>News Risk: {news_risk}</span>"
    )

    macro_sorted = sorted(report_data["macro_strength"].items(), key=lambda x: x[1], reverse=True)
    macro_bias_bars = ""
    for ccy, score in macro_sorted:
        width = min(100, int(abs(score)))
        color = "var(--good)" if score >= 0 else "var(--risk)"
        macro_bias_bars += (
            f"<div class='bar-wrap'><div class='bar-label'><span>{ccy}</span><span>{score:.2f}</span></div>"
            f"<div class='bar'><div class='bar-fill' style='width:{width}%; background:{color};'></div></div></div>"
        )

    micro_regime_list = "".join(
        f"<p><b>{pair}</b> · {meta.get('regime', 'n/a').title()} · {meta.get('structure_direction_h4', 'n/a')}</p>"
        for pair, meta in report_data["micro_strength"].items()
    )

    high_events = [e for e in report_data["news_events"] if e.get("impact") == "high"]
    news_risk_list = "".join(
        f"<p><b>{ev['currency']}</b> {ev['event_name']} · T{_minutes_to_event(ev['timestamp_utc']):+d}m</p>" for ev in high_events
    ) or "<p>No high-impact events in queue.</p>"

    watchlist = report_data["watchlist"]
    watchlist_list = "".join(
        f"<p><b>{row['pair']}</b> · {row['direction'].upper()} · score {row['priority_score']}</p>" for row in watchlist[:8]
    )

    macro_rows = "".join(
        f"<tr><td>{ccy}</td><td>{score:.2f}</td><td>{_status_from_score(score)}</td></tr>" for ccy, score in macro_sorted
    )
    macro_table = (
        "<h3>Macro Strength</h3><table><thead><tr><th>Moeda</th><th>Score</th><th>Status</th></tr></thead>"
        f"<tbody>{macro_rows}</tbody></table>"
    )

    pairs_rows = ""
    for row in watchlist:
        pairs_rows += (
            f"<tr><td>{row['pair']}</td><td>{row.get('structure_h4','N/A')}</td><td>{row.get('regime','N/A')}</td>"
            f"<td>{'Yes' if row.get('micro_aligned') else 'No'}</td><td>{row['direction'].upper()}</td></tr>"
        )
    pairs_table = (
        "<h3>Pairs Ranking</h3><table><thead><tr><th>Par</th><th>Estrutura H4</th><th>Regime</th><th>Setup Friendly</th><th>Bias</th></tr></thead>"
        f"<tbody>{pairs_rows}</tbody></table>"
    )

    tech_blocks = ""
    for detail in report_data["technical_details"]:
        setup_badge = _setup_badge(detail["score_final"])
        tech_blocks += f"""
        <details>
          <summary>
            <span>{detail['pair']} · {detail['bias'].upper()}</span>
            <span>{setup_badge}</span>
          </summary>
          <div class='detail-body'>
            <div class='metric'><div class='k'>Contexto W1</div><div class='v'>{detail['context_w1']}</div></div>
            <div class='metric'><div class='k'>Contexto D1</div><div class='v'>{detail['context_d1']}</div></div>
            <div class='metric'><div class='k'>Estrutura H4</div><div class='v'>{detail['structure_h4']}</div></div>
            <div class='metric'><div class='k'>MSS Status</div><div class='v'>{detail['mss_status']}</div></div>
            <div class='metric'><div class='k'>FVG Status</div><div class='v'>{detail['fvg_status']}</div></div>
            <div class='metric'><div class='k'>Premium/Discount</div><div class='v'>{detail['premium_discount']}</div></div>
            <div class='metric'><div class='k'>RR Projetado</div><div class='v'>{detail['rr_projected']}</div></div>
            <div class='metric'><div class='k'>Score Final</div><div class='v'>{detail['score_final']}</div></div>
            <div class='metric'><div class='k'>Chart Placeholder</div><div class='chart-placeholder'>Future chart integration</div></div>
          </div>
        </details>
        """

    html = _render_template(
        template_str,
        {
            "report_date": report_date,
            "header_badges": header_badges,
            "macro_bias_bars": macro_bias_bars,
            "micro_regime_list": micro_regime_list,
            "news_risk_list": news_risk_list,
            "watchlist_list": watchlist_list,
            "macro_table": macro_table,
            "pairs_table": pairs_table,
            "technical_accordion": tech_blocks,
        },
    )

    output_path.write_text(html, encoding="utf-8")
    return output_path


def build_report_payload(
    report_date: str,
    session: str,
    regime: str,
    macro_strength: Dict[str, float],
    micro_meta_by_pair: Dict[str, Dict],
    watchlist: List[Dict],
    news_events: List[Dict],
    technical_details: List[Dict],
) -> Dict:
    return {
        "report_date": report_date,
        "session": session,
        "regime": regime,
        "news_risk": _risk_level(news_events),
        "macro_strength": macro_strength,
        "micro_strength": micro_meta_by_pair,
        "watchlist": watchlist,
        "news_events": news_events,
        "technical_details": technical_details,
    }
