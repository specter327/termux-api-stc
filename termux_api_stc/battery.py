"""Wrapper de `termux-battery-status`."""
from .core import run
from .core import run_async


def status():
    """
    Wraps `termux-battery-status`.
    Devuelve un dict con: health, percentage, plugged, status, temperature, current.
    """
    return run("termux-battery-status")

# ==========
# Asynchronous API
# ==========
async def status_async():
    """
    Wraps `termux-battery-status`.
    Devuelve un dict con: health, percentage, plugged, status, temperature, current.
    """
    return await run_async("termux-battery-status")
