from __future__ import annotations

import os
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PreflightCheck:
    name: str
    ok: bool
    detail: str | None = None


@dataclass
class PreflightReport:
    runner: str | None
    checks: list[PreflightCheck] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "runner": self.runner,
            "ok": self.ok,
            "checks": [asdict(check) for check in self.checks],
        }


def _check_binary(name: str) -> PreflightCheck:
    path = shutil.which(name)
    if path:
        return PreflightCheck(name=name, ok=True, detail=path)
    return PreflightCheck(name=name, ok=False, detail=f"{name!r} not on PATH")


def _check_env(name: str, expected: str | None = None) -> PreflightCheck:
    value = os.environ.get(name)
    if value is None:
        return PreflightCheck(name=name, ok=False, detail=f"environment variable {name} is unset")
    if expected and value != expected:
        return PreflightCheck(
            name=name,
            ok=False,
            detail=f"{name}={value!r} does not match expected {expected!r}",
        )
    return PreflightCheck(name=name, ok=True, detail=value)


def _check_autoware_workspace(root: Path | None) -> PreflightCheck:
    candidates: list[Path] = []
    env_value = os.environ.get("AUTOWARE_WORKSPACE")
    if env_value:
        candidates.append(Path(env_value))
    if root is not None:
        candidates.append(root / "autoware")
    for candidate in candidates:
        if candidate.is_dir() and (candidate / "src").is_dir():
            return PreflightCheck(
                name="autoware_workspace",
                ok=True,
                detail=str(candidate),
            )
    return PreflightCheck(
        name="autoware_workspace",
        ok=False,
        detail=(
            "AUTOWARE_WORKSPACE is unset or does not contain a src/ tree."
            " Set it to your pinned Autoware workspace before non-dry-run execution."
        ),
    )


def base_checks(root: Path | None = None) -> list[PreflightCheck]:
    return [
        _check_env("ROS_DISTRO"),
        _check_binary("ros2"),
        _check_autoware_workspace(root),
    ]


def preflight_for_runner(runner_type: str, *, root: Path | None = None) -> PreflightReport:
    report = PreflightReport(runner=runner_type)
    report.checks.extend(base_checks(root))
    if runner_type == "scenario_simulator_v2":
        report.checks.append(_check_binary("scenario_test_runner"))
    elif runner_type == "rosbag_replay":
        report.checks.append(_check_binary("ros2"))
    elif runner_type in {"planning_simulator", "awsim"}:
        report.checks.append(
            PreflightCheck(
                name=runner_type,
                ok=False,
                detail=f"runner {runner_type!r} has no preflight handler yet",
            )
        )
    else:
        report.checks.append(
            PreflightCheck(
                name="runner",
                ok=False,
                detail=f"unknown runner {runner_type!r}",
            )
        )
    return report


def format_preflight_text(report: PreflightReport) -> str:
    lines = [f"runner: {report.runner}"]
    for check in report.checks:
        marker = "OK " if check.ok else "FAIL"
        detail = check.detail or ""
        lines.append(f"  [{marker}] {check.name}: {detail}")
    lines.append(f"result: {'pass' if report.ok else 'fail'}")
    return "\n".join(lines) + "\n"
