from __future__ import annotations

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
) -> tuple[Path | None, str]:
    """Pick the most relevant RunRecord for (benchmark, experiment).

    Preference order:
      1. baseline matching the experiment name (most specific)
      2. most recent runs/<id>/result.json whose benchmark + experiment match
         and that is a non-dry-run record
      3. None — show the row as "missing"
    """
    baseline_result = benchmark_dir / "baselines" / experiment_name / "result.json"
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
            if doc.get("benchmark") != benchmark_name:
                continue
            if doc.get("execution", {}).get("dry_run"):
                continue
            candidates.append(record_path)
        if candidates:
            return candidates[-1], "runs"

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
                benchmark_dir, benchmark_name, exp_name, runs_root
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


def emit_leaderboard(root: Path, *, fmt: str) -> str:
    board = build_leaderboard(root)
    if fmt == "json":
        return json.dumps(board.to_dict(), indent=2, sort_keys=True) + "\n"
    if fmt == "markdown":
        return format_leaderboard_markdown(board)
    return format_leaderboard_text(board)
