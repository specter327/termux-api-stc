"""Wrapper de `termux-infrared-frequencies` y `termux-infrared-transmit`."""
from typing import List
from .core import run
from .core import run_async


def frequencies():
    """Wraps `termux-infrared-frequencies`. Rangos de frecuencia IR soportados por el hardware."""
    return run("termux-infrared-frequencies")


def transmit(frequency: int, pattern: List[int]):
    """
    Wraps `termux-infrared-transmit -f frequency pattern`.
    :param frequency: frecuencia portadora en Hz
    :param pattern: lista de duraciones on/off en microsegundos, p.ej. [200,200,200,200]
    """
    args = ["-f", str(frequency), ",".join(str(p) for p in pattern)]
    return run("termux-infrared-transmit", args, parse_json=False)

# ==========
# Asynchronous API
# ==========
async def frequencies_async():
    """Wraps `termux-infrared-frequencies`. Rangos de frecuencia IR soportados por el hardware."""
    return await run_async("termux-infrared-frequencies")


async def transmit_async(frequency: int, pattern: List[int]):
    """
    Wraps `termux-infrared-transmit -f frequency pattern`.
    :param frequency: frecuencia portadora en Hz
    :param pattern: lista de duraciones on/off en microsegundos, p.ej. [200,200,200,200]
    """
    args = ["-f", str(frequency), ",".join(str(p) for p in pattern)]
    return await run_async("termux-infrared-transmit", args, parse_json=False)
