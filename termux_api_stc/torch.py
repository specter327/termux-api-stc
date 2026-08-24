"""Wrapper de `termux-torch`."""
from .core import run


def on():
    """Wraps `termux-torch on`. Enciende el flash de la camara."""
    return run("termux-torch", ["on"], parse_json=False)


def off():
    """Wraps `termux-torch off`. Apaga el flash de la camara."""
    return run("termux-torch", ["off"], parse_json=False)
