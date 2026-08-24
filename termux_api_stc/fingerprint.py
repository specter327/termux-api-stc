"""Wrapper de `termux-fingerprint`."""
from .core import run


def scan():
    """
    Wraps `termux-fingerprint`.
    Solicita un escaneo de huella y devuelve JSON con 'auth_result',
    'errors' y 'failed_attempts'.
    """
    return run("termux-fingerprint")
