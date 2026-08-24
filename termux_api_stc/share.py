"""Wrapper de `termux-share`."""
from typing import Optional
from .core import run


def share(file: str, action: str = "send", content_type: Optional[str] = None,
          title: Optional[str] = None, default_receiver: bool = False):
    """
    Wraps `termux-share [-a action] [-c content-type] [-d] [-t title] file`.
    :param action: 'send', 'view' o 'edit'
    """
    args = ["-a", action]
    if content_type is not None:
        args += ["-c", content_type]
    if default_receiver:
        args.append("-d")
    if title is not None:
        args += ["-t", title]
    args.append(file)
    return run("termux-share", args, parse_json=False)
