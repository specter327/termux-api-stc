"""Wrapper de `termux-nfc` conforme al CLI oficial actual."""

from typing import Any, Optional

from .core import run

_VALID_READ_MODES = {"short", "full"}


def read(detail: str = "short") -> Any:
    """Lee una etiqueta NFC en modo short o full."""
    if detail not in _VALID_READ_MODES:
        raise ValueError("detail debe ser 'short' o 'full'")
    return run("termux-nfc", ["-r", detail])


def write(text: str) -> Any:
    """Escribe texto en una etiqueta NDEF."""
    return run("termux-nfc", ["-w", "-t", text])
