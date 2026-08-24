"""Wrapper de `termux-download`."""
from typing import Optional
from .core import run
from .core import run_async


def download(url: str, title: Optional[str] = None, description: Optional[str] = None,
             path: Optional[str] = None):
    """
    Wraps `termux-download [-d description] [-t title] [-p path] url`.
    Encola una URL en el DownloadManager de Android.
    """
    args = []
    if description is not None:
        args += ["-d", description]
    if title is not None:
        args += ["-t", title]
    if path is not None:
        args += ["-p", path]
    args.append(url)
    return run("termux-download", args, parse_json=False)

# ==========
# Asynchronous API
# ==========
async def download_async(url: str, title: Optional[str] = None, description: Optional[str] = None,
             path: Optional[str] = None):
    """
    Wraps `termux-download [-d description] [-t title] [-p path] url`.
    Encola una URL en el DownloadManager de Android.
    """
    args = []
    if description is not None:
        args += ["-d", description]
    if title is not None:
        args += ["-t", title]
    if path is not None:
        args += ["-p", path]
    args.append(url)
    return await run_async("termux-download", args, parse_json=False)
