from __future__ import annotations
from typing import Literal
from .core.command import Command

_COMMAND = Command("termux-brightness")
Brightness = int | Literal["auto"]


def _value(value: Brightness) -> str:
    if value == "auto":
        return "auto"
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("brightness must be int or 'auto'")
    if not 0 <= value <= 255:
        raise ValueError("brightness must be between 0 and 255")
    return str(value)


def set(value: Brightness, *, timeout: float | None = 15.0) -> str:
    return _COMMAND.text(_value(value), timeout=timeout)


async def set_async(value: Brightness, *, timeout: float | None = 15.0) -> str:
    return await _COMMAND.text_async(_value(value), timeout=timeout)
