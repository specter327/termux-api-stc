"""Wrapper de `termux-wallpaper`."""
from typing import Optional
from .core import run
from .core import run_async


def set(file: Optional[str] = None, url: Optional[str] = None, lockscreen: bool = False):
    """
    Wraps `termux-wallpaper [-f file] [-u url] [-l]`.
    Establece el fondo de pantalla (o de bloqueo) desde un archivo local o URL.
    """
    args = []
    if file is not None:
        args += ["-f", file]
    if url is not None:
        args += ["-u", url]
    if lockscreen:
        args.append("-l")
    return run("termux-wallpaper", args, parse_json=False)

# ==========
# Asynchronous API
# ==========
async def set_async(file: Optional[str] = None, url: Optional[str] = None, lockscreen: bool = False):
    """
    Wraps `termux-wallpaper [-f file] [-u url] [-l]`.
    Establece el fondo de pantalla (o de bloqueo) desde un archivo local o URL.
    """
    args = []
    if file is not None:
        args += ["-f", file]
    if url is not None:
        args += ["-u", url]
    if lockscreen:
        args.append("-l")
    return await run_async("termux-wallpaper", args, parse_json=False)
