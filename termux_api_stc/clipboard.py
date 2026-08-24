"""Wrapper de `termux-clipboard-get` / `termux-clipboard-set`."""
from .core import run
from .core import run_async


def get() -> str:
    """Wraps `termux-clipboard-get`. Devuelve el texto del portapapeles."""
    result = run("termux-clipboard-get", parse_json=False)
    return result or ""


def set(text: str):
    """Wraps `termux-clipboard-set`. Escribe texto en el portapapeles via stdin."""
    return run("termux-clipboard-set", input_data=text, parse_json=False)

# ==========
# Asynchronous API
# ==========
async def get_async() -> str:
    """Wraps `termux-clipboard-get`. Devuelve el texto del portapapeles."""
    result = await run_async("termux-clipboard-get", parse_json=False)
    return result or ""


async def set_async(text: str):
    """Wraps `termux-clipboard-set`. Escribe texto en el portapapeles via stdin."""
    return await run_async("termux-clipboard-set", input_data=text, parse_json=False)
