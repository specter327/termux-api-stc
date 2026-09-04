from __future__ import annotations
from collections.abc import Sequence
from .core.command import Command
from .core.models import ExecutionResult

_COMMAND = Command("termux-sensor")


def list_available(*, timeout: float | None = 15.0):
    return _COMMAND.json("-l", timeout=timeout)


async def list_available_async(*, timeout: float | None = 15.0):
    return await _COMMAND.json_async("-l", timeout=timeout)


def cleanup(*, timeout: float | None = 15.0) -> ExecutionResult:
    return _COMMAND.result("-c", timeout=timeout)


async def cleanup_async(*, timeout: float | None = 15.0) -> ExecutionResult:
    return await _COMMAND.result_async("-c", timeout=timeout)


def _selection_args(*, sensors: str | Sequence[str] | None, all_sensors: bool, delay_ms: int | None, limit: int | None) -> tuple[str, ...]:
    if all_sensors and sensors is not None:
        raise ValueError("all_sensors and sensors are mutually exclusive")
    if not all_sensors and sensors is None:
        raise ValueError("select sensors or set all_sensors=True")
    args: list[str] = []
    if all_sensors:
        args.append("-a")
    else:
        if isinstance(sensors, str):
            selected = sensors
        else:
            selected = ",".join(sensors or ())
        if not selected:
            raise ValueError("sensors selection must not be empty")
        args.extend(("-s", selected))
    if delay_ms is not None:
        if isinstance(delay_ms, bool) or not isinstance(delay_ms, int) or delay_ms < 0:
            raise ValueError("delay_ms must be a non-negative integer")
        args.extend(("-d", str(delay_ms)))
    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be an integer >= 1")
        args.extend(("-n", str(limit)))
    return tuple(args)


def read_result(*, sensors: str | Sequence[str] | None = None, all_sensors: bool = False, delay_ms: int | None = None, limit: int = 1, timeout: float | None = 30.0) -> ExecutionResult:
    args = _selection_args(sensors=sensors, all_sensors=all_sensors, delay_ms=delay_ms, limit=limit)
    return _COMMAND.result(*args, timeout=timeout)


async def read_result_async(*, sensors: str | Sequence[str] | None = None, all_sensors: bool = False, delay_ms: int | None = None, limit: int = 1, timeout: float | None = 30.0) -> ExecutionResult:
    args = _selection_args(sensors=sensors, all_sensors=all_sensors, delay_ms=delay_ms, limit=limit)
    return await _COMMAND.result_async(*args, timeout=timeout)


def stream_lines(*, sensors: str | Sequence[str] | None = None, all_sensors: bool = False, delay_ms: int | None = None, startup_timeout: float | None = 30.0):
    args = _selection_args(sensors=sensors, all_sensors=all_sensors, delay_ms=delay_ms, limit=None)
    return _COMMAND.stream_lines(*args, startup_timeout=startup_timeout)
