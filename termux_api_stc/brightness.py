"""Wrapper de `termux-brightness`."""
from typing import Union
from .core import run
from .core import run_async


def set_brightness(level: Union[int, str]):
    """
    Wraps `termux-brightness <0-255|auto>`.
    :param level: entero 0-255, o el string "auto" para brillo automatico.
    """
    if isinstance(level, str):
        if level != "auto":
            raise ValueError("level debe ser int 0-255, o el string 'auto'")
        value = level
    else:
        if not (0 <= level <= 255):
            raise ValueError("level debe estar entre 0 y 255, o ser 'auto'")
        value = str(level)
    return run("termux-brightness", [value], parse_json=False)

# ==========
# Asynchronous API
# ==========
async def set_brightness_async(level: Union[int, str]):
    """
    Wraps `termux-brightness <0-255|auto>`.
    :param level: entero 0-255, o el string "auto" para brillo automatico.
    """
    if isinstance(level, str):
        if level != "auto":
            raise ValueError("level debe ser int 0-255, o el string 'auto'")
        value = level
    else:
        if not (0 <= level <= 255):
            raise ValueError("level debe estar entre 0 y 255, o ser 'auto'")
        value = str(level)
    return await run_async("termux-brightness", [value], parse_json=False)
