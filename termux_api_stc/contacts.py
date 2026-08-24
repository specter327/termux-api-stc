"""Wrapper de `termux-contact-list`."""
from .core import run
from .core import run_async


def list_contacts():
    """Wraps `termux-contact-list`. Devuelve lista de dicts {name, number}."""
    return run("termux-contact-list")

# ==========
# Asynchronous API
# ==========
async def list_contacts_async():
    """Wraps `termux-contact-list`. Devuelve lista de dicts {name, number}."""
    return await run_async("termux-contact-list")
