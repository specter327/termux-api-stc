"""Wrapper de `termux-microphone-record`."""
from typing import Optional
from .core import run


def record(file: Optional[str] = None, limit_seconds: Optional[int] = None,
           encoder: Optional[str] = None, bitrate: Optional[int] = None,
           sample_rate: Optional[int] = None, channels: Optional[int] = None,
           background: bool = True):
    """
    Wraps `termux-microphone-record -f file [-l limit] [-e encoder] [-b bitrate]
    [-r rate] [-c channels] [-d]`.
    :param background: si True, agrega -d para ejecutar en segundo plano y
                        devolver el control de inmediato.
    """
    args = []
    if background:
        args.append("-d")
    if file is not None:
        args += ["-f", file]
    if limit_seconds is not None:
        args += ["-l", str(limit_seconds)]
    if encoder is not None:
        args += ["-e", encoder]
    if bitrate is not None:
        args += ["-b", str(bitrate)]
    if sample_rate is not None:
        args += ["-r", str(sample_rate)]
    if channels is not None:
        args += ["-c", str(channels)]
    return run("termux-microphone-record", args, parse_json=False)


def info():
    """Wraps `termux-microphone-record -i`. Estado de la grabacion actual."""
    return run("termux-microphone-record", ["-i"])


def quit():
    """Wraps `termux-microphone-record -q`. Detiene la grabacion en curso."""
    return run("termux-microphone-record", ["-q"], parse_json=False)
