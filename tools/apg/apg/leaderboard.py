from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .schema import (
    iter_benchmark_manifests,
    iter_experiment_manifests,
    load_document,
)


@dataclass
class LeaderboardEntry:
    benchmark: str
    experiment: str
    task: str
    run_id: str | None
    source: str  # "baseline" | "runs" | "missing"
    baseline_status: str | None
    status: str | None
    failures: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

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
        }


@dataclass
class Leaderboard:
    columns: list[str]
    entries: list[LeaderboardEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "columns": self.columns,
            "entries": [entry.to_dict() for entry in self.entries],
        }


def _collect_metric_columns(
    benchmark_doc: dict[str, Any], entries: Iterable[LeaderboardEntry]
) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()
    gates = benchmark_doc.get("gates", {}) or {}
    for group in ("required", "diagnostic"):
        for gate in gates.get(group, []) or []:
            name = gate.get("name")
            if name and name not in seen:
                columns.append(name)
                seen.add(name)
    for entry in entries:
        for name in entry.metrics:
            if name not in seen and not name.startswith("dry_run"):
                columns.append(name)
                seen.add(name)
    return columns


def _select_best_record(
    benchmark_dir: Path,
    experiment_name: str,
    runs_root: Path | None,
) -> tuple[Path | None, str]:
    """Pick the most relevant RunRecord for (benchmark, experiment).

    Preference order:
      1. baseline matching the experiment name (most specific)
      2. most recent runs/<id>/result.json whose benchmark + experiment match
      3. None — show the row as "missing" (dry-run not used as leaderboard data)
    """
    baseline_dir = benchmark_dir / "baselines" / experiment_name
    baseline_result = baseline_dir / "result.json"
    if baseline_result.is_file():
        return baseline_result, "baseline"

    if runs_root and runs_root.is_dir():
        candidates: list[Path] = []
        for record_path in sorted(runs_root.glob("*/result.json")):
            try:
                doc = json.loads(record_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if doc.get("experiment") != experiment_name:
                continue
            if doc.get("benchmark") != _benchmark_name(benchmark_dir):
                continue
            if doc.get("execution", {}).get("dry_run"):
                continue
            candidates.append(record_path)
        if candidates:
            return candidates[-1], "runs"

    return None, "missing"


def _benchmark_name(benchmark_dir: Path) -> str:
    manifest = load_document(benchmark_dir / "benchmark.yaml")
    return manifest.get("name", benchmark_dir.name)


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
    benchmark_manifests = iter_benchmark_manifests(root)

    experiment_index: dict[str, dict[str, Any]] = {}
    for exp_path in iter_experiment_manifests(root):
        doc = load_document(exp_path)
        rel = exp_path.parent.relative_to(root).as_posix()
        doc.setdefault("_path", rel)
        experiment_index[rel] = doc

    all_entries: list[LeaderboardEntry] = []
    all_columns: list[str] = []
    seen_columns: set[str] = set()

    for manifest_path in benchmark_manifests:
        benchmark_dir = manifest_path.parent
        benchmark_doc = load_document(manifest_path)
        benchmark_name = benchmark_doc.get("name", benchmark_dir.name)
        benchmark_rel = benchmark_dir.relative_to(root).as_posix()
        task = benchmark_doc.get("task", "unknown")

        candidate_experiments: list[str] = []
        for exp_rel, exp_doc in experiment_index.items():
            if exp_doc.get("task") != task:
                continue
            if benchmark_rel in _experiment_refs(exp_doc) or not _experiment_refs(exp_doc):
                candidate_experiments.append(exp_rel)

        bench_entries: list[LeaderboardEntry] = []
        for exp_rel in sorted(candidate_experiments):
            exp_doc = experiment_index[exp_rel]
            exp_name = exp_doc.get("name", Path(exp_rel).name)
            record_path, source = _select_best_record(benchmark_dir, exp_name, runs_root)
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
            bench_entries.append(entry)

        for column in _collect_metric_columns(benchmark_doc, bench_entries):
            if column not in seen_columns:
                all_columns.append(column)
                seen_columns.add(column)
        all_entries.extend(bench_entries)

    return Leaderboard(columns=all_columns, entries=all_entries)


def _format_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "✓" if value else "✗"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def format_leaderboard_markdown(board: Leaderboard) -> str:
    if not board.entries:
        return "no benchmarks found.\n"
    header_cols = [
        "benchmark",
        "experiment",
        "source",
        "baseline_status",
        "status",
    ] + board.columns + ["failures"]
    rows = ["| " + " | ".join(header_cols) + " |"]
    rows.append("|" + "|".join(["---"] * len(header_cols)) + "|")
    for entry in board.entries:
        cells = [
            entry.benchmark,
            entry.experiment,
            entry.source,
            entry.baseline_status or "—",
            entry.status or "—",
        ]
        for col in board.columns:
            cells.append(_format_value(entry.metrics.get(col)))
        cells.append(",".join(entry.failures) if entry.failures else "—")
        rows.append("| " + " | ".join(str(c) for c in cells) + " |")
    return "\n".join(rows) + "\n"


def format_leaderboard_text(board: Leaderboard) -> str:
    if not board.entries:
        return "no benchmarks found.\n"
    lines: list[str] = []
    for entry in board.entries:
        prefix = f"{entry.benchmark} :: {entry.experiment} ({entry.source})"
        status = f"baseline_status={entry.baseline_status or '—'} status={entry.status or '—'}"
        lines.append(f"{prefix} — {status}")
        for col in board.columns:
            value = entry.metrics.get(col)
            if value is not None:
                lines.append(f"  {col}: {_format_value(value)}")
        if entry.failures:
            lines.append(f"  failures: {', '.join(entry.failures)}")
    return "\n".join(lines) + "\n"


def emit_leaderboard(root: Path, *, fmt: str) -> str:
    board = build_leaderboard(root)
    if fmt == "json":
        return json.dumps(board.to_dict(), indent=2, sort_keys=True) + "\n"
    if fmt == "markdown":
        return format_leaderboard_markdown(board)
    return format_leaderboard_text(board)
