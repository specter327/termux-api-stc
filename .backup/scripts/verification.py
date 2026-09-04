#!/usr/bin/env python3
"""
termux-api-stc — Verification Console

Verify a local termux-api-stc installation and/or source checkout.

Checks:
- selected Python interpreter
- package importability
- distribution metadata/version
- import path
- source checkout metadata, when present
- pyproject/__version__/installed-version consistency
- package files inventory
- optional pip check
- optional unit tests
- optional Termux environment inspection
- evidence generation with SHA256
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import venv
from pathlib import Path

APP_VERSION="1.0"
BOOTSTRAP_MARKER="TERMUX_API_STC_VERIFY_BOOTSTRAPPED"

RICH_AVAILABLE=False
try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich.traceback import install as rich_traceback_install
    RICH_AVAILABLE=True
    rich_traceback_install(show_locals=False)
except Exception:
    Console=None  # type: ignore

class VerificationError(RuntimeError): pass

class UI:
    def __init__(self,enabled=True):
        self.enabled=enabled and RICH_AVAILABLE
        self.console=Console() if self.enabled else None
    def banner(self):
        if self.enabled:
            self.console.print(Panel(
                Align.center(Text.assemble(
                    Text("termux-api-stc",style="bold cyan"),"\n",
                    Text("Verification Console",style="bold white"),"\n\n",
                    Text("Installation integrity • metadata • environment",style="green")
                )),border_style="cyan",box=box.ROUNDED))
        else:
            print("="*78); print("termux-api-stc — Verification Console"); print("="*78)
    def section(self,t):
        self.console.rule(f"[bold cyan]{t}[/bold cyan]") if self.enabled else print(f"\n{'='*78}\n{t}\n{'='*78}")
    def ok(self,m): self.console.print(f"[green]✔[/green] {m}") if self.enabled else print(f"[ OK ] {m}")
    def warn(self,m): self.console.print(f"[yellow]▲[/yellow] {m}") if self.enabled else print(f"[WARN] {m}",file=sys.stderr)
    def fail(self,m): self.console.print(f"[bold red]✘ {m}[/bold red]") if self.enabled else print(f"[FAIL] {m}",file=sys.stderr)
    def info(self,m): self.console.print(f"[cyan]●[/cyan] {m}") if self.enabled else print(f"[INFO] {m}")
    def kv(self,rows):
        if self.enabled:
            t=Table(box=box.SIMPLE,show_header=False); t.add_column(style="bold"); t.add_column()
            for k,v in rows:t.add_row(k,v)
            self.console.print(t)
        else:
            w=max((len(k) for k,_ in rows),default=0)
            for k,v in rows:print(f"{k:<{w}}  {v}")

UI_INSTANCE:UI

def detect_root(start):
    for c in (start,*start.parents):
        if (c/"pyproject.toml").is_file() and (c/"termux_api_stc").is_dir(): return c
    return None

def bootstrap(argv,root):
    if os.environ.get(BOOTSTRAP_MARKER)=="1" or "--no-bootstrap" in argv:return
    if importlib.util.find_spec("rich") is not None:return
    base=(root or Path.cwd())/".verification-tools"
    py=base/("Scripts/python.exe" if os.name=="nt" else "bin/python")
    print("[BOOT] Preparing isolated verification UI tools...")
    if not py.exists(): venv.EnvBuilder(with_pip=True).create(base)
    if subprocess.run([str(py),"-m","pip","install","--quiet","--upgrade","rich>=13.7"]).returncode!=0: raise SystemExit(1)
    env=os.environ.copy();env[BOOTSTRAP_MARKER]="1"
    os.execve(str(py),[str(py),str(Path(__file__).resolve()),*argv],env)

def py_query(py:Path):
    code=r