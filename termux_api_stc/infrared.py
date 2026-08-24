"""Wrapper de `termux-infrared-frequencies` y `termux-infrared-transmit`."""
from typing import List
from .core import run


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
