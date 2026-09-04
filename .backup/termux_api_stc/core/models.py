from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping

@dataclass(frozen=True, slots=True)
class ExecutionResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: bytes
    stderr: bytes
    duration: float

    @property
    def ok(self) -> bool:
        return self.returncode == 0

@dataclass(frozen=True, slots=True)
class EnvironmentReport:
    is_termux: bool
    prefix: str | None
    home: str | None
    android_release: str | None
    android_sdk: str | None
    commands: Mapping[str, bool]
