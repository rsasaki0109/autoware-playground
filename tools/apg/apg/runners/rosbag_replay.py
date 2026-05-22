from __future__ import annotations

from typing import Any

from .base import RunnerOutcome


def dry_run(
    *,
    benchmark: dict[str, Any],
    experiment: dict[str, Any],
    headless: bool,
    seed: int | None,
) -> RunnerOutcome:
    runner_cfg = benchmark.get("runner", {}) or {}
    assets = benchmark.get("assets", {}) or {}
    rosbag = runner_cfg.get("rosbag") or assets.get("rosbag")

    metrics: dict[str, Any] = {"dry_run": True}
    gates = benchmark.get("gates", {}) or {}
    for group in ("required", "diagnostic"):
        for gate in gates.get(group, []) or []:
            metrics.setdefault(gate.get("name"), None)

    runtime_hints = {
        "backend": "rosbag_replay",
        "dispatched": True,
        "headless": headless,
        "rosbag": rosbag,
        "loop": False,
        "timeout_sec": runner_cfg.get("timeout_sec"),
        "experiment_mode": experiment.get("mode"),
        "seed": seed,
    }

    failures = ["sim_invalid"]
    return RunnerOutcome(
        runner="rosbag_replay",
        metrics=metrics,
        failures=failures,
        runtime_hints=runtime_hints,
    )
