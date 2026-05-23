from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


# Metrics that we never report as regressions because they reflect the
# environment (CI runtime, replay clock) rather than the experiment's
# behavior — diffing them produces noise.
_NOISY_METRICS: frozenset[str] = frozenset(
    {
        "play_elapsed_sec",
        "play_timed_out",
    }
)


def _entry_key(entry: dict[str, Any]) -> tuple[str, str]:
    return (
        str(entry.get("benchmark", "")),
        str(entry.get("experiment", "")),
    )


def _iter_entries(payload: dict[str, Any]) -> Iterable[dict[str, Any]]:
    if isinstance(payload.get("entries"), list):
        return payload["entries"]
    flat: list[dict[str, Any]] = []
    for block in payload.get("blocks", []) or []:
        for entry in block.get("entries", []) or []:
            flat.append(entry)
    return flat


@dataclass
class MetricChange:
    name: str
    base: Any
    head: Any

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "base": self.base, "head": self.head}


@dataclass
class EntryDiff:
    benchmark: str
    experiment: str
    kind: str  # "added" | "removed" | "changed" | "unchanged"
    base: dict[str, Any] | None = None
    head: dict[str, Any] | None = None
    metric_changes: list[MetricChange] = field(default_factory=list)
    status_change: tuple[str | None, str | None] | None = None
    failure_added: list[str] = field(default_factory=list)
    failure_removed: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark": self.benchmark,
            "experiment": self.experiment,
            "kind": self.kind,
            "metric_changes": [m.to_dict() for m in self.metric_changes],
            "status_change": list(self.status_change) if self.status_change else None,
            "failure_added": self.failure_added,
            "failure_removed": self.failure_removed,
        }


@dataclass
class LeaderboardDiff:
    diffs: list[EntryDiff] = field(default_factory=list)

    @property
    def changed(self) -> list[EntryDiff]:
        return [d for d in self.diffs if d.kind != "unchanged"]

    @property
    def has_changes(self) -> bool:
        return any(d.kind != "unchanged" for d in self.diffs)

    def to_dict(self) -> dict[str, Any]:
        return {"diffs": [d.to_dict() for d in self.diffs]}


def _compare_metrics(
    base_metrics: dict[str, Any], head_metrics: dict[str, Any]
) -> list[MetricChange]:
    changes: list[MetricChange] = []
    all_keys = sorted(set(base_metrics) | set(head_metrics))
    for key in all_keys:
        if key in _NOISY_METRICS:
            continue
        base_val = base_metrics.get(key)
        head_val = head_metrics.get(key)
        if base_val == head_val:
            continue
        changes.append(MetricChange(name=key, base=base_val, head=head_val))
    return changes


def compute_diff(base_payload: dict[str, Any], head_payload: dict[str, Any]) -> LeaderboardDiff:
    base_index = {_entry_key(e): e for e in _iter_entries(base_payload)}
    head_index = {_entry_key(e): e for e in _iter_entries(head_payload)}

    diffs: list[EntryDiff] = []
    for key in sorted(set(base_index) | set(head_index)):
        base_entry = base_index.get(key)
        head_entry = head_index.get(key)
        benchmark, experiment = key

        if base_entry is None:
            diffs.append(
                EntryDiff(
                    benchmark=benchmark,
                    experiment=experiment,
                    kind="added",
                    head=head_entry,
                )
            )
            continue
        if head_entry is None:
            diffs.append(
                EntryDiff(
                    benchmark=benchmark,
                    experiment=experiment,
                    kind="removed",
                    base=base_entry,
                )
            )
            continue

        metric_changes = _compare_metrics(
            base_entry.get("metrics") or {}, head_entry.get("metrics") or {}
        )
        base_status = base_entry.get("status")
        head_status = head_entry.get("status")
        status_change = (
            (base_status, head_status) if base_status != head_status else None
        )
        base_failures = set(base_entry.get("failures") or [])
        head_failures = set(head_entry.get("failures") or [])
        failure_added = sorted(head_failures - base_failures)
        failure_removed = sorted(base_failures - head_failures)

        kind = "unchanged"
        if metric_changes or status_change or failure_added or failure_removed:
            kind = "changed"

        diffs.append(
            EntryDiff(
                benchmark=benchmark,
                experiment=experiment,
                kind=kind,
                base=base_entry,
                head=head_entry,
                metric_changes=metric_changes,
                status_change=status_change,
                failure_added=failure_added,
                failure_removed=failure_removed,
            )
        )

    return LeaderboardDiff(diffs=diffs)


def _format_value(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "✓" if value else "✗"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _format_metric_change(change: MetricChange) -> str:
    return (
        f"`{change.name}`: {_format_value(change.base)} → {_format_value(change.head)}"
    )


def format_diff_markdown(diff: LeaderboardDiff) -> str:
    if not diff.has_changes:
        return "## Leaderboard diff\n\nNo benchmark rows changed.\n"
    lines: list[str] = ["## Leaderboard diff", ""]
    summary = {
        "added": 0,
        "removed": 0,
        "changed": 0,
    }
    for d in diff.diffs:
        if d.kind in summary:
            summary[d.kind] += 1
    lines.append(
        f"_Rows added: {summary['added']}, "
        f"removed: {summary['removed']}, "
        f"changed: {summary['changed']}._"
    )
    lines.append("")
    lines.append("| benchmark | experiment | kind | what changed |")
    lines.append("|---|---|---|---|")
    for d in diff.changed:
        parts: list[str] = []
        if d.status_change:
            base_status, head_status = d.status_change
            parts.append(
                f"status: {_format_value(base_status)} → {_format_value(head_status)}"
            )
        if d.failure_added:
            parts.append("failures+: " + ", ".join(f"`{t}`" for t in d.failure_added))
        if d.failure_removed:
            parts.append("failures-: " + ", ".join(f"`{t}`" for t in d.failure_removed))
        if d.metric_changes:
            parts.extend(_format_metric_change(c) for c in d.metric_changes)
        if not parts:
            if d.kind == "added":
                parts.append("new row")
            elif d.kind == "removed":
                parts.append("row removed")
        cell = "<br>".join(parts) if parts else "—"
        lines.append(
            f"| {d.benchmark} | {d.experiment} | {d.kind} | {cell} |"
        )
    lines.append("")
    return "\n".join(lines)


def diff_paths(base_path: Path, head_path: Path) -> LeaderboardDiff:
    base_payload = json.loads(base_path.read_text(encoding="utf-8"))
    head_payload = json.loads(head_path.read_text(encoding="utf-8"))
    return compute_diff(base_payload, head_payload)
