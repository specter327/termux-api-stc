from __future__ import annotations
from .core.command import Command
from .core.models import ExecutionResult

_COMMAND = Command("termux-toast")


def _args(*, background: str | None, color: str | None, gravity: str | None, short: bool) -> tuple[str, ...]:
    args: list[str] = []
    if short:
        args.append("-s")
    if color is not None:
        args.extend(("-c", color))
    if background is not None:
        args.extend(("-b", background))
    if gravity is not None:
        args.extend(("-g", gravity))
    return tuple(args)


def show(text: str, *, background: str | None = None, color: str | None = None, gravity: str | None = None, short: bool = False, timeout: float | None = 15.0) -> ExecutionResult:
    return _COMMAND.result(*_args(background=background, color=color, gravity=gravity, short=short), input=text.encode("utf-8"), timeout=timeout)


async def show_async(text: str, *, background: str | None = None, color: str | None = None, gravity: str | None = None, short: bool = False, timeout: float | None = 15.0) -> ExecutionResult:
    return await _COMMAND.result_async(*_args(background=background, color=color, gravity=gravity, short=short), input=text.encode("utf-8"), timeout=timeout)
