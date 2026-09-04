from .core.command import Command
_COMMAND = Command("termux-torch")
def set(enabled: bool, *, timeout: float | None=15.0) -> str:
    return _COMMAND.text("on" if enabled else "off", timeout=timeout)
async def set_async(enabled: bool, *, timeout: float | None=15.0) -> str:
    return await _COMMAND.text_async("on" if enabled else "off", timeout=timeout)
