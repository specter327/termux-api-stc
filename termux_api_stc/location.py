"""Wrapper de `termux-location`."""
from .core import run
from .core import run_async
from .core import stream_text_async


def get(provider: str = "gps", request: str = "once"):
    """
    Wraps `termux-location [-p provider] [-r request]`.
    :param provider: 'gps', 'network' o 'passive'
    :param request: 'once', 'last' o 'updates'
    """
    if provider not in ("gps", "network", "passive"):
        raise ValueError("provider debe ser 'gps', 'network' o 'passive'")
    if request not in ("once", "last", "updates"):
        raise ValueError("request debe ser 'once', 'last' o 'updates'")
    args = ["-p", provider, "-r", request]
    timeout = None if request == "updates" else 30
    return run("termux-location", args, timeout=timeout)

# ==========
# Asynchronous API
# ==========
async def get_async(provider: str = "gps", request: str = "once"):
    """
    Wraps `termux-location [-p provider] [-r request]`.
    :param provider: 'gps', 'network' o 'passive'
    :param request: 'once', 'last' o 'updates'
    """
    if provider not in ("gps", "network", "passive"):
        raise ValueError("provider debe ser 'gps', 'network' o 'passive'")
    if request not in ("once", "last", "updates"):
        raise ValueError("request debe ser 'once', 'last' o 'updates'")
    args = ["-p", provider, "-r", request]
    timeout = None if request == "updates" else 30
    return await run_async("termux-location", args, timeout=timeout)

async def stream_updates(
    provider: str = "gps",
):
    """Transmite incrementalmente actualizaciones continuas de ubicacion."""
    if provider not in _PROVIDERS:
        raise ValueError("provider debe ser gps, network o passive")

    args = [
        "-p",
        provider,
        "-r",
        "updates",
    ]

    async for line in stream_text_async("termux-location", args):
        yield line

