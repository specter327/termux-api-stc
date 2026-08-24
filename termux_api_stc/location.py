"""Wrapper de `termux-location`."""
from .core import run


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
