from __future__ import annotations
import os, stat, sys
from pathlib import Path
import pytest

@pytest.fixture
def fakebin(tmp_path: Path):
    bindir = tmp_path / "bin"
    bindir.mkdir()
    def make(name: str, body: str):
        path = bindir / name
        path.write_text(f"#!{sys.executable}\n" + body, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path
    return bindir, make

@pytest.fixture
def env_with(fakebin, monkeypatch):
    bindir, make = fakebin
    monkeypatch.setenv("PATH", str(bindir))
    return bindir, make
