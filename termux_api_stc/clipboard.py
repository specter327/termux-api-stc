"""Wrapper de `termux-clipboard-get` / `termux-clipboard-set`."""
from .core import run


def get() -> str:
    """Wraps `termux-clipboard-get`. Devuelve el texto del portapapeles."""
    result = run("termux-clipboard-get", parse_json=False)
    return result or ""


def set(text: str):
    """Wraps `termux-clipboard-set`. Escribe texto en el portapapeles via stdin."""
    return run("termux-clipboard-set", input_data=text, parse_json=False)
