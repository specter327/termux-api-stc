"""Wrapper de `termux-telephony-call`, `termux-telephony-cellinfo`, `termux-telephony-deviceinfo`."""
from .core import run
from .core import run_async


def call(number: str):
    """Wraps `termux-telephony-call number`. Realiza una llamada (requiere permiso CALL_PHONE)."""
    return run("termux-telephony-call", [number], parse_json=False)


def cell_info():
    """Wraps `termux-telephony-cellinfo`. Devuelve info de las torres celulares cercanas."""
    return run("termux-telephony-cellinfo")


def device_info():
    """Wraps `termux-telephony-deviceinfo`. Devuelve info telefonica del dispositivo."""
    return run("termux-telephony-deviceinfo")

# ==========
# Asynchronous API
# ==========
async def call_async(number: str):
    """Wraps `termux-telephony-call number`. Realiza una llamada (requiere permiso CALL_PHONE)."""
    return await run_async("termux-telephony-call", [number], parse_json=False)


async def cell_info_async():
    """Wraps `termux-telephony-cellinfo`. Devuelve info de las torres celulares cercanas."""
    return await run_async("termux-telephony-cellinfo")


async def device_info_async():
    """Wraps `termux-telephony-deviceinfo`. Devuelve info telefonica del dispositivo."""
    return await run_async("termux-telephony-deviceinfo")
