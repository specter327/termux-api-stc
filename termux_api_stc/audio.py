"""Wrapper de `termux-audio-info`."""
from .core import run


def info():
    """Wraps `termux-audio-info`. Devuelve parametros de audio del sistema (sample rate, etc.)."""
    return run("termux-audio-info")
