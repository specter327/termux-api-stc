"""Wrapper de `termux-tts-engines` y `termux-tts-speak`."""
from typing import Optional
from .core import run


def engines():
    """Wraps `termux-tts-engines`. Lista los motores de texto a voz disponibles."""
    return run("termux-tts-engines")


def speak(text: str, engine: Optional[str] = None, language: Optional[str] = None,
          region: Optional[str] = None, variant: Optional[str] = None,
          pitch: Optional[float] = None, rate: Optional[float] = None,
          stream: Optional[str] = None):
    """
    Wraps `termux-tts-speak [-e engine] [-l language] [-n region] [-v variant]
    [-p pitch] [-r rate] [-s stream] text`.
    """
    args = []
    if engine is not None:
        args += ["-e", engine]
    if language is not None:
        args += ["-l", language]
    if region is not None:
        args += ["-n", region]
    if variant is not None:
        args += ["-v", variant]
    if pitch is not None:
        args += ["-p", str(pitch)]
    if rate is not None:
        args += ["-r", str(rate)]
    if stream is not None:
        args += ["-s", stream]
    args.append(text)
    return run("termux-tts-speak", args, parse_json=False)
