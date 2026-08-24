"""Wrapper de `termux-volume`."""
from .core import run

_STREAMS = {"alarm", "music", "notification", "ring", "system", "call"}


def get_all():
    """Wraps `termux-volume` sin argumentos. Devuelve info de volumen de todos los streams."""
    return run("termux-volume")


def set(stream: str, volume: int):
    """Wraps `termux-volume stream volume`. Ajusta el volumen del stream indicado."""
    if stream not in _STREAMS:
        raise ValueError(f"stream debe ser uno de {_STREAMS}")
    return run("termux-volume", [stream, str(volume)], parse_json=False)
