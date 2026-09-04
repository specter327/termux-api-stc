#!/usr/bin/env python3
"""
termux-api-stc — Uninstallation Console

Controlled uninstall of termux-api-stc from a selected Python environment.

Modes:
- check      : inspect whether the package is installed
- plan       : show uninstall plan
- uninstall  : uninstall and verify absence

Never removes the source repository. It only acts on the selected Python
environment through pip uninstall.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import venv
from pathlib import Path

APP_VERSION="1.0"
BOOTSTRAP_MARKER="TERMUX_API_STC_UNINSTALL_BOOTSTRAPPED"
RICH_AVAILABLE=False
try:
    from rich import box
    from rich.align import Align
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
    RICH_AVAILABLE=True
except Exception:
    Console=None  # type: ignore

class UninstallError(RuntimeError):pass

class UI:
    def __init__(self,enabled=True):
        self.enabled=enabled and RICH_AVAILABLE
        self.console=Console() if self.enabled else None
    def banner(self):
        if self.enabled:
            self.console.print(Panel(
                Align.center(Text.assemble(
                    Text("termux-api-stc",style="bold cyan"),"\n",
                    Text("Uninstallation Console",style="bold white"),"\n\n",
                    Text("Controlled removal • post-removal verification",style="green")
                )),border_style="cyan",box=box.ROUNDED))
        else:
            print("="*78);print("termux-api-stc — Uninstallation Console");print("="*78)
    def section(self,t):
        self.console.rule(f"[bold cyan]{t}[/bold cyan]") if self.enabled else print(f"\n{'='*78}\n{t}\n{'='*78}")
    def kv(self,rows):
        if self.enabled:
            t=Table(box=box.SIMPLE,show_header=False);t.add_column(style="bold");t.add_column()
            for k,v in rows:t.add_row(k,v)
            self.console.print(t)
        else:
            w=max((len(k) for k,_ in rows),default=0)
            for k,v in rows:print(f"{k:<{w}}  {v}")
    def ok(self,m):self.console.print(f"[green]✔[/green] {m}") if self.enabled else print(f"[ OK ] {m}")
    def fail(self,m):self.console.print(f"[bold red]✘ {m}[/bold red]") if self.enabled else print(f"[FAIL] {m}",file=sys.stderr)
    def info(self,m):self.console.print(f"[cyan]●[/cyan] {m}") if self.enabled else print(f"[INFO] {m}")
    def confirm(self,prompt,default=False):
        if self.enabled:return Confirm.ask(prompt,default=default)
        raw=input(f"{prompt} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
        if not raw:return default
        return raw in {"y","yes","s","si","sí"}
    def choose(self,prompt,choices,default):
        if self.enabled:return Prompt.ask(prompt,choices=list(choices),default=default)
        return input(f"{prompt} ({'/'.join(choices)}) [{default}]: ").strip() or default

UI_INSTANCE:UI

def detect_root(start):
    for c in (start,*start.parents):
        if (c/"pyproject.toml").is_file() and (c/"termux_api_stc").is_dir():return c
    return None

def bootstrap(argv,root):
    if os.environ.get(BOOTSTRAP_MARKER)=="1" or "--no-bootstrap" in argv:return
    if importlib.util.find_spec("rich") is not None:return
    base=(root or Path.cwd())/".uninstall-tools"
    py=base/("Scripts/python.exe" if os.name=="nt" else "bin/python")
    print("[BOOT] Preparing isolated uninstall UI tools...")
    if not py.exists():venv.EnvBuilder(with_pip=True).create(base)
    if subprocess.run([str(py),"-m","pip","install","--quiet","--upgrade","rich>=13.7"]).returncode!=0:raise SystemExit(1)
    env=os.environ.copy();env[BOOTSTRAP_MARKER]="1"
    os.execve(str(py),[str(py),str(Path(__file__).resolve()),*argv],env)

def query(py:Path):
    code=r