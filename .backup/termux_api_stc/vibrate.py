from .core.command import Command
_COMMAND = Command("termux-vibrate")
def vibrate(duration_ms: int=1000, *, force: bool=False, timeout: float | None=15.0) -> str:
    if duration_ms < 0:
        raise ValueError("duration_ms must be >= 0")
    args=["-d",str(duration_ms)]
    if force: args.append("-f")
    return _COMMAND.text(*args, timeout=timeout)
async def vibrate_async(duration_ms: int=1000, *, force: bool=False, timeout: float | None=15.0) -> str:
    if duration_ms < 0:
        raise ValueError("duration_ms must be >= 0")
    args=["-d",str(duration_ms)]
    if force: args.append("-f")
    return await _COMMAND.text_async(*args, timeout=timeout)
