"""Wrapper de `termux-sensor`."""

from typing import Any, List, Optional

from .core import run, run_text


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
