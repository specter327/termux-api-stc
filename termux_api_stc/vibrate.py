"""Wrapper de `termux-vibrate`."""
from typing import Optional
from .core import run
from .core import run_async


def vibrate(duration_ms: Optional[int] = None, force: bool = False):
    """Wraps `termux-vibrate [-d duration] [-f]`. Hace vibrar el dispositivo."""
    args = []
    if duration_ms is not None:
        args += ["-d", str(duration_ms)]
    if force:
        args.append("-f")
    return run("termux-vibrate", args, parse_json=False)

# ==========
# Asynchronous API
# ==========
async def vibrate_async(duration_ms: Optional[int] = None, force: bool = False):
    """Wraps `termux-vibrate [-d duration] [-f]`. Hace vibrar el dispositivo."""
    args = []
    if duration_ms is not None:
        args += ["-d", str(duration_ms)]
    if force:
        args.append("-f")
    return await run_async("termux-vibrate", args, parse_json=False)
