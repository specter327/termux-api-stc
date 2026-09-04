from .core.command import Command
_COMMAND = Command("termux-audio-info")
def info(*, timeout: float | None = 15.0):
    return _COMMAND.json(timeout=timeout)
async def info_async(*, timeout: float | None = 15.0):
    return await _COMMAND.json_async(timeout=timeout)
