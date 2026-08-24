"""Wrapper de `termux-battery-status`."""
from .core import run


def status():
    """
    Wraps `termux-battery-status`.
    Devuelve un dict con: health, percentage, plugged, status, temperature, current.
    """
    return run("termux-battery-status")
