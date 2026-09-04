from __future__ import annotations
from .core.command import Command
from .core.models import ExecutionResult

_COMMAND = Command("termux-fingerprint")


def authenticate(*, title: str | None = None, description: str | None = None, subtitle: str | None = None, cancel: str | None = None, timeout: float | None = 120.0) -> ExecutionResult:
    args: list[str] = []
    if title is not None:
        args.extend(("-t", title))
    if description is not None:
        args.extend(("-d", description))
    if subtitle is not None:
        args.extend(("-s", subtitle))
    if cancel is not None:
        args.extend(("-c", cancel))
    return _COMMAND.result(*args, timeout=timeout)

async def authenticate_async(*, title: str | None = None, description: str | None = None, subtitle: str | None = None, cancel: str | None = None, timeout: float | None = 120.0) -> ExecutionResult:
    args: list[str] = []
    if title is not None:
        args.extend(("-t", title))
    if description is not None:
        args.extend(("-d", description))
    if subtitle is not None:
        args.extend(("-s", subtitle))
    if cancel is not None:
        args.extend(("-c", cancel))
    return await _COMMAND.result_async(*args, timeout=timeout)
