"""Wrapper de `termux-wifi-connectioninfo`, `termux-wifi-enable`, `termux-wifi-scaninfo`."""
from .core import run
from .core import run_async


def connection_info():
    """Wraps `termux-wifi-connectioninfo`. Info de la conexion Wi-Fi actual."""
    return run("termux-wifi-connectioninfo")


def enable(state: bool):
    """Wraps `termux-wifi-enable true|false`. Activa o desactiva el Wi-Fi."""
    return run("termux-wifi-enable", ["true" if state else "false"], parse_json=False)


def scan_info():
    """Wraps `termux-wifi-scaninfo`. Resultados del ultimo escaneo Wi-Fi."""
    return run("termux-wifi-scaninfo")

# ==========
# Asynchronous API
# ==========
async def connection_info_async():
    """Wraps `termux-wifi-connectioninfo`. Info de la conexion Wi-Fi actual."""
    return await run_async("termux-wifi-connectioninfo")


async def enable_async(state: bool):
    """Wraps `termux-wifi-enable true|false`. Activa o desactiva el Wi-Fi."""
    return await run_async("termux-wifi-enable", ["true" if state else "false"], parse_json=False)


async def scan_info_async():
    """Wraps `termux-wifi-scaninfo`. Resultados del ultimo escaneo Wi-Fi."""
    return await run_async("termux-wifi-scaninfo")
