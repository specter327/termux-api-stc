"""Wrapper de `termux-contact-list`."""
from .core import run


def list_contacts():
    """Wraps `termux-contact-list`. Devuelve lista de dicts {name, number}."""
    return run("termux-contact-list")
