from __future__ import annotations

from .core.command import Command
from .core.models import ExecutionResult

_COMMAND = Command("termux-notification-channel")


def _nonempty(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def create(
    channel_id: str,
    channel_name: str,
    *,
    timeout: float | None = 15.0,
) -> ExecutionResult:
    """Create or rename an Android notification channel."""
    return _COMMAND.result(
        _nonempty("channel_id", channel_id),
        _nonempty("channel_name", channel_name),
        timeout=timeout,
    )


async def create_async(
    channel_id: str,
    channel_name: str,
    *,
    timeout: float | None = 15.0,
) -> ExecutionResult:
    return await _COMMAND.result_async(
        _nonempty("channel_id", channel_id),
        _nonempty("channel_name", channel_name),
        timeout=timeout,
    )


def delete(channel_id: str, *, timeout: float | None = 15.0) -> ExecutionResult:
    """Delete an Android notification channel."""
    return _COMMAND.result("-d", _nonempty("channel_id", channel_id), timeout=timeout)


async def delete_async(channel_id: str, *, timeout: float | None = 15.0) -> ExecutionResult:
    return await _COMMAND.result_async(
        "-d", _nonempty("channel_id", channel_id), timeout=timeout
    )
