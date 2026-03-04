from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from smart_market_intelligence.utils.helpers import ensure_dir


def _safe(value, fallback: str = "—") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _render_template(template_str: str, values: Dict[str, str]) -> str:
    html = template_str
    for key, value in values.items():
        html = html.replace(f"{{{{{key}}}}}", value)
    return html


def _setup_badge(score: int) -> str:
    if score >= 80:
        return "<span class='badge good'>SETUP ELITE</span>"
    if score >= 60:
        return "<span class='badge warn'>SETUP VÁLIDO</span>"
    return "<span class='badge neutral'>AGUARDAR</span>"


def _risk_level(news_events: List[Dict]) -> str:
    high_count = len([e for e in news_events if e.get("impact") == "high"])
    if high_count >= 3:
        return "High"
    if high_count >= 1:
        return "Medium"
    return "Low"


def _impact_badge(impact: str) -> str:
    imp = (impact or "").lower()
    klass = "risk" if imp == "high" else "warn" if imp == "medium" else "neutral"
    return f"<span class='badge {klass}'>{_safe(impact).upper()}</span>"


def _status_from_score(score: float) -> str:
    if score >= 30:
        return "Forte"
    if score <= -30:
        return "Fraca"
    return "Neutra"


def _ticker_item_html(row: Dict) -> str:
    pct = row.get("change_pct")
    change = row.get("change")
    if pct is None:
        color = "#9ca3af"
        pct_txt = "—"
    elif float(pct) > 0:
        color = "#22c55e"
        pct_txt = f"+{float(pct):.2f}%"
    elif float(pct) < 0:
        color = "#ef4444"
        pct_txt = f"{float(pct):.2f}%"
    else:
        color = "#9ca3af"
        pct_txt = "0.00%"

    change_txt = "—" if change is None else (f"+{float(change):.2f}" if float(change) > 0 else f"{float(change):.2f}")
    price_txt = "—" if row.get("price") is None else f"{float(row['price']):,.2f}"
    return (
        f"<span class='ticker-item'><b>{_safe(row.get('name'))}/{_safe(row.get('symbol'))}</b>"
        f"<span>{price_txt}</span><span style='color:{color}'>{change_txt} ({pct_txt})</span></span>"
    )


def build_report(report_data: Dict, output_root: str = "reports", report_date: str | None = None) -> Path:
    if report_date is None or report_date == "today":
        report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    report_dir = ensure_dir(Path(output_root) / report_date)
    report_path = report_dir / "report.html"
    dashboard_path = report_dir / "dashboard.html"
    index_path = report_dir / "index.html"

    template = Path("smart_market_intelligence/reporting/html_template.html").read_text(encoding="utf-8")

    session = _safe(report_data.get("session"))
    regime = _safe(report_data.get("regime"))
    news_risk = _safe(report_data.get("news_risk"))
    regime_class = "good" if regime.lower() == "trend" else "warn" if regime.lower() == "range" else "risk"
    risk_class = "good" if news_risk.lower() == "low" else "warn" if news_risk.lower() == "medium" else "risk"
    header_badges = (
        f"<span class='badge good'>Session: {session}</span>"
        f"<span class='badge {regime_class}'>Regime: {regime}</span>"
        f"<span class='badge {risk_class}'>News Risk: {news_risk}</span>"
    )

    watchlist = report_data.get("watchlist") or []
    watchlist_list = "".join(
        f"<p><b>{_safe(row.get('pair'))}</b> · {_safe(str(row.get('direction', '—')).upper())} · {_safe(row.get('priority_score'))}</p>"
        for row in watchlist[:10]
    ) or "—"

    macro_sorted = sorted((report_data.get("macro_strength") or {}).items(), key=lambda x: x[1], reverse=True)
    macro_rows = "".join(
        f"<tr><td>{_safe(ccy)}</td><td>{float(score):.2f}</td><td>{_status_from_score(float(score))}</td></tr>"
        for ccy, score in macro_sorted
    ) or "<tr><td colspan='3'>—</td></tr>"
    macro_table = f"<table><thead><tr><th>Moeda</th><th>Score</th><th>Status</th></tr></thead><tbody>{macro_rows}</tbody></table>"

    pairs_rows = "".join(
        f"<tr><td>{_safe(row.get('pair'))}</td><td>{_safe(row.get('structure_h4'))}</td><td>{_safe(row.get('regime'))}</td><td>{'Yes' if row.get('micro_aligned') else 'No'}</td><td>{_safe(str(row.get('direction','—')).upper())}</td></tr>"
        for row in watchlist
    ) or "<tr><td colspan='5'>—</td></tr>"
    pairs_table = f"<table><thead><tr><th>Par ▲</th><th>Estrutura H4</th><th>Regime</th><th>Setup</th><th>Bias</th></tr></thead><tbody>{pairs_rows}</tbody></table>"

    news_timeline = ""
    for ev in (report_data.get("news_events") or [])[:12]:
        tags = ev.get("tags") or []
        chips = "".join(f"<span class='chip'>{_safe(t)}</span>" for t in tags) or "<span class='chip'>—</span>"
        news_timeline += f"<div style='margin-bottom:8px'><b>{_safe(ev.get('timestamp_utc'))}</b> · {_safe(ev.get('currency'))} · {_impact_badge(_safe(ev.get('impact')))}<br/>{_safe(ev.get('event_name'))}<br/>{chips}</div>"
    news_timeline = news_timeline or "—"

    theme_chips = "".join(f"<span class='chip'>{tag}</span>" for tag in ["inflation", "jobs", "rates", "growth"])

    total_pairs = len(watchlist)
    avg_setup = int(sum((row.get("setup_score") or 0) for row in watchlist) / total_pairs) if total_pairs else 0
    kpi_strip = (
        f"<div class='kpi'><div class='k'>Pairs Tracked</div><div class='v'>{total_pairs}</div></div>"
        f"<div class='kpi'><div class='k'>Avg Setup Score</div><div class='v'>{avg_setup}</div></div>"
        f"<div class='kpi'><div class='k'>News Events</div><div class='v'>{len(report_data.get('news_events') or [])}</div></div>"
        f"<div class='kpi'><div class='k'>High Risk Events</div><div class='v'>{len([e for e in (report_data.get('news_events') or []) if e.get('impact') == 'high'])}</div></div>"
    )

    tech = ""
    for detail in report_data.get("technical_details") or []:
        score = int(detail.get("score_final") or 0)
        tech += f"""
        <details>
          <summary><span>{_safe(detail.get('pair'))}</span><span>{_setup_badge(score)}</span></summary>
          <div class='detail-body'>
            <div class='metric'><div class='mk'>W1</div><div class='mv'>{_safe(detail.get('context_w1'))}</div></div>
            <div class='metric'><div class='mk'>D1</div><div class='mv'>{_safe(detail.get('context_d1'))}</div></div>
            <div class='metric'><div class='mk'>H4</div><div class='mv'>{_safe(detail.get('structure_h4'))}</div></div>
            <div class='metric'><div class='mk'>MSS</div><div class='mv'>{_safe(detail.get('mss_status'))}</div></div>
            <div class='metric'><div class='mk'>FVG</div><div class='mv'>{_safe(detail.get('fvg_status'))}</div></div>
            <div class='metric'><div class='mk'>PD</div><div class='mv'>{_safe(detail.get('premium_discount'))}</div></div>
            <div class='metric'><div class='mk'>RR</div><div class='mv'>{_safe(detail.get('rr_projected'))}</div></div>
            <div class='metric'><div class='mk'>Score</div><div class='mv'>{score}</div></div>
            <div class='metric'><div class='mk'>Rules</div><div class='mv'>News block / Range block</div></div>
          </div>
        </details>
        """
    technical_accordion = tech or "<div class='card'>—</div>"

    ticker_quotes = report_data.get("ticker_quotes") or []
    ticker_items = "".join(_ticker_item_html(row) for row in ticker_quotes) or "<span class='ticker-item'>No ticker data</span>"

    html = _render_template(
        template,
        {
            "report_date": _safe(report_date),
            "header_badges": header_badges,
            "ticker_items": ticker_items,
            "ticker_last_update": _safe(report_data.get("ticker_last_update"), datetime.now(timezone.utc).strftime("%H:%M:%S UTC")),
            "kpi_strip": kpi_strip,
            "macro_table": macro_table,
            "pairs_table": pairs_table,
            "news_timeline": news_timeline,
            "technical_accordion": technical_accordion,
            "watchlist_list": watchlist_list,
            "theme_chips": theme_chips,
        },
    )

    dashboard_path.write_text(html, encoding="utf-8")
    report_path.write_text(html, encoding="utf-8")
    index_path.write_text("<meta http-equiv='refresh' content='0; url=dashboard.html' />", encoding="utf-8")
    return report_path


def build_report_payload(
    report_date: str,
    session: str,
    regime: str,
    macro_strength: Dict[str, float],
    micro_meta_by_pair: Dict[str, Dict],
    watchlist: List[Dict],
    news_events: List[Dict],
    technical_details: List[Dict],
    ticker_quotes: List[Dict] | None = None,
    ticker_last_update: str | None = None,
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
        "ticker_quotes": ticker_quotes or [],
        "ticker_last_update": ticker_last_update or datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
    }
