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


def _status_from_score(score: float) -> str:
    if score >= 30:
        return "Forte"
    if score <= -30:
        return "Fraca"
    return "Neutra"


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


def _minutes_to_event(ts: str) -> str:
    try:
        event_dt = datetime.fromisoformat(ts).astimezone(timezone.utc)
        now = datetime.now(timezone.utc)
        return f"T{int((event_dt - now).total_seconds() // 60):+d}m"
    except Exception:
        return "—"


def _render_template(template_str: str, values: Dict[str, str]) -> str:
    html = template_str
    for key, value in values.items():
        html = html.replace(f"{{{{{key}}}}}", value)
    return html


def _impact_badge(impact: str) -> str:
    impact_norm = (impact or "").lower()
    klass = "risk" if impact_norm == "high" else "warn" if impact_norm == "medium" else "neutral"
    return f"<span class='badge {klass}'>{_safe(impact, 'unknown').upper()}</span>"


def _heat_color(score: float) -> str:
    if score >= 30:
        return "#166534"
    if score >= 0:
        return "#15803d"
    if score <= -30:
        return "#991b1b"
    return "#b45309"


def build_report(report_data: Dict, output_root: str = "reports", report_date: str | None = None) -> Path:
    if report_date is None or report_date == "today":
        report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    report_dir = ensure_dir(Path(output_root) / report_date)
    output_path = report_dir / "report.html"

    template_path = Path("smart_market_intelligence/reporting/html_template.html")
    template_str = template_path.read_text(encoding="utf-8")

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

    macro_sorted = sorted((report_data.get("macro_strength") or {}).items(), key=lambda x: x[1], reverse=True)
    macro_rows = "".join(
        f"<tr><td>{_safe(ccy)}</td><td>{float(score):.2f}</td><td>{_status_from_score(float(score))}</td></tr>"
        for ccy, score in macro_sorted
    ) or "<tr><td colspan='3'>—</td></tr>"
    macro_table = (
        "<table><thead><tr><th>Moeda</th><th>Score</th><th>Status</th></tr></thead>"
        f"<tbody>{macro_rows}</tbody></table>"
    )

    macro_heatmap = "".join(
        f"<p><b>{_safe(ccy)}</b> <span class='heat-cell' style='background:{_heat_color(float(score))}'>{float(score):.1f}</span></p>"
        for ccy, score in macro_sorted[:8]
    ) or "—"

    watchlist = report_data.get("watchlist") or []
    pairs_rows = ""
    for row in watchlist:
        pairs_rows += (
            f"<tr><td>{_safe(row.get('pair'))}</td><td>{_safe(row.get('structure_h4'))}</td><td>{_safe(row.get('regime'))}</td>"
            f"<td>{'Yes' if row.get('micro_aligned') else 'No'}</td><td>{_safe(str(row.get('direction', '—')).upper())}</td></tr>"
        )
    pairs_rows = pairs_rows or "<tr><td colspan='5'>—</td></tr>"
    pairs_table = (
        "<table><thead><tr><th>Par ▲</th><th>Estrutura H4</th><th>Regime</th><th>Setup Friendly</th><th>Bias</th></tr></thead>"
        f"<tbody>{pairs_rows}</tbody></table>"
    )

    high_events = [e for e in (report_data.get("news_events") or []) if e.get("impact") == "high"]
    if not high_events:
        high_events = report_data.get("news_events") or []

    news_timeline = ""
    for ev in high_events[:12]:
        tags = ev.get("tags") or []
        tag_chips = " ".join(f"<span class='chip'>{_safe(tag)}</span>" for tag in tags) if tags else "<span class='chip'>—</span>"
        news_timeline += (
            "<div class='event'>"
            f"<div><b>{_minutes_to_event(_safe(ev.get('timestamp_utc'), ''))}</b> · {_safe(ev.get('currency'))} · {_impact_badge(_safe(ev.get('impact')))}</div>"
            f"<div>{_safe(ev.get('event_name'))}</div>"
            f"<div class='chip-wrap'>{tag_chips}</div>"
            "</div>"
        )
    news_timeline = news_timeline or "<div class='event'>—</div>"

    theme_set = []
    for event in report_data.get("news_events") or []:
        for tag in event.get("tags") or []:
            t = str(tag).lower()
            if t in {"inflation", "jobs", "rates", "growth"} and t not in theme_set:
                theme_set.append(t)
    for fallback in ["inflation", "jobs", "rates", "growth"]:
        if fallback not in theme_set:
            theme_set.append(fallback)
    theme_chips = "".join(f"<span class='chip'>{t}</span>" for t in theme_set[:6])

    watchlist_list = "".join(
        f"<p><b>{_safe(row.get('pair'))}</b> · {_safe(str(row.get('direction','—')).upper())} · score {_safe(row.get('priority_score'))}</p>"
        for row in watchlist[:8]
    ) or "—"

    total_pairs = len(watchlist)
    avg_setup = int(sum((row.get("setup_score") or 0) for row in watchlist) / total_pairs) if total_pairs else 0
    macro_leader = macro_sorted[0][0] if macro_sorted else "—"
    high_impact_count = len([e for e in (report_data.get("news_events") or []) if e.get("impact") == "high"])

    kpi_strip = (
        f"<div class='kpi'><div class='label'>Pairs Tracked</div><div class='value'>{total_pairs}</div></div>"
        f"<div class='kpi'><div class='label'>Avg Setup Score</div><div class='value'>{avg_setup}</div></div>"
        f"<div class='kpi'><div class='label'>Macro Leader</div><div class='value'>{_safe(macro_leader)}</div></div>"
        f"<div class='kpi'><div class='label'>High Impact Events</div><div class='value'>{high_impact_count}</div></div>"
    )

    tech_blocks = ""
    for detail in report_data.get("technical_details") or []:
        score_final = int(detail.get("score_final") or 0)
        setup_badge = _setup_badge(score_final)
        tech_blocks += f"""
        <details>
          <summary>
            <span>{_safe(detail.get('pair'))} · {_safe(str(detail.get('bias', '—')).upper())}</span>
            <span>{setup_badge}</span>
          </summary>
          <div class='detail-body'>
            <div class='metric'><div class='k'>Contexto W1</div><div class='v'>{_safe(detail.get('context_w1'))}</div></div>
            <div class='metric'><div class='k'>Contexto D1</div><div class='v'>{_safe(detail.get('context_d1'))}</div></div>
            <div class='metric'><div class='k'>Estrutura H4</div><div class='v'>{_safe(detail.get('structure_h4'))}</div></div>
            <div class='metric'><div class='k'>MSS Status</div><div class='v'>{_safe(detail.get('mss_status'))}</div></div>
            <div class='metric'><div class='k'>FVG Status</div><div class='v'>{_safe(detail.get('fvg_status'))}</div></div>
            <div class='metric'><div class='k'>Premium/Discount</div><div class='v'>{_safe(detail.get('premium_discount'))}</div></div>
            <div class='metric'><div class='k'>RR Projetado</div><div class='v'>{_safe(detail.get('rr_projected'))}</div></div>
            <div class='metric'><div class='k'>Score Final</div><div class='v'>{score_final}</div></div>
            <div class='metric'><div class='k'>Rules</div><div class='v'>News block + Range block</div></div>
          </div>
        </details>
        """
    tech_blocks = tech_blocks or "<div class='card'>—</div>"

    html = _render_template(
        template_str,
        {
            "report_date": _safe(report_date),
            "header_badges": header_badges,
            "kpi_strip": kpi_strip,
            "macro_table": macro_table,
            "pairs_table": pairs_table,
            "news_timeline": news_timeline,
            "technical_accordion": tech_blocks,
            "theme_chips": theme_chips,
            "watchlist_list": watchlist_list,
            "macro_heatmap": macro_heatmap,
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
