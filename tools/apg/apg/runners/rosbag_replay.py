from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path
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


_ENV_REF = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?")


def _expand_env(value: str) -> str:
    def replace(match: "re.Match[str]") -> str:
        return os.environ.get(match.group(1), match.group(0))

    return _ENV_REF.sub(replace, value)


def _resolve_rosbag(benchmark: dict[str, Any]) -> Path:
    runner_cfg = benchmark.get("runner", {}) or {}
    raw = runner_cfg.get("rosbag")
    if not isinstance(raw, str):
        raise ApgRunnerError(
            "rosbag_replay: benchmark.runner.rosbag is required but missing"
        )
    expanded = _expand_env(raw)
    if "$" in expanded:
        raise ApgRunnerError(
            f"rosbag_replay: rosbag path still contains unresolved variables: {expanded!r}."
            " Set $APG_DATA (or the referenced env vars) before non-dry-run execution."
        )
    path = Path(expanded).expanduser()
    if not path.exists():
        raise ApgRunnerError(
            f"rosbag_replay: rosbag not found at {path}."
            " Download or generate the bag before running."
        )
    return path


def _ros2_bag_info(bag: Path) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(bag)}
    try:
        proc = subprocess.run(
            ["ros2", "bag", "info", str(bag)],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise ApgRunnerError("rosbag_replay: `ros2` not on PATH") from exc
    info["info_returncode"] = proc.returncode
    if proc.returncode != 0:
        info["info_stderr"] = proc.stderr.strip()
        return info
    duration_sec: float | None = None
    message_count: int | None = None
    topic_count = 0
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("Duration:"):
            match = re.search(r"([0-9]+(?:\.[0-9]+)?)", stripped)
            if match:
                duration_sec = float(match.group(1))
        elif stripped.startswith("Messages:"):
            match = re.search(r"([0-9]+)", stripped)
            if match:
                message_count = int(match.group(1))
        elif "Topic:" in stripped and "Type:" in stripped:
            topic_count += 1
    info["duration_sec"] = duration_sec
    info["message_count"] = message_count
    info["topic_count"] = topic_count or None
    return info


def execute(
    *,
    benchmark: dict[str, Any],
    experiment: dict[str, Any],
    headless: bool,
    seed: int | None,
) -> RunnerOutcome:
    if not shutil.which("ros2"):
        raise ApgRunnerError("rosbag_replay: `ros2` not on PATH")
    bag = _resolve_rosbag(benchmark)
    runner_cfg = benchmark.get("runner", {}) or {}
    timeout_sec = runner_cfg.get("timeout_sec")

    info = _ros2_bag_info(bag)

    started = time.monotonic()
    try:
        proc = subprocess.run(
            ["ros2", "bag", "play", str(bag)],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_sec if timeout_sec else None,
        )
        play_returncode = proc.returncode
        play_stderr = proc.stderr.strip()
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        play_returncode = None
        play_stderr = f"timed out after {exc.timeout}s"
        timed_out = True
    elapsed_sec = time.monotonic() - started

    failures: list[str] = []
    if timed_out:
        failures.append("sim_invalid")
    elif play_returncode != 0:
        failures.append("sim_invalid")

    metrics: dict[str, Any] = {
        "rosbag_duration_sec": info.get("duration_sec"),
        "rosbag_message_count": info.get("message_count"),
        "rosbag_topic_count": info.get("topic_count"),
        "play_returncode": play_returncode,
        "play_elapsed_sec": round(elapsed_sec, 3),
        "play_timed_out": timed_out,
    }
    gates = benchmark.get("gates", {}) or {}
    for group in ("required", "diagnostic"):
        for gate in gates.get(group, []) or []:
            metrics.setdefault(gate.get("name"), None)

    runtime_hints = {
        "backend": "rosbag_replay",
        "dispatched": True,
        "executed": True,
        "headless": headless,
        "rosbag": str(bag),
        "timeout_sec": timeout_sec,
        "experiment_mode": experiment.get("mode"),
        "seed": seed,
        "play_stderr_tail": play_stderr[-400:] if play_stderr else None,
    }
    return RunnerOutcome(
        runner="rosbag_replay",
        metrics=metrics,
        failures=failures,
        runtime_hints=runtime_hints,
    )
