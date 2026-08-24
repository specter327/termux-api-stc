"""Wrapper de `termux-storage-get`."""
from .core import run
from .core import run_async


def get(output_file: str):
    """Wraps `termux-storage-get output_file`. Pide al usuario elegir un archivo a copiar."""
    return run("termux-storage-get", [output_file], parse_json=False)

# ==========
# Asynchronous API
# ==========
async def get_async(output_file: str):
    """Wraps `termux-storage-get output_file`. Pide al usuario elegir un archivo a copiar."""
    return await run_async("termux-storage-get", [output_file], parse_json=False)
