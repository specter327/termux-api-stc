from .core.command import Command
_COMMAND = Command("termux-battery-status")
def status(*, timeout: float | None = 15.0):
    return _COMMAND.json(timeout=timeout)
async def status_async(*, timeout: float | None = 15.0):
    return await _COMMAND.json_async(timeout=timeout)
