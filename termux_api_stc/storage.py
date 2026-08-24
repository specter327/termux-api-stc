"""Wrapper de `termux-storage-get`."""
from .core import run


def get(output_file: str):
    """Wraps `termux-storage-get output_file`. Pide al usuario elegir un archivo a copiar."""
    return run("termux-storage-get", [output_file], parse_json=False)
