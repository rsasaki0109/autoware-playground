from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ApgRunnerError(RuntimeError):
    pass


@dataclass
class RunnerOutcome:
    runner: str
    metrics: dict[str, Any] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)
    runtime_hints: dict[str, Any] = field(default_factory=dict)
