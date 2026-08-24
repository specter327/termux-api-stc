"""Wrapper de `termux-job-scheduler` conforme al CLI oficial actual."""

from typing import Any, Optional

from .core import run, run_text
from .core import run_async, run_text_async

_VALID_NETWORKS = {"any", "unmetered", "cellular", "not_roaming", "none"}


def schedule(
    script: str,
    job_id: int,
    period_ms: Optional[int] = None,
    network: Optional[str] = None,
    persisted: Optional[bool] = None,
    battery_not_low: Optional[bool] = None,
    charging: Optional[bool] = None,
    storage_not_low: Optional[bool] = None,
    trigger_content_uri: Optional[str] = None,
    trigger_content_flag: Optional[int] = None,
) -> Optional[str]:
    """Programa un script mediante Android JobScheduler."""
    if network is not None and network not in _VALID_NETWORKS:
        raise ValueError("network debe ser uno de: {}".format(sorted(_VALID_NETWORKS)))
    if period_ms is not None and period_ms < 0:
        raise ValueError("period_ms no puede ser negativo")

    args = ["-s", script, "--job-id", str(job_id)]

    if period_ms is not None:
        args += ["--period-ms", str(period_ms)]
    if network is not None:
        args += ["--network", network]

    for flag, value in (
        ("--persisted", persisted),
        ("--battery-not-low", battery_not_low),
        ("--charging", charging),
        ("--storage-not-low", storage_not_low),
    ):
        if value is not None:
            args += [flag, "true" if value else "false"]

    if trigger_content_uri is not None:
        args += ["--trigger-content-uri", trigger_content_uri]
    if trigger_content_flag is not None:
        args += ["--trigger-content-flag", str(trigger_content_flag)]

    return run_text("termux-job-scheduler", args)


def cancel(job_id: int) -> Optional[str]:
    """Cancela un trabajo programado por identificador."""
    return run_text(
        "termux-job-scheduler",
        ["--cancel", "--job-id", str(job_id)],
    )


def cancel_all() -> Optional[str]:
    """Cancela todos los trabajos programados."""
    return run_text("termux-job-scheduler", ["--cancel-all"])


def pending() -> Any:
    """Lista los trabajos pendientes."""
    return run("termux-job-scheduler", ["--pending"])

# ==========
# Asynchronous API
# ==========
async def schedule_async(
    script: str,
    job_id: int,
    period_ms: Optional[int] = None,
    network: Optional[str] = None,
    persisted: Optional[bool] = None,
    battery_not_low: Optional[bool] = None,
    charging: Optional[bool] = None,
    storage_not_low: Optional[bool] = None,
    trigger_content_uri: Optional[str] = None,
    trigger_content_flag: Optional[int] = None,
) -> Optional[str]:
    """Programa un script mediante Android JobScheduler."""
    if network is not None and network not in _VALID_NETWORKS:
        raise ValueError("network debe ser uno de: {}".format(sorted(_VALID_NETWORKS)))
    if period_ms is not None and period_ms < 0:
        raise ValueError("period_ms no puede ser negativo")

    args = ["-s", script, "--job-id", str(job_id)]

    if period_ms is not None:
        args += ["--period-ms", str(period_ms)]
    if network is not None:
        args += ["--network", network]

    for flag, value in (
        ("--persisted", persisted),
        ("--battery-not-low", battery_not_low),
        ("--charging", charging),
        ("--storage-not-low", storage_not_low),
    ):
        if value is not None:
            args += [flag, "true" if value else "false"]

    if trigger_content_uri is not None:
        args += ["--trigger-content-uri", trigger_content_uri]
    if trigger_content_flag is not None:
        args += ["--trigger-content-flag", str(trigger_content_flag)]

    return await run_text_async("termux-job-scheduler", args)


async def cancel_async(job_id: int) -> Optional[str]:
    """Cancela un trabajo programado por identificador."""
    return await run_text_async(
        "termux-job-scheduler",
        ["--cancel", "--job-id", str(job_id)],
    )


async def cancel_all_async() -> Optional[str]:
    """Cancela todos los trabajos programados."""
    return await run_text_async("termux-job-scheduler", ["--cancel-all"])


async def pending_async() -> Any:
    """Lista los trabajos pendientes."""
    return await run_async("termux-job-scheduler", ["--pending"])
