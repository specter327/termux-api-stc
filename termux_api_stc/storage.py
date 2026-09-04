from __future__ import annotations
from pathlib import Path
from .core.command import Command
from .core.models import ExecutionResult

_COMMAND = Command("termux-storage-get")


def get(output_file: str | Path, *, timeout: float | None = 120.0) -> ExecutionResult:
    return _COMMAND.result(str(output_file), timeout=timeout)


async def get_async(output_file: str | Path, *, timeout: float | None = 120.0) -> ExecutionResult:
    return await _COMMAND.result_async(str(output_file), timeout=timeout)
