"""Wrapper de `termux-speech-to-text`."""
from .core import run


def listen() -> str:
    """Wraps `termux-speech-to-text`. Devuelve el texto transcrito."""
    result = run("termux-speech-to-text", parse_json=False)
    return result or ""
