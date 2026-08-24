"""Wrapper de `termux-fingerprint`."""
from .core import run
from .core import run_async


def scan():
    """
    Wraps `termux-fingerprint`.
    Solicita un escaneo de huella y devuelve JSON con 'auth_result',
    'errors' y 'failed_attempts'.
    """
    return run("termux-fingerprint")

# ==========
# Asynchronous API
# ==========
async def scan_async():
    """
    Wraps `termux-fingerprint`.
    Solicita un escaneo de huella y devuelve JSON con 'auth_result',
    'errors' y 'failed_attempts'.
    """
    return await run_async("termux-fingerprint")
