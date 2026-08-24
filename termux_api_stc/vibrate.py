"""Wrapper de `termux-vibrate`."""
from typing import Optional
from .core import run


def vibrate(duration_ms: Optional[int] = None, force: bool = False):
    """Wraps `termux-vibrate [-d duration] [-f]`. Hace vibrar el dispositivo."""
    args = []
    if duration_ms is not None:
        args += ["-d", str(duration_ms)]
    if force:
        args.append("-f")
    return run("termux-vibrate", args, parse_json=False)
