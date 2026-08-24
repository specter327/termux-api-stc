"""Wrapper de `termux-toast`."""
from typing import Optional
from .core import run
from .core import run_async


def show(text: str, background: Optional[str] = None, text_color: Optional[str] = None,
          gravity: Optional[str] = None, short: bool = False):
    """
    Wraps `termux-toast [-b background] [-c textcolor] [-g gravity] [-s] text`.
    :param gravity: 'top', 'middle' o 'bottom'
    """
    args = []
    if background is not None:
        args += ["-b", background]
    if text_color is not None:
        args += ["-c", text_color]
    if gravity is not None:
        args += ["-g", gravity]
    if short:
        args.append("-s")
    args.append(text)
    return run("termux-toast", args, parse_json=False)

# ==========
# Asynchronous API
# ==========
async def show_async(text: str, background: Optional[str] = None, text_color: Optional[str] = None,
          gravity: Optional[str] = None, short: bool = False):
    """
    Wraps `termux-toast [-b background] [-c textcolor] [-g gravity] [-s] text`.
    :param gravity: 'top', 'middle' o 'bottom'
    """
    args = []
    if background is not None:
        args += ["-b", background]
    if text_color is not None:
        args += ["-c", text_color]
    if gravity is not None:
        args += ["-g", gravity]
    if short:
        args.append("-s")
    args.append(text)
    return await run_async("termux-toast", args, parse_json=False)
