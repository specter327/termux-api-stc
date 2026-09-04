from .core.command import Command
_CONNECTION = Command("termux-wifi-connectioninfo")
_SCAN = Command("termux-wifi-scaninfo")
_ENABLE = Command("termux-wifi-enable")

def connection_info(*, timeout: float | None=15.0):
    return _CONNECTION.json(timeout=timeout)
async def connection_info_async(*, timeout: float | None=15.0):
    return await _CONNECTION.json_async(timeout=timeout)

def scan_info(*, timeout: float | None=30.0):
    return _SCAN.json(timeout=timeout)
async def scan_info_async(*, timeout: float | None=30.0):
    return await _SCAN.json_async(timeout=timeout)

def enable(enabled: bool, *, timeout: float | None=15.0) -> str:
    return _ENABLE.text("true" if enabled else "false", timeout=timeout)
async def enable_async(enabled: bool, *, timeout: float | None=15.0) -> str:
    return await _ENABLE.text_async("true" if enabled else "false", timeout=timeout)
