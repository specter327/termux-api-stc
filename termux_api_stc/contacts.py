from __future__ import annotations
from .core.command import Command
from .core.models import ExecutionResult

_COMMAND = Command("termux-contact-list")


def list_result(*, timeout: float | None = 15.0) -> ExecutionResult:
    return _COMMAND.result(timeout=timeout)


async def list_result_async(*, timeout: float | None = 15.0) -> ExecutionResult:
    return await _COMMAND.result_async(timeout=timeout)


def list_json(*, timeout: float | None = 15.0):
    return _COMMAND.json(timeout=timeout)


async def list_json_async(*, timeout: float | None = 15.0):
    return await _COMMAND.json_async(timeout=timeout)
