from __future__ import annotations
from pathlib import Path
from typing import Literal
from .core.command import Command
from .core.models import ExecutionResult

_COMMAND = Command("termux-share")
Action = Literal["edit", "send", "view"]


def _args(*, action: Action, content_type: str | None, default_receiver: bool, title: str | None) -> list[str]:
    if action not in {"edit", "send", "view"}:
        raise ValueError(f"unsupported action: {action}")
    args = ["-a", action]
    if content_type is not None:
        args.extend(("-c", content_type))
    if default_receiver:
        args.append("-d")
    if title is not None:
        args.extend(("-t", title))
    return args


def share_text(text: str, *, action: Action = "view", content_type: str | None = None, default_receiver: bool = False, title: str | None = None, timeout: float | None = 30.0) -> ExecutionResult:
    args = _args(action=action, content_type=content_type, default_receiver=default_receiver, title=title)
    return _COMMAND.result(*args, input=text.encode("utf-8"), timeout=timeout)


def share_file(file: str | Path, *, action: Action = "view", content_type: str | None = None, default_receiver: bool = False, title: str | None = None, timeout: float | None = 30.0) -> ExecutionResult:
    path = Path(file)
    if not path.is_file():
        raise ValueError(f"not a file: {path}")
    args = _args(action=action, content_type=content_type, default_receiver=default_receiver, title=title)
    args.append(str(path))
    return _COMMAND.result(*args, timeout=timeout)

async def share_text_async(text: str, *, action: Action = "view", content_type: str | None = None, default_receiver: bool = False, title: str | None = None, timeout: float | None = 30.0) -> ExecutionResult:
    args = _args(action=action, content_type=content_type, default_receiver=default_receiver, title=title)
    return await _COMMAND.result_async(*args, input=text.encode("utf-8"), timeout=timeout)


async def share_file_async(file: str | Path, *, action: Action = "view", content_type: str | None = None, default_receiver: bool = False, title: str | None = None, timeout: float | None = 30.0) -> ExecutionResult:
    path = Path(file)
    if not path.is_file():
        raise ValueError(f"not a file: {path}")
    args = _args(action=action, content_type=content_type, default_receiver=default_receiver, title=title)
    args.append(str(path))
    return await _COMMAND.result_async(*args, timeout=timeout)
