from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict

from smart_market_intelligence.utils.helpers import ensure_dir


def _table(rows, headers):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{head}</tr>{body}</table>"


def build_report(report_data: Dict, output_root: str = "smart_market_intelligence/reports") -> Path:
    report_date = datetime.utcnow().strftime("%Y-%m-%d")
    report_dir = ensure_dir(Path(output_root) / report_date)
    output_path = report_dir / "report.html"

    executive = report_data["executive"]
    macro_table = _table(executive["macro_ranking"], ["Moeda", "Força Macro"])
    micro_table = _table(executive["micro_ranking"], ["Par", "Força Micro"])
    watch_rows = [(w["pair"], w["session"], w["direction"], w["priority_score"]) for w in executive["watchlist"]]
    watch_table = _table(watch_rows, ["Par", "Sessão", "Direção", "Score"])

    technical_html = ""
    for item in report_data["technical"]:
        technical_html += (
            f"<div class='card'><h3>{item['pair']}</h3><p><b>Contexto W1/D1:</b> {item['context']}</p>"
            f"<p><b>Estrutura H4:</b> {item['structure']}</p><p><b>MSS validado:</b> {item['mss']}</p>"
            f"<p><b>PD Array:</b> {item['pd']}</p><p><b>Score Setup:</b> {item['setup_score']}</p>"
            f"<p><b>Conclusão:</b> {item['conclusion']}</p></div>"
        )

    html = f"""<!DOCTYPE html><html lang='pt-BR'><head><meta charset='UTF-8'><title>Relatório {report_date}</title>
    <style>body{{font-family:Arial;margin:24px}} .card{{border:1px solid #ddd;padding:10px;margin:10px 0}} table{{width:100%;border-collapse:collapse}} th,td{{border:1px solid #ddd;padding:6px}}</style>
    </head><body><h1>Relatório Diário - Smart Market Intelligence</h1><p><b>Data:</b> {report_date}</p>
    <h2>Parte 1 — Resumo Executivo</h2><div class='card'><p><b>Ambiente do dia:</b> {executive['environment']}</p><p><b>Estado de notícias:</b> {executive['news_state']}</p></div>
    <div class='card'><h3>Ranking Macro</h3>{macro_table}</div><div class='card'><h3>Ranking Micro</h3>{micro_table}</div><div class='card'><h3>Watchlist por sessão</h3>{watch_table}</div>
    <h2>Parte 2 — Análise Técnica</h2>{technical_html}</body></html>"""

    output_path.write_text(html, encoding="utf-8")
    return output_path


def make_technical_block(pair: str, structure: Dict, setup_score: int, direction: str) -> Dict:
    return {
        "pair": pair,
        "context": "Viés direcional calculado com dados sintéticos W1/D1.",
        "structure": "Range" if structure["range_state"]["in_range"] else "Expansão",
        "mss": "Sim" if structure["mss_state"].get("mss_valid") else "Não",
        "pd": structure["pd_state"].get("status", "unknown"),
        "setup_score": setup_score,
        "conclusion": f"Priorizar direção {direction} com gestão institucional.",
    }
