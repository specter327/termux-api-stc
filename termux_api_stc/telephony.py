"""Wrapper de `termux-telephony-call`, `termux-telephony-cellinfo`, `termux-telephony-deviceinfo`."""
from .core import run


def call(number: str):
    """Wraps `termux-telephony-call number`. Realiza una llamada (requiere permiso CALL_PHONE)."""
    return run("termux-telephony-call", [number], parse_json=False)


def cell_info():
    """Wraps `termux-telephony-cellinfo`. Devuelve info de las torres celulares cercanas."""
    return run("termux-telephony-cellinfo")


def device_info():
    """Wraps `termux-telephony-deviceinfo`. Devuelve info telefonica del dispositivo."""
    return run("termux-telephony-deviceinfo")
