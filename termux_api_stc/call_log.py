from __future__ import annotations
from .core.command import Command
from .core.models import ExecutionResult

_COMMAND = Command("termux-call-log")


def _args(limit: int, offset: int) -> tuple[str, ...]:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError("limit must be a non-negative integer")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    return ("-l", str(limit), "-o", str(offset))


def query(*, limit: int = 10, offset: int = 0, timeout: float | None = 15.0) -> ExecutionResult:
    return _COMMAND.result(*_args(limit, offset), timeout=timeout)


async def query_async(*, limit: int = 10, offset: int = 0, timeout: float | None = 15.0) -> ExecutionResult:
    return await _COMMAND.result_async(*_args(limit, offset), timeout=timeout)


def query_json(*, limit: int = 10, offset: int = 0, timeout: float | None = 15.0):
    return _COMMAND.json(*_args(limit, offset), timeout=timeout)


async def query_json_async(*, limit: int = 10, offset: int = 0, timeout: float | None = 15.0):
    return await _COMMAND.json_async(*_args(limit, offset), timeout=timeout)
