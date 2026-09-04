from pathlib import Path
from .core.command import Command
_INFO = Command("termux-camera-info")
_PHOTO = Command("termux-camera-photo")

def info(*, timeout: float | None = 15.0):
    return _INFO.json(timeout=timeout)

async def info_async(*, timeout: float | None = 15.0):
    return await _INFO.json_async(timeout=timeout)

def photo(output_file: str | Path, *, camera_id: int = 0, timeout: float | None = 60.0) -> str:
    path = str(output_file)
    return _PHOTO.text("-c", str(camera_id), path, timeout=timeout)

async def photo_async(output_file: str | Path, *, camera_id: int = 0, timeout: float | None = 60.0) -> str:
    path = str(output_file)
    return await _PHOTO.text_async("-c", str(camera_id), path, timeout=timeout)
