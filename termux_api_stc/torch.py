"""Wrapper de `termux-torch`."""
from .core import run
from .core import run_async


def on():
    """Wraps `termux-torch on`. Enciende el flash de la camara."""
    return run("termux-torch", ["on"], parse_json=False)


def off():
    """Wraps `termux-torch off`. Apaga el flash de la camara."""
    return run("termux-torch", ["off"], parse_json=False)

# ==========
# Asynchronous API
# ==========
async def on_async():
    """Wraps `termux-torch on`. Enciende el flash de la camara."""
    return await run_async("termux-torch", ["on"], parse_json=False)


async def off_async():
    """Wraps `termux-torch off`. Apaga el flash de la camara."""
    return await run_async("termux-torch", ["off"], parse_json=False)
