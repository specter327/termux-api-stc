"""Wrapper de `termux-media-scan`."""
from typing import List
from .core import run
from .core import run_async


def scan(files: List[str], recursive: bool = False, verbose: bool = False):
    """
    Wraps `termux-media-scan [-r] [-v] file...`.
    Anade archivos al indice MediaStore de Android.
    """
    args = []
    if recursive:
        args.append("-r")
    if verbose:
        args.append("-v")
    args += files
    return run("termux-media-scan", args, parse_json=False)

# ==========
# Asynchronous API
# ==========
async def scan_async(files: List[str], recursive: bool = False, verbose: bool = False):
    """
    Wraps `termux-media-scan [-r] [-v] file...`.
    Anade archivos al indice MediaStore de Android.
    """
    args = []
    if recursive:
        args.append("-r")
    if verbose:
        args.append("-v")
    args += files
    return await run_async("termux-media-scan", args, parse_json=False)
