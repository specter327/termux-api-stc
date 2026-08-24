"""Wrapper de `termux-audio-info`."""
from .core import run
from .core import run_async


def info():
    """Wraps `termux-audio-info`. Devuelve parametros de audio del sistema (sample rate, etc.)."""
    return run("termux-audio-info")

# ==========
# Asynchronous API
# ==========
async def info_async():
    """Wraps `termux-audio-info`. Devuelve parametros de audio del sistema (sample rate, etc.)."""
    return await run_async("termux-audio-info")
