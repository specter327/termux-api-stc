"""Wrapper de `termux-call-log`."""
from typing import Optional
from .core import run


def call_log(limit: Optional[int] = None, offset: Optional[int] = None):
    """
    Wraps `termux-call-log [-l limit] [-o offset]`.
    Devuelve una lista de entradas del registro de llamadas.
    """
    args = []
    if limit is not None:
        args += ["-l", str(limit)]
    if offset is not None:
        args += ["-o", str(offset)]
    return run("termux-call-log", args)
