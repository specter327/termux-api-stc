"""Wrapper de `termux-sensor`."""

from typing import Any, List, Optional

from .core import run, run_text
from .core import run_async, run_text_async
from .core import stream_text_async


def list_sensors() -> Any:
    """Lista todos los sensores disponibles."""
    return run("termux-sensor", ["-l"])


def read(
    sensors: List[str],
    delay_ms: Optional[int] = None,
    limit: Optional[int] = None,
) -> Any:
    """Lee uno o mas sensores seleccionados."""
    if not sensors:
        raise ValueError("sensors no puede estar vacio")

    args = ["-s", ",".join(sensors)]
    if delay_ms is not None:
        args += ["-d", str(delay_ms)]
    if limit is not None:
        if limit < 1:
            raise ValueError("limit debe ser >= 1")
        args += ["-n", str(limit)]

    return run(
        "termux-sensor",
        args,
        timeout=None if limit is None else 60,
    )


def read_all(
    delay_ms: Optional[int] = None,
    limit: Optional[int] = None,
) -> Any:
    """Lee todos los sensores disponibles."""
    args = ["-a"]
    if delay_ms is not None:
        args += ["-d", str(delay_ms)]
    if limit is not None:
        if limit < 1:
            raise ValueError("limit debe ser >= 1")
        args += ["-n", str(limit)]

    return run(
        "termux-sensor",
        args,
        timeout=None if limit is None else 60,
    )


def cleanup() -> Optional[str]:
    """Libera listeners de sensores activos."""
    return run_text("termux-sensor", ["-c"])

# ==========
# Asynchronous API
# ==========
async def list_sensors_async() -> Any:
    """Lista todos los sensores disponibles."""
    return await run_async("termux-sensor", ["-l"])


async def read_async(
    sensors: List[str],
    delay_ms: Optional[int] = None,
    limit: Optional[int] = None,
) -> Any:
    """Lee uno o mas sensores seleccionados."""
    if not sensors:
        raise ValueError("sensors no puede estar vacio")

    args = ["-s", ",".join(sensors)]
    if delay_ms is not None:
        args += ["-d", str(delay_ms)]
    if limit is not None:
        if limit < 1:
            raise ValueError("limit debe ser >= 1")
        args += ["-n", str(limit)]

    return await run_async(
        "termux-sensor",
        args,
        timeout=None if limit is None else 60,
    )


async def read_all_async(
    delay_ms: Optional[int] = None,
    limit: Optional[int] = None,
) -> Any:
    """Lee todos los sensores disponibles."""
    args = ["-a"]
    if delay_ms is not None:
        args += ["-d", str(delay_ms)]
    if limit is not None:
        if limit < 1:
            raise ValueError("limit debe ser >= 1")
        args += ["-n", str(limit)]

    return await run_async(
        "termux-sensor",
        args,
        timeout=None if limit is None else 60,
    )


async def cleanup_async() -> Optional[str]:
    """Libera listeners de sensores activos."""
    return await run_text_async("termux-sensor", ["-c"])

async def stream(
    sensors: List[str],
    delay_ms: Optional[int] = None,
):
    """Transmite incrementalmente la salida de uno o mas sensores."""
    if not sensors:
        raise ValueError("sensors no puede estar vacio")

    args = ["-s", ",".join(sensors)]
    if delay_ms is not None:
        args += ["-d", str(delay_ms)]

    async for line in stream_text_async("termux-sensor", args):
        yield line


async def stream_all(
    delay_ms: Optional[int] = None,
):
    """Transmite incrementalmente la salida de todos los sensores."""
    args = ["-a"]
    if delay_ms is not None:
        args += ["-d", str(delay_ms)]

    async for line in stream_text_async("termux-sensor", args):
        yield line

