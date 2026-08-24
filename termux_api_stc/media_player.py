"""Wrapper de `termux-media-player`."""
from typing import Optional
from .core import run


def play(file: Optional[str] = None):
    """Wraps `termux-media-player play [file]`. Reanuda o inicia la reproduccion."""
    args = ["play"] + ([file] if file else [])
    return run("termux-media-player", args, parse_json=False)


def pause():
    """Wraps `termux-media-player pause`."""
    return run("termux-media-player", ["pause"], parse_json=False)


def stop():
    """Wraps `termux-media-player stop`."""
    return run("termux-media-player", ["stop"], parse_json=False)


def player_info():
    """Wraps `termux-media-player info`. Devuelve el estado actual de reproduccion."""
    return run("termux-media-player", ["info"], parse_json=False)
