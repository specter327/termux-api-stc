from __future__ import annotations
import os
import pytest


def _is_termux() -> bool:
    prefix = os.environ.get("PREFIX", "")
    return bool(prefix and "com.termux" in prefix)


def pytest_collection_modifyitems(config, items):
    if _is_termux():
        return
    skip = pytest.mark.skip(reason="requires real Termux environment")
    for item in items:
        if item.get_closest_marker("device"):
            item.add_marker(skip)
