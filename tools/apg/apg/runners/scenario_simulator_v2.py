from __future__ import annotations

from typing import Any

from .base import ApgRunnerError, RunnerOutcome


def dry_run(
    *,
    benchmark: dict[str, Any],
    experiment: dict[str, Any],
    headless: bool,
    seed: int | None,
) -> RunnerOutcome:
    runner_cfg = benchmark.get("runner", {}) or {}
    scenario = runner_cfg.get("scenario") or benchmark.get("assets", {}).get("scenario")
    autoware_launch = (benchmark.get("autoware") or {}).get("launch") or {}

    metrics: dict[str, Any] = {"dry_run": True}
    gates = benchmark.get("gates", {}) or {}
    for group in ("required", "diagnostic"):
        for gate in gates.get(group, []) or []:
            metrics.setdefault(gate.get("name"), None)

    runtime_hints = {
        "backend": "scenario_simulator_v2",
        "dispatched": True,
        "headless": headless,
        "scenario": scenario,
        "timeout_sec": runner_cfg.get("timeout_sec"),
        "autoware_launch_package": autoware_launch.get("package"),
        "autoware_launch_file": autoware_launch.get("file"),
        "experiment_mode": experiment.get("mode"),
        "seed": seed,
    }

    failures = ["sim_invalid"]
    return RunnerOutcome(
        runner="scenario_simulator_v2",
        metrics=metrics,
        failures=failures,
        runtime_hints=runtime_hints,
    )


def execute(
    *,
    benchmark: dict[str, Any],
    experiment: dict[str, Any],
    headless: bool,
    seed: int | None,
) -> RunnerOutcome:
    raise ApgRunnerError(
        "scenario_simulator_v2 real execution is not connected yet."
        " The image ghcr.io/tier4/scenario_simulator_v2:humble is verified"
        " working by .github/workflows/scenario-sim-probe.yaml (bundled"
        " all-in-one.yaml reaches Passed). Next step: invoke"
        " scenario_test_runner inside that image with benchmark.assets.scenario"
        " and collect metrics into a real RunRecord. See plan.md §27 item 20."
    )
