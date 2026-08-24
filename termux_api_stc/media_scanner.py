"""Wrapper de `termux-media-scan`."""
from typing import List
from .core import run


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
