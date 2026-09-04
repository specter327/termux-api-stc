from .core.command import Command
_CALL = Command("termux-telephony-call")
_CELL = Command("termux-telephony-cellinfo")
_DEVICE = Command("termux-telephony-deviceinfo")

def call(number: str, *, timeout: float | None=15.0) -> str:
    return _CALL.text(number, timeout=timeout)
async def call_async(number: str, *, timeout: float | None=15.0) -> str:
    return await _CALL.text_async(number, timeout=timeout)

def cell_info(*, timeout: float | None=15.0):
    return _CELL.json(timeout=timeout)
async def cell_info_async(*, timeout: float | None=15.0):
    return await _CELL.json_async(timeout=timeout)

def device_info(*, timeout: float | None=15.0):
    return _DEVICE.json(timeout=timeout)
async def device_info_async(*, timeout: float | None=15.0):
    return await _DEVICE.json_async(timeout=timeout)
