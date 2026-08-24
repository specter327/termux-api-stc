"""Wrapper de `termux-camera-info` y `termux-camera-photo`."""
from typing import Optional
from .core import run
from .core import run_async


def info():
    """Wraps `termux-camera-info`. Devuelve lista de dicts con info de cada camara."""
    return run("termux-camera-info")


def photo(output_file: str, camera_id: Optional[str] = "0"):
    """
    Wraps `termux-camera-photo [-c camera_id] output_file`.
    Captura una foto con la camara indicada y la guarda en output_file.
    """
    args = []
    if camera_id is not None:
        args += ["-c", str(camera_id)]
    args.append(output_file)
    return run("termux-camera-photo", args, parse_json=False)

# ==========
# Asynchronous API
# ==========
async def info_async():
    """Wraps `termux-camera-info`. Devuelve lista de dicts con info de cada camara."""
    return await run_async("termux-camera-info")


async def photo_async(output_file: str, camera_id: Optional[str] = "0"):
    """
    Wraps `termux-camera-photo [-c camera_id] output_file`.
    Captura una foto con la camara indicada y la guarda en output_file.
    """
    args = []
    if camera_id is not None:
        args += ["-c", str(camera_id)]
    args.append(output_file)
    return await run_async("termux-camera-photo", args, parse_json=False)
