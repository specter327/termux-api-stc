#!/usr/bin/env python3
"""
termux-api-stc — Installation Console

Install termux-api-stc in a controlled, auditable way.

Supported sources:
- PyPI
- TestPyPI
- local source checkout
- editable local checkout
- local wheel

Modes:
- check      : validate install prerequisites and selected source
- plan       : show the exact installation plan without installing
- install    : install and verify

The script can be used interactively or in CI.
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
import tempfile
import venv
from pathlib import Path
from typing import Sequence

APP_VERSION = "1.0"
EXPECTED_PROJECT = "termux-api-stc"
BOOTSTRAP_MARKER = "TERMUX_API_STC_INSTALL_BOOTSTRAPPED"

RICH_AVAILABLE = False
try:
    from rich import box
    from rich.align import Align
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
    from rich.traceback import install as rich_traceback_install
    RICH_AVAILABLE = True
    rich_traceback_install(show_locals=False)
except Exception:
    Console = None  # type: ignore[assignment]


class InstallError(RuntimeError):
    pass


@dataclasses.dataclass(slots=True)
class Config:
    mode: str
    source: str
    project_root: Path | None
    wheel: Path | None
    version: str | None
    python: Path
    user: bool = False
    force: bool = False
    upgrade: bool = False
    no_deps: bool = False
    dry_run: bool = False
    yes: bool = False
    no_ui: bool = False
    no_bootstrap: bool = False
    verify: bool = True


class UI:
    def __init__(self, enabled=True):
        self.enabled = enabled and RICH_AVAILABLE
        self.console = Console() if self.enabled else None

    def banner(self):
        if self.enabled:
            body = Text("Controlled installation • verification • evidence", style="green")
            self.console.print(Panel(
                Align.center(Text.assemble(
                    Text("termux-api-stc", style="bold cyan"), "\n",
                    Text("Installation Console", style="bold white"), "\n\n",
                    body
                )),
                border_style="cyan", box=box.ROUNDED
            ))
        else:
            print("="*78)
            print("termux-api-stc — Installation Console")
            print("="*78)

    def section(self, t):
        if self.enabled:
            self.console.rule(f"[bold cyan]{t}[/bold cyan]")
        else:
            print("\n"+"="*78); print(t); print("="*78)

    def info(self, m):
        self.console.print(f"[cyan]●[/cyan] {m}") if self.enabled else print(f"[INFO] {m}")

    def ok(self, m):
        self.console.print(f"[green]✔[/green] {m}") if self.enabled else print(f"[ OK ] {m}")

    def warn(self, m):
        self.console.print(f"[yellow]▲[/yellow] {m}") if self.enabled else print(f"[WARN] {m}", file=sys.stderr)

    def fail(self, m):
        self.console.print(f"[bold red]✘ {m}[/bold red]") if self.enabled else print(f"[FAIL] {m}", file=sys.stderr)

    def kv(self, rows):
        if self.enabled:
            t = Table(box=box.SIMPLE, show_header=False)
            t.add_column(style="bold"); t.add_column()
            for k,v in rows: t.add_row(k,v)
            self.console.print(t)
        else:
            w=max((len(k) for k,_ in rows), default=0)
            for k,v in rows: print(f"{k:<{w}}  {v}")

    def choose(self, prompt, choices, default):
        if self.enabled:
            return Prompt.ask(prompt, choices=list(choices), default=default)
        raw=input(f"{prompt} ({'/'.join(choices)}) [{default}]: ").strip()
        return raw or default

    def confirm(self, prompt, default=False):
        if self.enabled:
            return Confirm.ask(prompt, default=default)
        raw=input(f"{prompt} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
        if not raw: return default
        return raw in {"y","yes","s","si","sí"}

UI_INSTANCE: UI


def shell_quote(v: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_./:=@+-]+", v):
        return v
    return "'" + v.replace("'", "'\"'\"'") + "'"


def run(argv: Sequence[str], *, cwd: Path|None=None, env=None, check=True, dry_run=False):
    UI_INSTANCE.info("$ " + " ".join(shell_quote(x) for x in argv))
    if dry_run:
        return subprocess.CompletedProcess(argv, 0, "", "")
    cp = subprocess.run(list(argv), cwd=str(cwd) if cwd else None, env=env, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if cp.stdout.strip():
        print(cp.stdout, end="" if cp.stdout.endswith("\n") else "\n")
    if cp.stderr.strip():
        print(cp.stderr, file=sys.stderr, end="" if cp.stderr.endswith("\n") else "\n")
    if check and cp.returncode != 0:
        raise InstallError(f"Command failed with exit code {cp.returncode}: {' '.join(argv)}")
    return cp


def detect_root(start: Path) -> Path|None:
    for c in (start, *start.parents):
        if (c/"pyproject.toml").is_file() and (c/"termux_api_stc").is_dir():
            return c
    return None


def bootstrap(argv, root):
    if os.environ.get(BOOTSTRAP_MARKER) == "1" or "--no-bootstrap" in argv:
        return
    if importlib.util.find_spec("rich") is not None:
        return
    base = (root or Path.cwd()) / ".install-tools"
    py = base / ("Scripts/python.exe" if os.name=="nt" else "bin/python")
    print("[BOOT] Preparing isolated UI tools...")
    if not py.exists():
        venv.EnvBuilder(with_pip=True).create(base)
    rc = subprocess.run([str(py), "-m", "pip", "install", "--quiet", "--upgrade", "rich>=13.7"]).returncode
    if rc != 0: raise SystemExit(rc)
    env=os.environ.copy(); env[BOOTSTRAP_MARKER]="1"
    os.execve(str(py), [str(py), str(Path(__file__).resolve()), *argv], env)


def package_location(py: Path) -> tuple[str|None,str|None]:
    code = (
        "import importlib.util,sys;"
        "s=importlib.util.find_spec('termux_api_stc');"
        "print('' if s is None else (s.origin or ''));"
        "\n"
        "try:\n"
        " import importlib.metadata as m; print(m.version('termux-api-stc'))\n"
        "except Exception: print('')"
    )
    cp = subprocess.run([str(py), "-c", code], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lines = cp.stdout.splitlines()
    return (lines[0] if len(lines)>0 and lines[0] else None,
            lines[1] if len(lines)>1 and lines[1] else None)


def verify_install(py: Path, expected_version: str|None=None):
    loc, ver = package_location(py)
    if not loc:
        raise InstallError("termux-api-stc is not importable after installation.")
    if expected_version and ver != expected_version:
        raise InstallError(f"Installed version mismatch: expected {expected_version}, got {ver}")
    return loc, ver


class InstallApp:
    def __init__(self, cfg: Config):
        self.cfg=cfg
        self.result_dir=(cfg.project_root or Path.cwd())/".install-results"/dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def preflight(self):
        UI_INSTANCE.section("Preflight")
        if not self.cfg.python.exists():
            raise InstallError(f"Python not found: {self.cfg.python}")
        cp=run([str(self.cfg.python), "--version"], check=True)
        pip=run([str(self.cfg.python), "-m", "pip", "--version"], check=False)
        if pip.returncode != 0:
            raise InstallError("pip is not available for the selected Python interpreter.")

        if self.cfg.source in {"source","editable"}:
            if not self.cfg.project_root:
                raise InstallError("Local project root not found.")
        if self.cfg.source=="wheel":
            if not self.cfg.wheel or not self.cfg.wheel.is_file():
                raise InstallError("A valid --wheel path is required.")

        loc, ver = package_location(self.cfg.python)
        UI_INSTANCE.kv([
            ("Python", str(self.cfg.python)),
            ("Source", self.cfg.source),
            ("Requested version", self.cfg.version or "latest"),
            ("Existing install", ver or "NONE"),
            ("Existing location", loc or "NONE"),
            ("User install", "YES" if self.cfg.user else "NO"),
            ("Dry run", "YES" if self.cfg.dry_run else "NO"),
        ])

        if ver and not (self.cfg.force or self.cfg.upgrade):
            UI_INSTANCE.warn("Package is already installed. Use --upgrade or --force to replace/reinstall it.")

    def build_pip_command(self):
        cmd=[str(self.cfg.python), "-m", "pip", "install"]
        if self.cfg.user:
            cmd.append("--user")
        if self.cfg.upgrade:
            cmd.append("--upgrade")
        if self.cfg.force:
            cmd.append("--force-reinstall")
        if self.cfg.no_deps:
            cmd.append("--no-deps")

        if self.cfg.source=="pypi":
            spec=EXPECTED_PROJECT + (f"=={self.cfg.version}" if self.cfg.version else "")
            cmd.append(spec)
        elif self.cfg.source=="testpypi":
            cmd += ["--index-url","https://test.pypi.org/simple/"]
            spec=EXPECTED_PROJECT + (f"=={self.cfg.version}" if self.cfg.version else "")
            cmd.append(spec)
        elif self.cfg.source=="source":
            cmd.append(str(self.cfg.project_root))
        elif self.cfg.source=="editable":
            cmd += ["-e", str(self.cfg.project_root)]
        elif self.cfg.source=="wheel":
            cmd.append(str(self.cfg.wheel))
        else:
            raise InstallError(f"Unsupported source: {self.cfg.source}")
        return cmd

    def write_evidence(self, status, error=None):
        if self.cfg.dry_run: return
        self.result_dir.mkdir(parents=True, exist_ok=True)
        loc, ver=package_location(self.cfg.python)
        data={
            "schema":1,
            "application":"termux-api-stc-install",
            "application_version":APP_VERSION,
            "timestamp_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "status":status,
            "error":error,
            "source":self.cfg.source,
            "python":str(self.cfg.python),
            "version":ver,
            "location":loc,
            "user_install":self.cfg.user,
        }
        report=self.result_dir/"install-report.json"
        report.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        digest=hashlib.sha256(report.read_bytes()).hexdigest()
        (self.result_dir/"SHA256SUMS").write_text(f"{digest}  {report.name}\n",encoding="utf-8")

    def execute(self):
        UI_INSTANCE.banner()
        try:
            self.preflight()
            cmd=self.build_pip_command()

            UI_INSTANCE.section("Installation plan")
            UI_INSTANCE.kv([
                ("Mode",self.cfg.mode),
                ("Command"," ".join(shell_quote(x) for x in cmd)),
                ("Verify","YES" if self.cfg.verify else "NO"),
            ])

            if self.cfg.mode=="check":
                self.write_evidence("PASS")
                UI_INSTANCE.ok("Installation prerequisites are valid.")
                return
            if self.cfg.mode=="plan":
                self.write_evidence("PASS")
                UI_INSTANCE.ok("Installation plan generated; no changes made.")
                return

            if not self.cfg.yes and sys.stdin.isatty():
                if not UI_INSTANCE.confirm("Install termux-api-stc now?", default=False):
                    raise InstallError("Cancelled by operator.")
            elif not self.cfg.yes and not sys.stdin.isatty():
                raise InstallError("Non-interactive installation requires --yes.")

            cp=run(cmd, check=True, dry_run=self.cfg.dry_run)

            if self.cfg.verify and not self.cfg.dry_run:
                UI_INSTANCE.section("Verification")
                loc,ver=verify_install(self.cfg.python, self.cfg.version)
                UI_INSTANCE.kv([("Version",ver or "UNKNOWN"),("Location",loc)])
                UI_INSTANCE.ok("Installed package imports correctly.")

            self.write_evidence("PASS")
            UI_INSTANCE.ok("Installation completed successfully.")
            UI_INSTANCE.info(f"Evidence: {self.result_dir}")
        except Exception as exc:
            try: self.write_evidence("FAIL", str(exc))
            except Exception: pass
            raise


def parser():
    p=argparse.ArgumentParser(prog="install.py",description="termux-api-stc installation console")
    p.add_argument("mode",nargs="?",choices=("check","plan","install"))
    p.add_argument("--source",choices=("pypi","testpypi","source","editable","wheel"),default="pypi")
    p.add_argument("--wheel")
    p.add_argument("--version")
    p.add_argument("--python",default=sys.executable)
    p.add_argument("--user",action="store_true")
    p.add_argument("--force",action="store_true")
    p.add_argument("--upgrade",action="store_true")
    p.add_argument("--no-deps",action="store_true")
    p.add_argument("--dry-run",action="store_true")
    p.add_argument("--yes",action="store_true")
    p.add_argument("--no-ui",action="store_true")
    p.add_argument("--no-bootstrap",action="store_true")
    p.add_argument("--no-verify",action="store_true")
    p.add_argument("--version-info",action="version",version=f"%(prog)s {APP_VERSION}")
    return p


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    p=parser(); ns=p.parse_args(argv)
    root=detect_root(Path(__file__).resolve().parent) or detect_root(Path.cwd())
    bootstrap(argv, root)
    global UI_INSTANCE
    UI_INSTANCE=UI(enabled=not ns.no_ui)

    try:
        if ns.mode is None:
            if not sys.stdin.isatty():
                raise InstallError("No mode supplied in non-interactive execution.")
            UI_INSTANCE.banner()
            mode=UI_INSTANCE.choose("Action",("check","plan","install"),"check")
            source=UI_INSTANCE.choose("Installation source",("pypi","testpypi","source","editable","wheel"),"pypi")
            yes=(mode=="install")
        else:
            mode=ns.mode; source=ns.source; yes=ns.yes

        cfg=Config(
            mode=mode, source=source, project_root=root,
            wheel=Path(ns.wheel).resolve() if ns.wheel else None,
            version=ns.version, python=Path(ns.python).resolve(),
            user=ns.user, force=ns.force, upgrade=ns.upgrade,
            no_deps=ns.no_deps, dry_run=ns.dry_run, yes=yes,
            no_ui=ns.no_ui, no_bootstrap=ns.no_bootstrap,
            verify=not ns.no_verify,
        )
        InstallApp(cfg).execute()
        return 0
    except KeyboardInterrupt:
        UI_INSTANCE.fail("Interrupted by operator."); return 130
    except InstallError as exc:
        UI_INSTANCE.fail(str(exc)); return 1


if __name__=="__main__":
    raise SystemExit(main())
