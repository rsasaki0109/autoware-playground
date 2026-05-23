from __future__ import annotations

import html
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .schema import (
    iter_benchmark_manifests,
    iter_experiment_manifests,
    load_document,
)


# Generic execution-side metrics that we surface regardless of benchmark
# (so two rosbag_replay benchmarks can be compared at a glance even
# when their gate metrics differ).
GENERIC_METRIC_COLUMNS: tuple[str, ...] = (
    "play_returncode",
    "play_elapsed_sec",
    "rosbag_message_count",
)


@dataclass
class LeaderboardEntry:
    benchmark: str
    experiment: str
    task: str
    run_id: str | None
    source: str  # "baseline" | "snapshot" | "runs" | "missing"
    baseline_status: str | None
    status: str | None
    failures: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    report_link: str | None = None  # repo-relative path to report.html or result.json
    record_link: str | None = None  # repo-relative path to result.json

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark": self.benchmark,
            "experiment": self.experiment,
            "task": self.task,
            "run_id": self.run_id,
            "source": self.source,
            "baseline_status": self.baseline_status,
            "status": self.status,
            "failures": self.failures,
            "metrics": self.metrics,
            "report_link": self.report_link,
            "record_link": self.record_link,
        }


@dataclass
class LeaderboardBlock:
    benchmark: str
    task: str
    runner: str | None
    columns: list[str]  # gate metrics for this benchmark only
    entries: list[LeaderboardEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark": self.benchmark,
            "task": self.task,
            "runner": self.runner,
            "columns": self.columns,
            "entries": [entry.to_dict() for entry in self.entries],
        }


@dataclass
class Leaderboard:
    blocks: list[LeaderboardBlock] = field(default_factory=list)

    @property
    def entries(self) -> list[LeaderboardEntry]:
        out: list[LeaderboardEntry] = []
        for block in self.blocks:
            out.extend(block.entries)
        return out

    @property
    def columns(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for block in self.blocks:
            for col in block.columns:
                if col not in seen:
                    out.append(col)
                    seen.add(col)
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocks": [block.to_dict() for block in self.blocks],
            "columns": self.columns,
            "entries": [entry.to_dict() for entry in self.entries],
        }


def _gate_columns(benchmark_doc: dict[str, Any]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    gates = benchmark_doc.get("gates", {}) or {}
    for group in ("required", "diagnostic"):
        for gate in gates.get(group, []) or []:
            name = gate.get("name")
            if name and name not in seen:
                columns.append(name)
                seen.add(name)
    return columns


def _block_columns(benchmark_doc: dict[str, Any]) -> list[str]:
    cols = _gate_columns(benchmark_doc)
    seen = set(cols)
    for name in GENERIC_METRIC_COLUMNS:
        if name not in seen:
            cols.append(name)
            seen.add(name)
    return cols


def _select_best_record(
    benchmark_dir: Path,
    benchmark_name: str,
    experiment_name: str,
    runs_root: Path | None,
    snapshots_root: Path | None = None,
) -> tuple[Path | None, str]:
    """Pick the most relevant RunRecord for (benchmark, experiment).

    Preference order:
      1. baseline matching the experiment name (most specific)
      2. most recent reports/run_snapshots/<id>/result.json whose benchmark +
         experiment match (committed CI-run snapshots — preferred over runs/
         because they live in-tree and so their report.html links resolve
         when published)
      3. most recent runs/<id>/result.json whose benchmark + experiment match
         and that is a non-dry-run record
      4. None — show the row as "missing"
    """
    baseline_result = benchmark_dir / "baselines" / experiment_name / "result.json"
    if baseline_result.is_file():
        return baseline_result, "baseline"

    def _scan(directory: Path | None) -> list[Path]:
        if not directory or not directory.is_dir():
            return []
        matches: list[Path] = []
        for record_path in sorted(directory.glob("*/result.json")):
            try:
                doc = json.loads(record_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if doc.get("experiment") != experiment_name:
                continue
            if doc.get("benchmark") != benchmark_name:
                continue
            if doc.get("execution", {}).get("dry_run"):
                continue
            matches.append(record_path)
        return matches

    snapshot_candidates = _scan(snapshots_root)
    if snapshot_candidates:
        return snapshot_candidates[-1], "snapshot"

    run_candidates = _scan(runs_root)
    if run_candidates:
        return run_candidates[-1], "runs"

    return None, "missing"


def _experiment_refs(experiment_doc: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    benchmarks = experiment_doc.get("benchmarks") or {}
    for group, items in benchmarks.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, str):
                    refs.add(item.rstrip("/"))
    return refs


def build_leaderboard(root: Path) -> Leaderboard:
    runs_root = root / "runs"
    snapshots_root = root / "reports" / "run_snapshots"
    benchmark_manifests = iter_benchmark_manifests(root)

    experiment_index: dict[str, dict[str, Any]] = {}
    for exp_path in iter_experiment_manifests(root):
        doc = load_document(exp_path)
        rel = exp_path.parent.relative_to(root).as_posix()
        doc.setdefault("_path", rel)
        experiment_index[rel] = doc

    blocks: list[LeaderboardBlock] = []

    for manifest_path in benchmark_manifests:
        benchmark_dir = manifest_path.parent
        benchmark_doc = load_document(manifest_path)
        benchmark_name = benchmark_doc.get("name", benchmark_dir.name)
        benchmark_rel = benchmark_dir.relative_to(root).as_posix()
        task = benchmark_doc.get("task", "unknown")
        runner = (benchmark_doc.get("runner") or {}).get("type")

        candidate_experiments: list[str] = []
        for exp_rel, exp_doc in experiment_index.items():
            if exp_doc.get("task") != task:
                continue
            refs = _experiment_refs(exp_doc)
            if benchmark_rel in refs or not refs:
                candidate_experiments.append(exp_rel)

        bench_entries: list[LeaderboardEntry] = []
        for exp_rel in sorted(candidate_experiments):
            exp_doc = experiment_index[exp_rel]
            exp_name = exp_doc.get("name", Path(exp_rel).name)
            record_path, source = _select_best_record(
                benchmark_dir,
                benchmark_name,
                exp_name,
                runs_root,
                snapshots_root,
            )
            entry = LeaderboardEntry(
                benchmark=benchmark_name,
                experiment=exp_name,
                task=task,
                run_id=None,
                source=source,
                baseline_status=None,
                status=None,
            )
            if record_path is not None:
                try:
                    record = json.loads(record_path.read_text(encoding="utf-8"))
                except Exception:
                    record = {}
                entry.run_id = record.get("run_id")
                entry.baseline_status = (record.get("execution") or {}).get("baseline_status")
                entry.status = (record.get("execution") or {}).get("status")
                entry.failures = list(record.get("failures") or [])
                entry.metrics = dict(record.get("metrics") or {})
                entry.record_link = record_path.relative_to(root).as_posix()
                report_path = record_path.parent / "report.html"
                if report_path.is_file():
                    entry.report_link = report_path.relative_to(root).as_posix()
            bench_entries.append(entry)

        blocks.append(
            LeaderboardBlock(
                benchmark=benchmark_name,
                task=task,
                runner=runner,
                columns=_block_columns(benchmark_doc),
                entries=bench_entries,
            )
        )

    return Leaderboard(blocks=blocks)


def _format_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "✓" if value else "✗"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _format_block_markdown(block: LeaderboardBlock) -> str:
    runner = f" — runner: `{block.runner}`" if block.runner else ""
    lines = [f"## {block.benchmark} ({block.task}){runner}", ""]
    if not block.entries:
        lines.append("_no experiments registered for this benchmark._")
        lines.append("")
        return "\n".join(lines)
    header = ["experiment", "source", "baseline_status", "status", *block.columns, "failures"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for entry in block.entries:
        cells = [
            entry.experiment,
            entry.source,
            entry.baseline_status or "—",
            entry.status or "—",
        ]
        for col in block.columns:
            cells.append(_format_value(entry.metrics.get(col)))
        cells.append(",".join(entry.failures) if entry.failures else "—")
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    lines.append("")
    return "\n".join(lines)


def format_leaderboard_markdown(board: Leaderboard) -> str:
    if not board.blocks:
        return "no benchmarks found.\n"
    return "\n".join(_format_block_markdown(block) for block in board.blocks)


def format_leaderboard_text(board: Leaderboard) -> str:
    if not board.blocks:
        return "no benchmarks found.\n"
    lines: list[str] = []
    for block in board.blocks:
        runner = f" [runner: {block.runner}]" if block.runner else ""
        lines.append(f"=== {block.benchmark} ({block.task}){runner} ===")
        if not block.entries:
            lines.append("  (no experiments registered)")
        for entry in block.entries:
            head = f"  {entry.experiment} ({entry.source}) — "
            head += f"baseline_status={entry.baseline_status or '—'} status={entry.status or '—'}"
            lines.append(head)
            for col in block.columns:
                value = entry.metrics.get(col)
                if value is not None:
                    lines.append(f"    {col}: {_format_value(value)}")
            if entry.failures:
                lines.append(f"    failures: {', '.join(entry.failures)}")
        lines.append("")
    return "\n".join(lines)


HTML_PAGE_CSS = """
body {
  color: #172026;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.5;
  margin: 0;
  background: #f7f8f8;
}
main {
  margin: 0 auto;
  max-width: 1080px;
  padding: 32px 20px 56px;
}
h1, h2 {
  line-height: 1.2;
}
h2 {
  margin-top: 32px;
  border-bottom: 1px solid #d8dedc;
  padding-bottom: 4px;
}
.runner-tag {
  display: inline-block;
  font-family: ui-monospace, "SFMono-Regular", Menlo, monospace;
  font-size: 0.85em;
  background: #eef2f1;
  border: 1px solid #d8dedc;
  border-radius: 4px;
  padding: 1px 6px;
  margin-left: 8px;
  color: #46545d;
}
.task-tag {
  font-weight: normal;
  color: #46545d;
}
table {
  border-collapse: collapse;
  width: 100%;
  background: #ffffff;
  border: 1px solid #d8dedc;
  margin-bottom: 8px;
  font-size: 0.95em;
}
th, td {
  border-bottom: 1px solid #e6ebe9;
  padding: 8px 10px;
  text-align: left;
  vertical-align: top;
}
thead th {
  background: #eef2f1;
  white-space: nowrap;
}
td.failures {
  color: #b03434;
}
td.value {
  font-family: ui-monospace, "SFMono-Regular", Menlo, monospace;
  white-space: nowrap;
}
.source-baseline { color: #46545d; }
.source-snapshot { color: #2c6e49; }
.source-runs { color: #2c6e49; }
.source-missing { color: #b03434; }
a { color: #1f5fa3; text-decoration: none; }
a:hover { text-decoration: underline; }
.meta { color: #46545d; font-size: 0.9em; }
""".strip()


def _join_link(link_base: str, path: str) -> str:
    base = link_base.rstrip("/")
    if not base or base == ".":
        return path
    return f"{base}/{path}"


def _experiment_cell_html(entry: LeaderboardEntry, link_base: str) -> str:
    name = html.escape(entry.experiment)
    target = entry.report_link or entry.record_link
    if not target:
        return name
    href = html.escape(_join_link(link_base, target))
    return f'<a href="{href}">{name}</a>'


def _format_block_html(block: LeaderboardBlock, link_base: str) -> str:
    runner = (
        f'<span class="runner-tag">{html.escape(block.runner)}</span>'
        if block.runner
        else ""
    )
    parts: list[str] = [
        f'<h2>{html.escape(block.benchmark)} '
        f'<span class="task-tag">({html.escape(block.task)})</span>'
        f"{runner}</h2>"
    ]
    if not block.entries:
        parts.append("<p class=\"meta\">no experiments registered for this benchmark.</p>")
        return "\n".join(parts)
    header_cells = ["experiment", "source", "baseline_status", "status"]
    header_cells.extend(block.columns)
    header_cells.append("failures")
    parts.append("<table>")
    parts.append("<thead><tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in header_cells) + "</tr></thead>")
    parts.append("<tbody>")
    for entry in block.entries:
        cells: list[str] = []
        cells.append(f"<td>{_experiment_cell_html(entry, link_base)}</td>")
        source_class = f"source-{entry.source}"
        cells.append(
            f'<td class="{source_class}">{html.escape(entry.source)}</td>'
        )
        cells.append(f"<td>{html.escape(entry.baseline_status or '—')}</td>")
        cells.append(f"<td>{html.escape(entry.status or '—')}</td>")
        for col in block.columns:
            value = _format_value(entry.metrics.get(col))
            cells.append(f'<td class="value">{html.escape(value)}</td>')
        failure_text = ", ".join(entry.failures) if entry.failures else "—"
        failure_class = "failures" if entry.failures else ""
        cells.append(f'<td class="{failure_class}">{html.escape(failure_text)}</td>')
        parts.append("<tr>" + "".join(cells) + "</tr>")
    parts.append("</tbody>")
    parts.append("</table>")
    return "\n".join(parts)


def format_leaderboard_html(board: Leaderboard, *, link_base: str = ".") -> str:
    body_blocks = (
        "\n".join(_format_block_html(block, link_base) for block in board.blocks)
        if board.blocks
        else "<p>no benchmarks found.</p>"
    )
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>autoware-playground leaderboard</title>
  <style>
{HTML_PAGE_CSS}
  </style>
</head>
<body>
<main>
  <h1>autoware-playground leaderboard</h1>
  <p class=\"meta\">Each row links to its <code>report.html</code> (or <code>result.json</code> if no report has been generated yet).</p>
{body_blocks}
</main>
</body>
</html>
"""


def emit_leaderboard(root: Path, *, fmt: str, link_base: str = ".") -> str:
    board = build_leaderboard(root)
    if fmt == "json":
        return json.dumps(board.to_dict(), indent=2, sort_keys=True) + "\n"
    if fmt == "markdown":
        return format_leaderboard_markdown(board)
    if fmt == "html":
        return format_leaderboard_html(board, link_base=link_base)
    return format_leaderboard_text(board)
