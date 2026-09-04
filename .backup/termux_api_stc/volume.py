from .core.command import Command
_COMMAND = Command("termux-volume")
def get_all(*, timeout: float | None=15.0):
    return _COMMAND.json(timeout=timeout)
async def get_all_async(*, timeout: float | None=15.0):
    return await _COMMAND.json_async(timeout=timeout)
def set(stream: str, volume: int, *, timeout: float | None=15.0) -> str:
    if volume < 0:
        raise ValueError("volume must be >= 0")
    return _COMMAND.text(stream, str(volume), timeout=timeout)
async def set_async(stream: str, volume: int, *, timeout: float | None=15.0) -> str:
    if volume < 0:
        raise ValueError("volume must be >= 0")
    return await _COMMAND.text_async(stream, str(volume), timeout=timeout)
