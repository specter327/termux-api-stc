"""Wrapper de `termux-speech-to-text`."""
from .core import run
from .core import run_async


def listen() -> str:
    """Wraps `termux-speech-to-text`. Devuelve el texto transcrito."""
    result = run("termux-speech-to-text", parse_json=False)
    return result or ""

# ==========
# Asynchronous API
# ==========
async def listen_async() -> str:
    """Wraps `termux-speech-to-text`. Devuelve el texto transcrito."""
    result = await run_async("termux-speech-to-text", parse_json=False)
    return result or ""
