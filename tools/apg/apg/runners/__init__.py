from __future__ import annotations

from typing import Any

from .base import ApgRunnerError, RunnerOutcome


KNOWN_DISPATCHED_RUNNERS = ("scenario_simulator_v2", "rosbag_replay")
KNOWN_FALLBACK_RUNNERS = ("planning_simulator", "awsim")


def runner_dry_run(
    runner_type: str,
    *,
    benchmark: dict[str, Any],
    experiment: dict[str, Any],
    headless: bool,
    seed: int | None,
) -> RunnerOutcome:
    if runner_type == "scenario_simulator_v2":
        from . import scenario_simulator_v2 as backend
    elif runner_type == "rosbag_replay":
        from . import rosbag_replay as backend
    elif runner_type in KNOWN_FALLBACK_RUNNERS:
        return RunnerOutcome(
            runner=runner_type,
            metrics={"dry_run": True},
            failures=["sim_invalid"],
            runtime_hints={
                "backend": runner_type,
                "dispatched": False,
                "headless": headless,
            },
        )
    else:
        raise ApgRunnerError(
            f"unknown runner.type {runner_type!r}"
            f" (known: {sorted(set(KNOWN_DISPATCHED_RUNNERS + KNOWN_FALLBACK_RUNNERS))})"
        )
    return backend.dry_run(
        benchmark=benchmark,
        experiment=experiment,
        headless=headless,
        seed=seed,
    )


def runner_execute(
    runner_type: str,
    *,
    benchmark: dict[str, Any],
    experiment: dict[str, Any],
    headless: bool,
    seed: int | None,
) -> RunnerOutcome:
    if runner_type == "scenario_simulator_v2":
        from . import scenario_simulator_v2 as backend
    elif runner_type == "rosbag_replay":
        from . import rosbag_replay as backend
    else:
        raise ApgRunnerError(
            f"real execution for runner {runner_type!r} is not connected yet"
            " — see plan.md §27 item 5"
        )
    return backend.execute(
        benchmark=benchmark,
        experiment=experiment,
        headless=headless,
        seed=seed,
    )


__all__ = [
    "ApgRunnerError",
    "RunnerOutcome",
    "KNOWN_DISPATCHED_RUNNERS",
    "KNOWN_FALLBACK_RUNNERS",
    "runner_dry_run",
    "runner_execute",
]
