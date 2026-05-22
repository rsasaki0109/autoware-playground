from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def _rows(mapping: dict[str, Any]) -> str:
    if not mapping:
        return "<tr><td colspan=\"2\">None</td></tr>"
    rows = []
    for key, value in mapping.items():
        rows.append(
            "<tr>"
            f"<th>{html.escape(str(key))}</th>"
            f"<td><code>{html.escape(json.dumps(value, sort_keys=True))}</code></td>"
            "</tr>"
        )
    return "\n".join(rows)


def _failure_card_rows(result: dict[str, Any]) -> str:
    cards = (result.get("artifacts") or {}).get("failure_cards") or []
    if isinstance(cards, str):
        cards = [cards]
    if not cards:
        return "<tr><td colspan=\"2\">None</td></tr>"
    rows = []
    for entry in cards:
        safe = html.escape(str(entry))
        rows.append(
            "<tr>"
            f"<th>Card</th>"
            f"<td><a href=\"{safe}\"><code>{safe}</code></a></td>"
            "</tr>"
        )
    return "\n".join(rows)


def render_report(result: dict[str, Any]) -> str:
    failures = result.get("failures") or []
    failure_text = ", ".join(html.escape(str(item)) for item in failures) if failures else "None"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>APG Run Report - {html.escape(str(result.get("run_id", "unknown")))}</title>
  <style>
    body {{
      color: #172026;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
      margin: 0;
      background: #f7f8f8;
    }}
    main {{
      margin: 0 auto;
      max-width: 980px;
      padding: 32px 20px 56px;
    }}
    h1, h2 {{
      line-height: 1.2;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      background: #ffffff;
      border: 1px solid #d8dedc;
      margin-bottom: 24px;
    }}
    th, td {{
      border-bottom: 1px solid #e6ebe9;
      padding: 10px 12px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      width: 260px;
      background: #eef2f1;
    }}
    code {{
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .status {{
      display: inline-block;
      border: 1px solid #aab6b3;
      border-radius: 4px;
      padding: 2px 8px;
      background: #ffffff;
    }}
  </style>
</head>
<body>
<main>
  <h1>APG Run Report</h1>
  <p><span class="status">{html.escape(str(result.get("execution", {}).get("status", "unknown")))}</span></p>

  <h2>Run</h2>
  <table>
    <tr><th>Run ID</th><td>{html.escape(str(result.get("run_id", "")))}</td></tr>
    <tr><th>Experiment</th><td>{html.escape(str(result.get("experiment", "")))}</td></tr>
    <tr><th>Benchmark</th><td>{html.escape(str(result.get("benchmark", "")))}</td></tr>
    <tr><th>Mode</th><td>{html.escape(str(result.get("mode", "")))}</td></tr>
    <tr><th>Failures</th><td>{failure_text}</td></tr>
  </table>

  <h2>Metrics</h2>
  <table>
    {_rows(result.get("metrics", {}))}
  </table>

  <h2>Assets</h2>
  <table>
    {_rows(result.get("assets", {}))}
  </table>

  <h2>Runtime</h2>
  <table>
    {_rows(result.get("runtime", {}))}
  </table>

  <h2>Failure Cards</h2>
  <table>
    {_failure_card_rows(result)}
  </table>

  <h2>Reproduce</h2>
  <table>
    <tr><th>Command</th><td><code>{html.escape(str(result.get("reproduce", "")))}</code></td></tr>
  </table>
</main>
</body>
</html>
"""


def write_report(result_path: Path, output_path: Path | None = None) -> Path:
    if result_path.is_dir():
        result_path = result_path / "result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    report_path = output_path or (result_path.parent / "report.html")
    report_path.write_text(render_report(result), encoding="utf-8")
    return report_path
