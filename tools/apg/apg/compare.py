from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def load_run_record(path: Path) -> dict[str, Any]:
    if path.is_dir():
        path = path / "result.json"
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class MetricDiff:
    name: str
    left: Any
    right: Any
    delta: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {"metric": self.name, "left": self.left, "right": self.right, "delta": self.delta}


@dataclass
class CompareResult:
    left_path: Path
    right_path: Path
    left_run_id: str | None = None
    right_run_id: str | None = None
    benchmark_match: bool = True
    metric_diffs: list[MetricDiff] = field(default_factory=list)
    failure_only_left: list[str] = field(default_factory=list)
    failure_only_right: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "left": {"path": str(self.left_path), "run_id": self.left_run_id},
            "right": {"path": str(self.right_path), "run_id": self.right_run_id},
            "benchmark_match": self.benchmark_match,
            "metric_diffs": [diff.to_dict() for diff in self.metric_diffs],
            "failure_only_left": self.failure_only_left,
            "failure_only_right": self.failure_only_right,
            "warnings": self.warnings,
        }


def _numeric_delta(left: Any, right: Any) -> Any:
    if isinstance(left, bool) or isinstance(right, bool):
        return None
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return right - left
    return None


def compare_run_records(left_path: Path, right_path: Path) -> CompareResult:
    left = load_run_record(left_path)
    right = load_run_record(right_path)
    result = CompareResult(
        left_path=left_path,
        right_path=right_path,
        left_run_id=left.get("run_id"),
        right_run_id=right.get("run_id"),
    )

    if left.get("benchmark") != right.get("benchmark"):
        result.benchmark_match = False
        result.warnings.append(
            f"benchmark differs: {left.get('benchmark')!r} vs {right.get('benchmark')!r}"
        )

    left_metrics = left.get("metrics") or {}
    right_metrics = right.get("metrics") or {}
    keys = sorted(set(left_metrics) | set(right_metrics))
    for key in keys:
        lvalue = left_metrics.get(key)
        rvalue = right_metrics.get(key)
        if lvalue == rvalue:
            continue
        result.metric_diffs.append(
            MetricDiff(name=key, left=lvalue, right=rvalue, delta=_numeric_delta(lvalue, rvalue))
        )

    left_failures = set(left.get("failures") or [])
    right_failures = set(right.get("failures") or [])
    result.failure_only_left = sorted(left_failures - right_failures)
    result.failure_only_right = sorted(right_failures - left_failures)
    return result


def format_compare_text(result: CompareResult) -> str:
    lines = [
        f"left:  {result.left_path}  ({result.left_run_id})",
        f"right: {result.right_path}  ({result.right_run_id})",
        f"benchmark_match: {result.benchmark_match}",
    ]
    if result.warnings:
        lines.append("")
        lines.append("warnings:")
        for warning in result.warnings:
            lines.append(f"  - {warning}")
    lines.append("")
    lines.append("metric diffs:")
    if not result.metric_diffs:
        lines.append("  (none)")
    for diff in result.metric_diffs:
        delta = f"  delta={diff.delta}" if diff.delta is not None else ""
        lines.append(f"  - {diff.name}: {diff.left!r} -> {diff.right!r}{delta}")
    lines.append("")
    lines.append(f"failures only on left:  {result.failure_only_left}")
    lines.append(f"failures only on right: {result.failure_only_right}")
    return "\n".join(lines) + "\n"
