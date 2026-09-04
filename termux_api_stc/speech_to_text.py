from __future__ import annotations
from .core.command import Command

_COMMAND = Command("termux-speech-to-text")


def transcribe(*, timeout: float | None = 120.0) -> str:
    return _COMMAND.text(timeout=timeout)


async def transcribe_async(*, timeout: float | None = 120.0) -> str:
    return await _COMMAND.text_async(timeout=timeout)


def progress_lines(*, startup_timeout: float | None = 120.0):
    return _COMMAND.stream_lines("-p", startup_timeout=startup_timeout)
