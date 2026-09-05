from __future__ import annotations
from collections.abc import Sequence
from .core.command import Command
from .core.models import ExecutionResult

_FREQ = Command("termux-infrared-frequencies")
_TX = Command("termux-infrared-transmit")


def frequencies(*, timeout: float | None = 15.0) -> ExecutionResult:
    return _FREQ.result(timeout=timeout)


async def frequencies_async(*, timeout: float | None = 15.0) -> ExecutionResult:
    return await _FREQ.result_async(timeout=timeout)


def frequencies_json(*, timeout: float | None = 15.0):
    return _FREQ.json_if_present(timeout=timeout)


def _pattern(value: str | Sequence[int]) -> str:
    if isinstance(value, str):
        if not value:
            raise ValueError("pattern must not be empty")
        return value
    items = list(value)
    if not items:
        raise ValueError("pattern must not be empty")
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in items):
        raise ValueError("pattern intervals must be non-negative integers")
    return ",".join(str(x) for x in items)


def transmit(frequency_hz: int, pattern: str | Sequence[int], *, timeout: float | None = 15.0) -> ExecutionResult:
    if isinstance(frequency_hz, bool) or not isinstance(frequency_hz, int) or frequency_hz <= 0:
        raise ValueError("frequency_hz must be a positive integer")
    return _TX.result("-f", str(frequency_hz), _pattern(pattern), timeout=timeout)


async def transmit_async(frequency_hz: int, pattern: str | Sequence[int], *, timeout: float | None = 15.0) -> ExecutionResult:
    if isinstance(frequency_hz, bool) or not isinstance(frequency_hz, int) or frequency_hz <= 0:
        raise ValueError("frequency_hz must be a positive integer")
    return await _TX.result_async("-f", str(frequency_hz), _pattern(pattern), timeout=timeout)

async def frequencies_json_async(*, timeout: float | None = 15.0):
    return await _FREQ.json_if_present_async(timeout=timeout)
