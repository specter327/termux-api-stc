from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class PayloadState(str, Enum):
    EMPTY = "EMPTY"
    NONEMPTY = "NONEMPTY"


class CapabilityState(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    PERMISSION_REQUIRED = "PERMISSION_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


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

    @property
    def payload_state(self) -> PayloadState:
        return PayloadState.NONEMPTY if self.stdout else PayloadState.EMPTY

    @property
    def has_stdout(self) -> bool:
        return bool(self.stdout)

    @property
    def has_stderr(self) -> bool:
        return bool(self.stderr)


@dataclass(frozen=True, slots=True)
class CapabilityObservation:
    command: str
    command_available: bool
    state: CapabilityState
    evidence: str
    result: ExecutionResult | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentReport:
    is_termux: bool
    prefix: str | None
    home: str | None
    android_release: str | None
    android_sdk: str | None
    device_manufacturer: str | None
    device_model: str | None
    device_name: str | None
    device_abi: str | None
    termux_version: str | None
    termux_api_package_version: str | None
    commands: Mapping[str, bool]
