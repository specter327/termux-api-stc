from __future__ import annotations
from pathlib import Path
from .core.command import Command
from .core.models import ExecutionResult

_COMMAND = Command("termux-wallpaper")


def from_file(file: str | Path, *, lockscreen: bool = False, timeout: float | None = 60.0) -> ExecutionResult:
    path = Path(file)
    if not path.is_file():
        raise ValueError(f"not a file: {path}")
    args: list[str] = []
    if lockscreen:
        args.append("-l")
    args.extend(("-f", str(path)))
    return _COMMAND.result(*args, timeout=timeout)


def from_url(url: str, *, lockscreen: bool = False, timeout: float | None = 60.0) -> ExecutionResult:
    if not url:
        raise ValueError("url must not be empty")
    args: list[str] = []
    if lockscreen:
        args.append("-l")
    args.extend(("-u", url))
    return _COMMAND.result(*args, timeout=timeout)

async def from_file_async(file: str | Path, *, lockscreen: bool = False, timeout: float | None = 60.0) -> ExecutionResult:
    path = Path(file)
    if not path.is_file():
        raise ValueError(f"not a file: {path}")
    args: list[str] = []
    if lockscreen:
        args.append("-l")
    args.extend(("-f", str(path)))
    return await _COMMAND.result_async(*args, timeout=timeout)


async def from_url_async(url: str, *, lockscreen: bool = False, timeout: float | None = 60.0) -> ExecutionResult:
    if not url:
        raise ValueError("url must not be empty")
    args: list[str] = []
    if lockscreen:
        args.append("-l")
    args.extend(("-u", url))
    return await _COMMAND.result_async(*args, timeout=timeout)
