from __future__ import annotations
from pathlib import Path
from typing import Literal
from .core.command import Command
from .core.models import ExecutionResult

_COMMAND = Command("termux-microphone-record")
Encoder = Literal["aac", "amr_wb", "amr_nb", "opus"]


def _record_args(*, file: str | Path | None, limit_seconds: int | None, encoder: Encoder | None, bitrate_kbps: int | None, sample_rate_hz: int | None, channels: int | None) -> tuple[str, ...]:
    args: list[str] = []
    if file is None and all(x is None for x in (limit_seconds, encoder, bitrate_kbps, sample_rate_hz, channels)):
        args.append("-d")
    if file is not None:
        args.extend(("-f", str(file)))
    if limit_seconds is not None:
        if limit_seconds < 0:
            raise ValueError("limit_seconds must be >= 0")
        args.extend(("-l", str(limit_seconds)))
    if encoder is not None:
        if encoder not in {"aac", "amr_wb", "amr_nb", "opus"}:
            raise ValueError(f"unsupported encoder: {encoder}")
        args.extend(("-e", encoder))
    if bitrate_kbps is not None:
        if bitrate_kbps <= 0:
            raise ValueError("bitrate_kbps must be > 0")
        args.extend(("-b", str(bitrate_kbps)))
    if sample_rate_hz is not None:
        if sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be > 0")
        args.extend(("-r", str(sample_rate_hz)))
    if channels is not None:
        if channels < 1:
            raise ValueError("channels must be >= 1")
        args.extend(("-c", str(channels)))
    return tuple(args)


def start(*, file: str | Path | None = None, limit_seconds: int | None = None, encoder: Encoder | None = None, bitrate_kbps: int | None = None, sample_rate_hz: int | None = None, channels: int | None = None, timeout: float | None = 30.0) -> ExecutionResult:
    return _COMMAND.result(*_record_args(file=file, limit_seconds=limit_seconds, encoder=encoder, bitrate_kbps=bitrate_kbps, sample_rate_hz=sample_rate_hz, channels=channels), timeout=timeout)


def info(*, timeout: float | None = 15.0) -> ExecutionResult:
    return _COMMAND.result("-i", timeout=timeout)


def stop(*, timeout: float | None = 15.0) -> ExecutionResult:
    return _COMMAND.result("-q", timeout=timeout)

async def start_async(*, file: str | Path | None = None, limit_seconds: int | None = None, encoder: Encoder | None = None, bitrate_kbps: int | None = None, sample_rate_hz: int | None = None, channels: int | None = None, timeout: float | None = 30.0) -> ExecutionResult:
    return await _COMMAND.result_async(*_record_args(file=file, limit_seconds=limit_seconds, encoder=encoder, bitrate_kbps=bitrate_kbps, sample_rate_hz=sample_rate_hz, channels=channels), timeout=timeout)


async def info_async(*, timeout: float | None = 15.0) -> ExecutionResult:
    return await _COMMAND.result_async("-i", timeout=timeout)


async def stop_async(*, timeout: float | None = 15.0) -> ExecutionResult:
    return await _COMMAND.result_async("-q", timeout=timeout)
