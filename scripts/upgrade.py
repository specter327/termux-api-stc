#!/usr/bin/env python3
"""
termux-api-stc — Repository Upgrade Console

A single-file repository updater for local use and CI.

Purpose
-------
Synchronize the current termux-api-stc Git working tree with its configured
remote/upstream in a controlled, auditable and reversible way.

Default policy
--------------
- Never discards local work.
- Refuses a dirty working tree unless --stash is explicitly requested.
- Fetches remote refs/tags before making decisions.
- Requires a branch/upstream relationship.
- Uses fast-forward-only updates by default.
- Refuses divergence by default.
- Runs repository verification and tests after updating.
- Can optionally reinstall/synchronize the local Python environment.
- Produces a detailed upgrade report under .upgrade-results/.

Interactive:
    ./scripts/upgrade.py

CI / non-interactive:
    ./scripts/upgrade.py check --no-ui
    ./scripts/upgrade.py plan --no-ui
    ./scripts/upgrade.py upgrade --no-ui --yes

Examples:
    ./scripts/upgrade.py upgrade
    ./scripts/upgrade.py upgrade --stash
    ./scripts/upgrade.py upgrade --strategy rebase
    ./scripts/upgrade.py upgrade --sync-environment editable
    ./scripts/upgrade.py upgrade --sync-environment wheel
    ./scripts/upgrade.py upgrade --branch main --remote origin
    ./scripts/upgrade.py upgrade --verify-target-signature

Dangerous recovery mode:
    ./scripts/upgrade.py upgrade --strategy hard-reset --yes

The program deliberately does NOT:
- silently overwrite local changes;
- auto-resolve merge/rebase conflicts;
- delete branches/tags;
- rewrite remote history;
- push anything to GitHub;
- modify project version or source files itself.
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
import textwrap
import urllib.parse
import venv
from pathlib import Path
from typing import Sequence

APP_VERSION = "1.0"
EXPECTED_PROJECT_NAME = "termux-api-stc"
BOOTSTRAP_MARKER = "TERMUX_API_STC_UPGRADE_BOOTSTRAPPED"
BOOTSTRAP_PACKAGES = ("rich>=13.7", "build>=1.2")

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


class UpgradeError(RuntimeError):
    """Expected repository-upgrade failure."""


@dataclasses.dataclass(slots=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclasses.dataclass(slots=True)
class Config:
    mode: str
    project_root: Path
    remote: str = "origin"
    branch: str | None = None
    strategy: str = "ff-only"
    stash: bool = False
    allow_untracked: bool = False
    skip_tests: bool = False
    skip_verification: bool = False
    dry_run: bool = False
    yes: bool = False
    no_ui: bool = False
    no_bootstrap: bool = False
    sync_environment: str = "none"
    requirements_file: Path | None = None
    verify_target_signature: bool = False
    fetch_tags: bool = True
    prune: bool = True


@dataclasses.dataclass(slots=True)
class RepoState:
    current_branch: str | None = None
    upstream: str | None = None
    head_before: str | None = None
    head_after: str | None = None
    remote_head: str | None = None
    ahead: int = 0
    behind: int = 0
    dirty: bool = False
    status_before: str = ""
    stash_ref: str | None = None
    remote_url: str | None = None


class UI:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled and RICH_AVAILABLE
        self.console = Console() if self.enabled else None

    def banner(self) -> None:
        if self.enabled:
            title = Text("termux-api-stc", style="bold cyan")
            subtitle = Text("Repository Upgrade Console", style="bold white")
            body = Text("Safe Git synchronization • validation • environment refresh", style="green")
            self.console.print(
                Panel(
                    Align.center(Text.assemble(title, "\n", subtitle, "\n\n", body)),
                    border_style="cyan",
                    box=box.ROUNDED,
                )
            )
        else:
            print("=" * 78)
            print("termux-api-stc — Repository Upgrade Console")
            print("=" * 78)

    def section(self, title: str) -> None:
        if self.enabled:
            self.console.rule(f"[bold cyan]{title}[/bold cyan]")
        else:
            print("\n" + "=" * 78)
            print(title)
            print("=" * 78)

    def info(self, message: str) -> None:
        if self.enabled:
            self.console.print(f"[cyan]●[/cyan] {message}")
        else:
            print(f"[INFO] {message}")

    def ok(self, message: str) -> None:
        if self.enabled:
            self.console.print(f"[green]✔[/green] {message}")
        else:
            print(f"[ OK ] {message}")

    def warn(self, message: str) -> None:
        if self.enabled:
            self.console.print(f"[yellow]▲[/yellow] {message}")
        else:
            print(f"[WARN] {message}", file=sys.stderr)

    def fail(self, message: str) -> None:
        if self.enabled:
            self.console.print(f"[bold red]✘ {message}[/bold red]")
        else:
            print(f"[FAIL] {message}", file=sys.stderr)

    def command(self, argv: Sequence[str]) -> None:
        rendered = " ".join(shell_quote(x) for x in argv)
        if self.enabled:
            self.console.print(f"[dim]$ {rendered}[/dim]")
        else:
            print(f"$ {rendered}")

    def key_values(self, rows: Sequence[tuple[str, str]]) -> None:
        if self.enabled:
            table = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
            table.add_column(style="bold")
            table.add_column()
            for key, value in rows:
                table.add_row(key, value)
            self.console.print(table)
        else:
            width = max((len(k) for k, _ in rows), default=0)
            for key, value in rows:
                print(f"{key:<{width}}  {value}")

    def plan_table(self, rows: Sequence[tuple[str, str, str]]) -> None:
        if self.enabled:
            table = Table(title="Upgrade plan", box=box.ROUNDED)
            table.add_column("Step", style="bold")
            table.add_column("Action")
            table.add_column("Policy")
            for step, action, policy in rows:
                table.add_row(step, action, policy)
            self.console.print(table)
        else:
            for step, action, policy in rows:
                print(f"{step}: {action} [{policy}]")

    def confirm(self, prompt: str, default: bool = False) -> bool:
        if self.enabled:
            return Confirm.ask(prompt, default=default)
        suffix = "Y/n" if default else "y/N"
        raw = input(f"{prompt} [{suffix}]: ").strip().lower()
        if not raw:
            return default
        return raw in {"y", "yes", "s", "si", "sí"}

    def choose(self, prompt: str, choices: Sequence[str], default: str) -> str:
        if self.enabled:
            return Prompt.ask(prompt, choices=list(choices), default=default)
        while True:
            raw = input(f"{prompt} ({'/'.join(choices)}) [{default}]: ").strip() or default
            if raw in choices:
                return raw

    def summary(self, status: str, rows: Sequence[tuple[str, str]]) -> None:
        if self.enabled:
            style = "green" if status == "PASS" else "red"
            table = Table(box=box.SIMPLE, show_header=False)
            table.add_column(style="bold")
            table.add_column()
            for key, value in rows:
                table.add_row(key, value)
            self.console.print(
                Panel(table, title=f"[bold {style}]{status}[/bold {style}]",
                      border_style=style, box=box.ROUNDED)
            )
        else:
            print(f"\nSTATUS: {status}")
            self.key_values(rows)


UI_INSTANCE: UI


def shell_quote(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_./:=@+-]+", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def run_command(
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
    capture: bool = True,
    dry_run: bool = False,
    echo: bool = True,
) -> CommandResult:
    if echo:
        UI_INSTANCE.command(argv)

    if dry_run:
        return CommandResult(tuple(argv), 0, "", "")

    completed = subprocess.run(
        list(argv),
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    result = CommandResult(
        tuple(argv),
        completed.returncode,
        completed.stdout or "",
        completed.stderr or "",
    )
    if check and not result.ok:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise UpgradeError(f"Command failed: {' '.join(argv)}\n{detail}")
    return result


def stream_command(
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    dry_run: bool = False,
) -> int:
    UI_INSTANCE.command(argv)
    if dry_run:
        return 0
    process = subprocess.Popen(list(argv), cwd=str(cwd) if cwd else None, env=env)
    return process.wait()


def require_command(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise UpgradeError(f"Required command not found: {name}")
    return path


def detect_project_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "termux_api_stc").is_dir():
            return candidate
    raise UpgradeError(
        "Unable to locate termux-api-stc project root "
        "(expected pyproject.toml and termux_api_stc/)."
    )


def read_project_name(pyproject: Path) -> str:
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^\[project\]\s*(.*?)(?=^\[|\Z)", text)
    if not match:
        raise UpgradeError("pyproject.toml has no [project] table.")
    name = re.search(r'(?m)^\s*name\s*=\s*"([^"]+)"\s*$', match.group(1))
    if not name:
        raise UpgradeError("Missing [project].name.")
    return name.group(1)


def bootstrap_if_needed(argv: Sequence[str], root: Path) -> None:
    if os.environ.get(BOOTSTRAP_MARKER) == "1" or "--no-bootstrap" in argv:
        return
    if importlib.util.find_spec("rich") is not None:
        return

    tools = root / ".upgrade-tools"
    python = tools / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    print("[BOOT] Preparing isolated upgrade UI tools...")

    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(tools)

    rc = subprocess.run([
        str(python), "-m", "pip", "install",
        "--disable-pip-version-check", "--quiet", "--upgrade", "rich>=13.7"
    ]).returncode
    if rc != 0:
        raise SystemExit(rc)

    env = os.environ.copy()
    env[BOOTSTRAP_MARKER] = "1"
    os.execve(
        str(python),
        [str(python), str(Path(__file__).resolve()), *argv],
        env,
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class UpgradeApp:
    def __init__(self, config: Config) -> None:
        self.cfg = config
        self.root = config.project_root
        self.state = RepoState()
        self.results_root = self.root / ".upgrade-results"
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.result_dir = self.results_root / stamp
        self.report_file = self.result_dir / "upgrade-report.json"
        self.log_file = self.result_dir / "upgrade-summary.txt"

    def git(self, *args: str, check: bool = True, dry_run: bool | None = None) -> CommandResult:
        if dry_run is None:
            dry_run = self.cfg.dry_run
        return run_command(
            ["git", *args],
            cwd=self.root,
            check=check,
            dry_run=dry_run,
        )

    def preflight(self) -> None:
        UI_INSTANCE.section("Repository preflight")
        require_command("git")

        if read_project_name(self.root / "pyproject.toml") != EXPECTED_PROJECT_NAME:
            raise UpgradeError(f"Unexpected project; expected {EXPECTED_PROJECT_NAME}.")

        inside = self.git("rev-parse", "--is-inside-work-tree", dry_run=False)
        if inside.stdout.strip() != "true":
            raise UpgradeError("Current project root is not a Git working tree.")

        remote_url = self.git("remote", "get-url", self.cfg.remote, dry_run=False)
        self.state.remote_url = remote_url.stdout.strip()

        branch = self.git("branch", "--show-current", dry_run=False).stdout.strip()
        if not branch:
            raise UpgradeError(
                "Detached HEAD detected. Select/check out a branch before normal upgrade."
            )

        self.state.current_branch = branch

        if self.cfg.branch and self.cfg.branch != branch:
            raise UpgradeError(
                f"Current branch is {branch!r}, requested branch is {self.cfg.branch!r}. "
                "Switch branches explicitly before upgrading."
            )

        self.state.head_before = self.git("rev-parse", "HEAD", dry_run=False).stdout.strip()

        status = self.git(
            "status", "--porcelain=v1", "--untracked-files=all", dry_run=False
        ).stdout.rstrip()
        self.state.status_before = status
        self.state.dirty = bool(status)

        tracked_dirty = self.git(
            "status", "--porcelain=v1", "--untracked-files=no", dry_run=False
        ).stdout.strip()
        untracked = [
            line for line in status.splitlines()
            if line.startswith("??")
        ]

        if tracked_dirty and not self.cfg.stash:
            raise UpgradeError(
                "Tracked local changes exist. Commit them or use --stash explicitly.\n"
                + tracked_dirty
            )
        if untracked and not (self.cfg.stash or self.cfg.allow_untracked):
            raise UpgradeError(
                "Untracked files exist. Use --stash to preserve them in the stash, "
                "or --allow-untracked if they cannot interfere with the update.\n"
                + "\n".join(untracked)
            )

        upstream = self.git(
            "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}",
            check=False, dry_run=False
        )
        if upstream.ok and upstream.stdout.strip():
            self.state.upstream = upstream.stdout.strip()
        else:
            candidate = f"{self.cfg.remote}/{branch}"
            exists = self.git(
                "show-ref", "--verify", f"refs/remotes/{candidate}",
                check=False, dry_run=False
            )
            if exists.ok:
                self.state.upstream = candidate
                UI_INSTANCE.warn(
                    f"No configured branch upstream; using discovered {candidate}."
                )
            else:
                # It may not exist locally until fetch; fetch will resolve it.
                self.state.upstream = candidate
                UI_INSTANCE.warn(
                    f"No configured branch upstream; candidate is {candidate}."
                )

        UI_INSTANCE.key_values([
            ("Repository", str(self.root)),
            ("Remote", self.cfg.remote),
            ("Remote URL", self.state.remote_url or "UNKNOWN"),
            ("Branch", branch),
            ("Upstream", self.state.upstream or "UNKNOWN"),
            ("HEAD", self.state.head_before),
            ("Working tree", "DIRTY" if self.state.dirty else "CLEAN"),
            ("Strategy", self.cfg.strategy),
            ("Mode", self.cfg.mode),
        ])
        UI_INSTANCE.ok("Repository preflight passed.")

    def fetch(self) -> None:
        UI_INSTANCE.section("Fetch remote state")
        args = ["fetch", self.cfg.remote]
        if self.cfg.prune:
            args.append("--prune")
        if self.cfg.fetch_tags:
            args.append("--tags")

        rc = stream_command(
            ["git", *args],
            cwd=self.root,
            dry_run=self.cfg.dry_run,
        )
        if rc != 0:
            raise UpgradeError(f"git fetch failed with exit code {rc}.")

        if self.cfg.dry_run:
            UI_INSTANCE.warn("Dry-run: remote graph cannot be recalculated after a simulated fetch.")
        else:
            UI_INSTANCE.ok("Remote refs updated.")

    def resolve_remote_state(self) -> None:
        UI_INSTANCE.section("Upgrade analysis")

        upstream = self.state.upstream
        if not upstream:
            raise UpgradeError("No upstream candidate available.")

        verify = self.git(
            "rev-parse", "--verify", f"{upstream}^{{commit}}",
            check=False, dry_run=False
        )
        if not verify.ok:
            raise UpgradeError(
                f"Upstream {upstream!r} does not exist after fetch. "
                "Configure branch tracking or select the correct --remote/--branch."
            )

        self.state.remote_head = verify.stdout.strip()

        counts = self.git(
            "rev-list", "--left-right", "--count", f"HEAD...{upstream}",
            dry_run=False
        ).stdout.strip().split()

        if len(counts) != 2:
            raise UpgradeError("Unable to calculate ahead/behind relationship.")

        self.state.ahead = int(counts[0])
        self.state.behind = int(counts[1])

        relation = (
            "UP-TO-DATE" if (self.state.ahead, self.state.behind) == (0, 0)
            else "BEHIND" if self.state.ahead == 0
            else "AHEAD" if self.state.behind == 0
            else "DIVERGED"
        )

        UI_INSTANCE.key_values([
            ("Local HEAD", self.state.head_before or "UNKNOWN"),
            ("Remote HEAD", self.state.remote_head or "UNKNOWN"),
            ("Ahead", str(self.state.ahead)),
            ("Behind", str(self.state.behind)),
            ("Relation", relation),
        ])

        if self.cfg.verify_target_signature:
            verify_sig = self.git(
                "verify-commit", self.state.remote_head,
                check=False, dry_run=False
            )
            if not verify_sig.ok:
                raise UpgradeError(
                    "Target commit signature verification failed.\n"
                    + (verify_sig.stderr.strip() or verify_sig.stdout.strip())
                )
            UI_INSTANCE.ok("Target commit signature verified.")

    def display_plan(self) -> None:
        rows: list[tuple[str, str, str]] = [
            ("1", f"Fetch {self.cfg.remote}", "read-only remote discovery"),
            ("2", f"Compare HEAD ↔ {self.state.upstream}", "ahead/behind graph"),
        ]
        if self.state.dirty and self.cfg.stash:
            rows.append(("3", "Create safety stash including untracked files", "reversible"))
        rows.append(("4", self._strategy_description(), self.cfg.strategy))
        if self.cfg.sync_environment != "none":
            rows.append(("5", f"Synchronize Python environment ({self.cfg.sync_environment})", "local env"))
        if not self.cfg.skip_verification:
            rows.append(("6", "Run verification", "post-update"))
        if not self.cfg.skip_tests:
            rows.append(("7", "Run tests/run-tests.sh", "post-update"))
        rows.append(("8", "Write upgrade evidence", ".upgrade-results/"))
        UI_INSTANCE.plan_table(rows)

    def _strategy_description(self) -> str:
        upstream = self.state.upstream or "<upstream>"
        if self.cfg.strategy == "ff-only":
            return f"Fast-forward HEAD to {upstream}"
        if self.cfg.strategy == "rebase":
            return f"Rebase local commits onto {upstream}"
        return f"Hard-reset HEAD to {upstream} (destructive)"

    def validate_strategy(self) -> None:
        if self.state.ahead == 0 and self.state.behind == 0:
            return

        if self.cfg.strategy == "ff-only":
            if self.state.ahead > 0 and self.state.behind > 0:
                raise UpgradeError(
                    "Local and remote histories diverged. ff-only refuses to rewrite or merge. "
                    "Use --strategy rebase after reviewing the graph, or resolve manually."
                )
            if self.state.ahead > 0 and self.state.behind == 0:
                raise UpgradeError(
                    "Local branch is ahead of upstream. There is nothing to pull; "
                    "ff-only refuses to alter local commits."
                )

        elif self.cfg.strategy == "rebase":
            # Valid for behind or diverged histories.
            pass

        elif self.cfg.strategy == "hard-reset":
            if not self.cfg.yes:
                raise UpgradeError(
                    "hard-reset is destructive and requires --yes in non-interactive execution."
                )

    def create_safety_stash(self) -> None:
        if not (self.state.dirty and self.cfg.stash):
            return

        UI_INSTANCE.section("Safety stash")
        before = self.git("stash", "list", "--format=%gd", dry_run=False).stdout.splitlines()

        message = f"termux-api-stc upgrade {utc_now()} {self.state.head_before}"
        rc = stream_command(
            ["git", "stash", "push", "-u", "-m", message],
            cwd=self.root,
            dry_run=self.cfg.dry_run,
        )
        if rc != 0:
            raise UpgradeError("Unable to create safety stash.")

        if self.cfg.dry_run:
            UI_INSTANCE.info("Dry-run: safety stash not created.")
            return

        after = self.git("stash", "list", "--format=%gd", dry_run=False).stdout.splitlines()
        new_refs = [ref for ref in after if ref not in before]
        self.state.stash_ref = new_refs[0] if new_refs else "stash@{0}"
        UI_INSTANCE.ok(f"Local work preserved in {self.state.stash_ref}.")

    def apply_update(self) -> None:
        UI_INSTANCE.section("Apply repository update")
        upstream = self.state.upstream
        if not upstream:
            raise UpgradeError("No upstream configured.")

        if self.state.ahead == 0 and self.state.behind == 0:
            UI_INSTANCE.ok("Repository is already up to date.")
            return

        if self.cfg.strategy == "ff-only":
            args = ["merge", "--ff-only", upstream]
        elif self.cfg.strategy == "rebase":
            args = ["rebase", upstream]
        else:
            args = ["reset", "--hard", upstream]

        rc = stream_command(
            ["git", *args],
            cwd=self.root,
            dry_run=self.cfg.dry_run,
        )
        if rc != 0:
            if self.cfg.strategy == "rebase":
                UI_INSTANCE.warn(
                    "Rebase stopped. Resolve conflicts and continue/abort manually; "
                    "the updater will not auto-resolve them."
                )
            raise UpgradeError(f"Git update failed with exit code {rc}.")

        if not self.cfg.dry_run:
            self.state.head_after = self.git("rev-parse", "HEAD", dry_run=False).stdout.strip()
            UI_INSTANCE.ok(f"Repository updated to {self.state.head_after}.")

    def restore_stash(self) -> None:
        if not self.state.stash_ref:
            return

        UI_INSTANCE.section("Restore local work")
        rc = stream_command(
            ["git", "stash", "pop", self.state.stash_ref],
            cwd=self.root,
            dry_run=self.cfg.dry_run,
        )
        if rc != 0:
            raise UpgradeError(
                "Repository update succeeded, but restoring the safety stash produced conflicts. "
                f"Your local work remains recoverable; inspect `git status` and `git stash list`."
            )
        UI_INSTANCE.ok("Local changes restored.")

    def sync_environment(self) -> None:
        mode = self.cfg.sync_environment
        if mode == "none":
            return

        UI_INSTANCE.section("Synchronize Python environment")

        if mode == "editable":
            args = [sys.executable, "-m", "pip", "install", "--upgrade", "-e", str(self.root)]
            rc = stream_command(args, cwd=self.root, dry_run=self.cfg.dry_run)
            if rc != 0:
                raise UpgradeError("Editable environment synchronization failed.")

        elif mode == "source":
            args = [sys.executable, "-m", "pip", "install", "--upgrade", str(self.root)]
            rc = stream_command(args, cwd=self.root, dry_run=self.cfg.dry_run)
            if rc != 0:
                raise UpgradeError("Source installation synchronization failed.")

        elif mode == "wheel":
            require_command("git")
            with tempfile.TemporaryDirectory(prefix="termux-api-stc-upgrade-build-") as tmp:
                dist = Path(tmp)
                args = [
                    sys.executable, "-m", "pip", "wheel",
                    "--no-deps", "--wheel-dir", str(dist), str(self.root)
                ]
                rc = stream_command(args, cwd=self.root, dry_run=self.cfg.dry_run)
                if rc != 0:
                    raise UpgradeError("Wheel build for environment synchronization failed.")
                if self.cfg.dry_run:
                    return
                wheels = sorted(dist.glob("*.whl"))
                if len(wheels) != 1:
                    raise UpgradeError(f"Expected one wheel, found {len(wheels)}.")
                rc = stream_command(
                    [sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall",
                     "--no-deps", str(wheels[0])],
                    cwd=self.root,
                )
                if rc != 0:
                    raise UpgradeError("Wheel environment synchronization failed.")

        if self.cfg.requirements_file:
            req = self.cfg.requirements_file
            if not req.is_file():
                raise UpgradeError(f"Requirements file not found: {req}")
            rc = stream_command(
                [sys.executable, "-m", "pip", "install", "--upgrade", "-r", str(req)],
                cwd=self.root,
                dry_run=self.cfg.dry_run,
            )
            if rc != 0:
                raise UpgradeError("Requirements synchronization failed.")

        UI_INSTANCE.ok(f"Python environment synchronized using mode={mode}.")

    def run_verification(self) -> None:
        if self.cfg.skip_verification:
            UI_INSTANCE.warn("Verification skipped by explicit request.")
            return

        UI_INSTANCE.section("Post-upgrade verification")

        verification = self.root / "scripts" / "verification.py"
        if verification.is_file():
            rc = stream_command(
                [sys.executable, str(verification), "--no-ui"],
                cwd=self.root,
                dry_run=self.cfg.dry_run,
            )
            if rc != 0:
                raise UpgradeError(f"verification.py failed with exit code {rc}.")
        else:
            # Until verification.py exists, do strict local smoke checks.
            rc = stream_command(
                [sys.executable, "-m", "compileall", "-q", str(self.root / "termux_api_stc")],
                cwd=self.root,
                dry_run=self.cfg.dry_run,
            )
            if rc != 0:
                raise UpgradeError("Python compilation verification failed.")

            script = (
                "import sys; "
                f"sys.path.insert(0, {str(self.root)!r}); "
                "import termux_api_stc; "
                "print(termux_api_stc.__file__)"
            )
            result = run_command(
                [sys.executable, "-c", script],
                cwd=self.root,
                dry_run=self.cfg.dry_run,
            )
            if result.stdout.strip():
                UI_INSTANCE.info(f"Import: {result.stdout.strip()}")

        UI_INSTANCE.ok("Post-upgrade verification passed.")

    def run_tests(self) -> None:
        if self.cfg.skip_tests:
            UI_INSTANCE.warn("Tests skipped by explicit request.")
            return

        UI_INSTANCE.section("Post-upgrade tests")
        runner = self.root / "tests" / "run-tests.sh"
        if not runner.is_file():
            raise UpgradeError(f"Test runner not found: {runner}")
        if not os.access(runner, os.X_OK):
            raise UpgradeError(f"Test runner is not executable: {runner}")

        rc = stream_command(
            [str(runner)],
            cwd=self.root,
            dry_run=self.cfg.dry_run,
        )
        if rc != 0:
            raise UpgradeError(f"Test campaign failed with exit code {rc}.")
        UI_INSTANCE.ok("Test campaign passed.")

    def write_report(self, status: str, error: str | None = None) -> None:
        if self.cfg.dry_run:
            return

        self.result_dir.mkdir(parents=True, exist_ok=True)
        if self.state.head_after is None:
            head = self.git("rev-parse", "HEAD", check=False, dry_run=False)
            self.state.head_after = head.stdout.strip() if head.ok else None

        final_status = self.git(
            "status", "--porcelain=v1", "--untracked-files=all",
            check=False, dry_run=False
        ).stdout.rstrip()

        report = {
            "schema": 1,
            "application": "termux-api-stc-upgrade",
            "application_version": APP_VERSION,
            "timestamp_utc": utc_now(),
            "status": status,
            "error": error,
            "mode": self.cfg.mode,
            "strategy": self.cfg.strategy,
            "remote": self.cfg.remote,
            "remote_url": self.state.remote_url,
            "branch": self.state.current_branch,
            "upstream": self.state.upstream,
            "head_before": self.state.head_before,
            "remote_head": self.state.remote_head,
            "head_after": self.state.head_after,
            "ahead_before": self.state.ahead,
            "behind_before": self.state.behind,
            "dirty_before": self.state.dirty,
            "stash_ref": self.state.stash_ref,
            "sync_environment": self.cfg.sync_environment,
            "skip_tests": self.cfg.skip_tests,
            "skip_verification": self.cfg.skip_verification,
            "git_status_after": final_status,
            "python": sys.executable,
        }
        self.report_file.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        lines = [
            f"status={status}",
            f"timestamp_utc={report['timestamp_utc']}",
            f"branch={self.state.current_branch}",
            f"upstream={self.state.upstream}",
            f"head_before={self.state.head_before}",
            f"remote_head={self.state.remote_head}",
            f"head_after={self.state.head_after}",
            f"strategy={self.cfg.strategy}",
            f"stash_ref={self.state.stash_ref or ''}",
            f"sync_environment={self.cfg.sync_environment}",
        ]
        if error:
            lines.append(f"error={error}")
        self.log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        sums = self.result_dir / "SHA256SUMS"
        sums.write_text(
            f"{sha256_file(self.report_file)}  {self.report_file.name}\n"
            f"{sha256_file(self.log_file)}  {self.log_file.name}\n",
            encoding="utf-8",
        )

    def execute(self) -> None:
        started = dt.datetime.now(dt.timezone.utc)
        UI_INSTANCE.banner()

        try:
            self.preflight()
            self.fetch()
            self.resolve_remote_state()
            self.display_plan()
            self.validate_strategy()

            if self.cfg.mode == "check":
                self.write_report("PASS")
                UI_INSTANCE.summary("PASS", [
                    ("Mode", "check"),
                    ("Branch", self.state.current_branch or "UNKNOWN"),
                    ("Ahead", str(self.state.ahead)),
                    ("Behind", str(self.state.behind)),
                    ("Update available", "YES" if self.state.behind else "NO"),
                ])
                return

            if self.cfg.mode == "plan":
                self.write_report("PASS")
                UI_INSTANCE.summary("PASS", [
                    ("Mode", "plan"),
                    ("Strategy", self.cfg.strategy),
                    ("Ahead", str(self.state.ahead)),
                    ("Behind", str(self.state.behind)),
                    ("Mutation", "NONE"),
                ])
                return

            if not self.cfg.yes and sys.stdin.isatty():
                if not UI_INSTANCE.confirm("Apply this repository upgrade?", default=False):
                    raise UpgradeError("Cancelled by operator.")
            elif not self.cfg.yes and not sys.stdin.isatty():
                raise UpgradeError(
                    "Non-interactive upgrade requires --yes."
                )

            self.create_safety_stash()
            self.apply_update()
            self.restore_stash()
            self.sync_environment()
            self.run_verification()
            self.run_tests()

            elapsed = dt.datetime.now(dt.timezone.utc) - started
            self.write_report("PASS")
            UI_INSTANCE.summary("PASS", [
                ("Mode", "upgrade"),
                ("Strategy", self.cfg.strategy),
                ("Before", self.state.head_before or "UNKNOWN"),
                ("After", self.state.head_after or self.state.head_before or "UNKNOWN"),
                ("Environment", self.cfg.sync_environment),
                ("Elapsed", str(elapsed).split(".")[0]),
                ("Evidence", str(self.result_dir)),
            ])
        except Exception as exc:
            try:
                self.write_report("FAIL", str(exc))
            except Exception:
                pass
            raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="upgrade.py",
        description="termux-api-stc safe repository upgrade console",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              ./scripts/upgrade.py
              ./scripts/upgrade.py check --no-ui
              ./scripts/upgrade.py plan --no-ui
              ./scripts/upgrade.py upgrade --yes --no-ui
              ./scripts/upgrade.py upgrade --stash
              ./scripts/upgrade.py upgrade --strategy rebase
              ./scripts/upgrade.py upgrade --sync-environment editable
            """
        ),
    )
    parser.add_argument("mode", nargs="?", choices=("check", "plan", "upgrade"))
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch")
    parser.add_argument(
        "--strategy",
        choices=("ff-only", "rebase", "hard-reset"),
        default="ff-only",
    )
    parser.add_argument("--stash", action="store_true")
    parser.add_argument("--allow-untracked", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-verification", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--no-ui", action="store_true")
    parser.add_argument("--no-bootstrap", action="store_true")
    parser.add_argument(
        "--sync-environment",
        choices=("none", "editable", "source", "wheel"),
        default="none",
    )
    parser.add_argument("--requirements-file")
    parser.add_argument("--verify-target-signature", action="store_true")
    parser.add_argument("--no-tags", action="store_true")
    parser.add_argument("--no-prune", action="store_true")
    parser.add_argument("--version", action="version", version=f"%(prog)s {APP_VERSION}")
    return parser


def namespace_to_config(ns: argparse.Namespace, root: Path) -> Config:
    return Config(
        mode=ns.mode,
        project_root=root,
        remote=ns.remote,
        branch=ns.branch,
        strategy=ns.strategy,
        stash=ns.stash,
        allow_untracked=ns.allow_untracked,
        skip_tests=ns.skip_tests,
        skip_verification=ns.skip_verification,
        dry_run=ns.dry_run,
        yes=ns.yes,
        no_ui=ns.no_ui,
        no_bootstrap=ns.no_bootstrap,
        sync_environment=ns.sync_environment,
        requirements_file=Path(ns.requirements_file).resolve() if ns.requirements_file else None,
        verify_target_signature=ns.verify_target_signature,
        fetch_tags=not ns.no_tags,
        prune=not ns.no_prune,
    )


def interactive_config(root: Path, ns: argparse.Namespace) -> Config:
    UI_INSTANCE.banner()
    UI_INSTANCE.section("Interactive upgrade configuration")

    mode = UI_INSTANCE.choose("Action", ("check", "plan", "upgrade"), "check")
    strategy = "ff-only"
    stash = False
    sync_environment = "none"
    yes = False

    if mode == "upgrade":
        strategy = UI_INSTANCE.choose(
            "Git update strategy",
            ("ff-only", "rebase", "hard-reset"),
            "ff-only",
        )
        stash = UI_INSTANCE.confirm(
            "Automatically stash and restore local modifications if present?",
            default=False,
        )
        sync_environment = UI_INSTANCE.choose(
            "Synchronize current Python environment after source update?",
            ("none", "editable", "source", "wheel"),
            "none",
        )
        yes = True

    return Config(
        mode=mode,
        project_root=root,
        remote=ns.remote,
        branch=ns.branch,
        strategy=strategy,
        stash=stash,
        allow_untracked=ns.allow_untracked,
        skip_tests=ns.skip_tests,
        skip_verification=ns.skip_verification,
        dry_run=ns.dry_run,
        yes=yes,
        no_ui=ns.no_ui,
        no_bootstrap=ns.no_bootstrap,
        sync_environment=sync_environment,
        requirements_file=Path(ns.requirements_file).resolve() if ns.requirements_file else None,
        verify_target_signature=ns.verify_target_signature,
        fetch_tags=not ns.no_tags,
        prune=not ns.no_prune,
    )


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    ns = parser.parse_args(argv)

    try:
        try:
            root = detect_project_root(Path(__file__).resolve().parent)
        except UpgradeError:
            root = detect_project_root(Path.cwd())
    except UpgradeError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    bootstrap_if_needed(argv, root)

    global UI_INSTANCE
    UI_INSTANCE = UI(enabled=not ns.no_ui)

    try:
        if ns.mode is None:
            if not sys.stdin.isatty():
                raise UpgradeError("No mode supplied in a non-interactive environment.")
            config = interactive_config(root, ns)
        else:
            config = namespace_to_config(ns, root)

        if config.strategy == "hard-reset" and config.mode != "upgrade":
            UI_INSTANCE.warn("hard-reset strategy has no effect outside upgrade mode.")

        UpgradeApp(config).execute()
        return 0

    except KeyboardInterrupt:
        UI_INSTANCE.fail("Interrupted by operator.")
        return 130
    except UpgradeError as exc:
        UI_INSTANCE.fail(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
