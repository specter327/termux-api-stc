#!/usr/bin/env python3
"""
termux-api-stc — Release Console

A single-file release application for local use and CI.

Features
--------
- Rich interactive terminal UI when no mode is supplied.
- Deterministic non-interactive CLI for CI:
    check | build | github | pypi | both
- Isolated bootstrap environment for release tooling.
- Git cleanliness and tracked-artifact checks.
- PEP 440 version validation and pyproject/__version__ consistency.
- Unit-test campaign execution.
- Clean wheel + sdist build.
- Twine metadata validation.
- Wheel installation/import smoke test.
- SHA256SUMS generation.
- GitHub Release creation through gh(1).
- PyPI/TestPyPI publication through Twine.
- PyPI Trusted Publishing preparation mode for GitHub Actions.
- Dry-run support.
- No source/version/changelog/commit mutation.

The program deliberately does NOT:
- edit source files;
- change the package version;
- git add/commit project changes;
- overwrite an existing PyPI release;
- overwrite an existing GitHub Release.
"""

from __future__ import annotations

import argparse
import ast
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
import urllib.error
import urllib.parse
import urllib.request
import venv
from pathlib import Path
from typing import Iterable, Sequence

APP_VERSION = "1.0"
EXPECTED_PROJECT_NAME = "termux-api-stc"
DEFAULT_TAG_PREFIX = "v"
BOOTSTRAP_PACKAGES = ("rich>=13.7", "build>=1.2", "twine>=6.0", "packaging>=24.0")
BOOTSTRAP_MARKER = "TERMUX_API_STC_RELEASE_BOOTSTRAPPED"

# ---------------------------------------------------------------------------
# Optional Rich UI
# ---------------------------------------------------------------------------

RICH_AVAILABLE = False

try:
    from rich import box
    from rich.align import Align
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
    from rich.traceback import install as rich_traceback_install

    RICH_AVAILABLE = True
    rich_traceback_install(show_locals=False)
except Exception:
    Console = None  # type: ignore[assignment]


class ReleaseError(RuntimeError):
    """Expected release validation/publication failure."""


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
class ProjectMetadata:
    name: str
    version: str
    init_version: str | None
    is_prerelease: bool


@dataclasses.dataclass(slots=True)
class Config:
    mode: str
    project_root: Path
    allow_dirty: bool = False
    skip_tests: bool = False
    dry_run: bool = False
    create_tag: bool = False
    trusted_publishing: bool = False
    repository: str = "pypi"
    notes_file: Path | None = None
    github_repo: str | None = None
    github_target: str | None = None
    tag_prefix: str = DEFAULT_TAG_PREFIX
    keep_tools: bool = False
    no_bootstrap: bool = False
    no_ui: bool = False


@dataclasses.dataclass(slots=True)
class ReleaseState:
    metadata: ProjectMetadata | None = None
    tag: str | None = None
    head_sha: str | None = None
    dist_files: list[Path] = dataclasses.field(default_factory=list)
    checksums_file: Path | None = None


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------


class UI:
    def __init__(self, *, enabled: bool = True) -> None:
        self.enabled = enabled and RICH_AVAILABLE
        self.console = Console() if self.enabled else None

    def banner(self) -> None:
        if self.enabled:
            title = Text("termux-api-stc", style="bold cyan")
            subtitle = Text("Release Console", style="bold white")
            body = Text()
            body.append("Deterministic release pipeline\n", style="dim")
            body.append("Git • Tests • Build • GitHub • PyPI", style="green")
            self.console.print(
                Panel(
                    Align.center(Text.assemble(title, "\n", subtitle, "\n\n", body)),
                    box=box.ROUNDED,
                    border_style="cyan",
                )
            )
        else:
            print("=" * 78)
            print("termux-api-stc — Release Console")
            print("=" * 78)

    def section(self, title: str) -> None:
        if self.enabled:
            self.console.rule(f"[bold cyan]{title}[/bold cyan]")
        else:
            print()
            print("=" * 78)
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

    def key_values(self, values: Sequence[tuple[str, str]]) -> None:
        if self.enabled:
            table = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
            table.add_column(style="bold")
            table.add_column()
            for key, value in values:
                table.add_row(key, value)
            self.console.print(table)
        else:
            width = max((len(k) for k, _ in values), default=0)
            for key, value in values:
                print(f"{key:<{width}}  {value}")

    def artifacts(self, paths: Sequence[Path]) -> None:
        if self.enabled:
            table = Table(title="Release artifacts", box=box.ROUNDED)
            table.add_column("Artifact", style="bold")
            table.add_column("Size", justify="right")
            table.add_column("SHA-256")
            for path in paths:
                digest = sha256_file(path)
                table.add_row(path.name, human_size(path.stat().st_size), digest[:20] + "…")
            self.console.print(table)
        else:
            for path in paths:
                print(f"- {path.name} ({human_size(path.stat().st_size)}) {sha256_file(path)}")

    def summary(self, *, status: str, lines: Sequence[tuple[str, str]]) -> None:
        if self.enabled:
            style = "green" if status == "PASS" else "red"
            body = Table(box=box.SIMPLE, show_header=False)
            body.add_column(style="bold")
            body.add_column()
            for key, value in lines:
                body.add_row(key, value)
            self.console.print(
                Panel(
                    body,
                    title=f"[bold {style}]{status}[/bold {style}]",
                    border_style=style,
                    box=box.ROUNDED,
                )
            )
        else:
            print()
            print(f"STATUS: {status}")
            self.key_values(lines)

    def choose(self, prompt: str, choices: Sequence[str], default: str) -> str:
        if self.enabled:
            return Prompt.ask(prompt, choices=list(choices), default=default)
        while True:
            raw = input(f"{prompt} ({'/'.join(choices)}) [{default}]: ").strip() or default
            if raw in choices:
                return raw

    def confirm(self, prompt: str, default: bool = False) -> bool:
        if self.enabled:
            return Confirm.ask(prompt, default=default)
        suffix = "Y/n" if default else "y/N"
        raw = input(f"{prompt} [{suffix}]: ").strip().lower()
        if not raw:
            return default
        return raw in {"y", "yes", "s", "si", "sí"}


UI_INSTANCE: UI


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def shell_quote(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_./:=@+-]+", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def which(name: str) -> str | None:
    return shutil.which(name)


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
        raise ReleaseError(f"Command failed: {' '.join(argv)}\n{detail}")

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

    process = subprocess.Popen(
        list(argv),
        cwd=str(cwd) if cwd else None,
        env=env,
    )
    return process.wait()


def require_command(name: str) -> str:
    path = which(name)
    if not path:
        raise ReleaseError(f"Required command not found: {name}")
    return path


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def detect_project_root(start: Path) -> Path:
    candidates = [start, *start.parents]
    for candidate in candidates:
        if (candidate / "pyproject.toml").is_file() and (candidate / "termux_api_stc").is_dir():
            return candidate
    raise ReleaseError(
        "Unable to locate project root. Expected pyproject.toml and termux_api_stc/."
    )


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------


def rich_is_available() -> bool:
    return importlib.util.find_spec("rich") is not None


def bootstrap_if_needed(argv: Sequence[str], project_root: Path) -> None:
    """
    Bootstrap release-only dependencies into an isolated venv and re-exec.

    This keeps the project environment clean while ensuring the interactive UI
    and packaging tools are available.
    """
    if os.environ.get(BOOTSTRAP_MARKER) == "1":
        return

    parsed_no_bootstrap = "--no-bootstrap" in argv
    if parsed_no_bootstrap:
        return

    # If everything needed is already importable, no bootstrap is required.
    modules = ("rich", "build", "twine", "packaging")
    if all(importlib.util.find_spec(name) is not None for name in modules):
        return

    base = project_root / ".release-tools"
    python_path = base / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

    print("[BOOT] Preparing isolated release tools...")

    if not python_path.exists():
        venv.EnvBuilder(with_pip=True, clear=False).create(base)

    cmd = [
        str(python_path),
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--quiet",
        "--upgrade",
        *BOOTSTRAP_PACKAGES,
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    env = os.environ.copy()
    env[BOOTSTRAP_MARKER] = "1"

    os.execve(
        str(python_path),
        [str(python_path), str(Path(__file__).resolve()), *argv],
        env,
    )


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


def read_project_table(pyproject: Path) -> dict[str, str | None]:
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^\[project\]\s*(.*?)(?=^\[|\Z)", text)
    if not match:
        raise ReleaseError("pyproject.toml has no [project] table.")
    block = match.group(1)

    def read_string(key: str) -> str | None:
        hit = re.search(rf'(?m)^\s*{re.escape(key)}\s*=\s*"([^"]+)"\s*$', block)
        return hit.group(1) if hit else None

    return {"name": read_string("name"), "version": read_string("version")}


def read_source_version(project_root: Path) -> str:
    version_file = project_root / "termux_api_stc" / "_version.py"
    if not version_file.is_file():
        raise ReleaseError("Missing termux_api_stc/_version.py.")
    match = re.search(
        r'(?m)^__version__\s*=\s*"([^"]+)"\s*$',
        version_file.read_text(encoding="utf-8"),
    )
    if not match:
        raise ReleaseError("Unable to read __version__ from termux_api_stc/_version.py.")
    return match.group(1)


def load_metadata(config: Config) -> ProjectMetadata:
    from packaging.version import InvalidVersion, Version

    project = read_project_table(config.project_root / "pyproject.toml")
    name = project["name"]
    raw_version = project["version"] or read_source_version(config.project_root)

    if name != EXPECTED_PROJECT_NAME:
        raise ReleaseError(
            f"Unexpected [project].name {name!r}; expected {EXPECTED_PROJECT_NAME!r}."
        )

    try:
        parsed = Version(raw_version)
    except InvalidVersion as exc:
        raise ReleaseError(f"Invalid PEP 440 version {raw_version!r}: {exc}") from exc

    return ProjectMetadata(
        name=name,
        version=raw_version,
        init_version=raw_version,
        is_prerelease=parsed.is_prerelease,
    )


# ---------------------------------------------------------------------------
# Release application
# ---------------------------------------------------------------------------


class ReleaseApp:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.root = config.project_root
        self.state = ReleaseState()
        self.dist = self.root / "dist"
        self.tests_runner = self.root / "tests" / "run-tests.sh"
        self.tools_python = Path(sys.executable)

    @property
    def metadata(self) -> ProjectMetadata:
        if self.state.metadata is None:
            raise ReleaseError("Project metadata has not been loaded.")
        return self.state.metadata

    @property
    def tag(self) -> str:
        if not self.state.tag:
            raise ReleaseError("Release tag has not been determined.")
        return self.state.tag

    def preflight(self) -> None:
        UI_INSTANCE.section("Preflight")

        require_command("git")
        inside = run_command(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=self.root,
        )
        if inside.stdout.strip() != "true":
            raise ReleaseError(f"{self.root} is not a Git working tree.")

        run_command(["git", "remote", "get-url", "origin"], cwd=self.root)

        status = run_command(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=self.root,
        ).stdout.strip()

        if status and not self.config.allow_dirty:
            raise ReleaseError(
                "Git working tree is dirty.\n\n"
                + status
                + "\n\nCommit/stash changes or use --allow-dirty explicitly."
            )
        if status:
            UI_INSTANCE.warn("Dirty Git tree explicitly allowed.")

        tracked = run_command(
            [
                "git",
                "ls-files",
                "dist/**",
                "build/**",
                "*.egg-info/**",
                "**/__pycache__/**",
                "*.pyc",
            ],
            cwd=self.root,
        ).stdout.strip()

        if tracked:
            raise ReleaseError(
                "Generated artifacts are tracked by Git and must be removed before release:\n"
                + tracked
            )

        self.state.head_sha = run_command(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
        ).stdout.strip()

        self.state.metadata = load_metadata(self.config)
        self.state.tag = self.config.tag_prefix + self.metadata.version

        UI_INSTANCE.key_values(
            [
                ("Project", self.metadata.name),
                ("Version", self.metadata.version),
                ("Tag", self.tag),
                ("Commit", self.state.head_sha),
                ("Mode", self.config.mode),
                ("Repository", self.config.repository),
                ("Python", sys.executable),
                ("Started", utc_now()),
            ]
        )
        UI_INSTANCE.ok("Repository and project metadata validated.")

    def validate_sources(self) -> None:
        UI_INSTANCE.section("Source validation")

        rc = stream_command(
            [sys.executable, "-m", "compileall", "-q", str(self.root / "termux_api_stc")],
            cwd=self.root,
            dry_run=self.config.dry_run,
        )
        if rc != 0:
            raise ReleaseError("Python source compilation failed.")

        script = textwrap.dedent(
            f"""
            import sys
            from pathlib import Path
            root = Path({str(self.root)!r})
            sys.path.insert(0, str(root))
            import termux_api_stc

            actual = getattr(termux_api_stc, "__version__", None)
            expected = {self.metadata.version!r}
            if actual is not None and actual != expected:
                raise SystemExit(f"version mismatch: {{actual!r}} != {{expected!r}}")
            print(termux_api_stc.__file__)
            print(actual or "version-not-exposed")
            """
        )

        result = run_command([sys.executable, "-c", script], cwd=self.root)
        if result.stdout.strip():
            UI_INSTANCE.info("Import smoke: " + " | ".join(result.stdout.splitlines()))
        UI_INSTANCE.ok("Sources compile and package imports.")

    def run_tests(self) -> None:
        UI_INSTANCE.section("Unit-test campaign")
        if self.config.skip_tests:
            UI_INSTANCE.warn("Tests skipped by explicit request.")
            return

        if not self.tests_runner.is_file():
            raise ReleaseError(f"Test runner not found: {self.tests_runner}")

        if not os.access(self.tests_runner, os.X_OK):
            raise ReleaseError(f"Test runner is not executable: {self.tests_runner}")

        rc = stream_command(
            [str(self.tests_runner)],
            cwd=self.root,
            dry_run=self.config.dry_run,
        )
        if rc != 0:
            raise ReleaseError(f"Unit-test campaign failed with exit code {rc}.")
        UI_INSTANCE.ok("Unit-test campaign passed.")

    def clean_build(self) -> None:
        UI_INSTANCE.section("Clean build workspace")

        if self.config.dry_run:
            UI_INSTANCE.info(f"Would remove {self.dist} and build/")
            return

        shutil.rmtree(self.dist, ignore_errors=True)
        shutil.rmtree(self.root / "build", ignore_errors=True)

        for path in self.root.glob("*.egg-info"):
            if path.is_dir():
                shutil.rmtree(path)

        self.dist.mkdir(parents=True, exist_ok=True)
        UI_INSTANCE.ok("Previous local build artifacts removed.")

    def build(self) -> None:
        UI_INSTANCE.section("Build wheel + sdist")

        env = os.environ.copy()
        try:
            commit_epoch = run_command(
                ["git", "show", "-s", "--format=%ct", "HEAD"],
                cwd=self.root,
            ).stdout.strip()
            if commit_epoch:
                env["SOURCE_DATE_EPOCH"] = commit_epoch
        except ReleaseError:
            pass

        rc = stream_command(
            [sys.executable, "-m", "build"],
            cwd=self.root,
            env=env,
            dry_run=self.config.dry_run,
        )
        if rc != 0:
            raise ReleaseError(f"Package build failed with exit code {rc}.")

        if self.config.dry_run:
            UI_INSTANCE.ok("Dry-run build command accepted.")
            return

        wheels = sorted(self.dist.glob("*.whl"))
        sdists = sorted(self.dist.glob("*.tar.gz"))

        if len(wheels) != 1:
            raise ReleaseError(f"Expected exactly one wheel; found {len(wheels)}.")
        if len(sdists) != 1:
            raise ReleaseError(f"Expected exactly one sdist; found {len(sdists)}.")

        self.state.dist_files = [wheels[0], sdists[0]]
        UI_INSTANCE.artifacts(self.state.dist_files)
        UI_INSTANCE.ok("Wheel and sdist built.")

    def twine_check(self) -> None:
        UI_INSTANCE.section("Package metadata")
        if self.config.dry_run:
            UI_INSTANCE.info("Would run: python -m twine check dist/*")
            return

        files = [str(x) for x in self.state.dist_files]
        rc = stream_command(
            [sys.executable, "-m", "twine", "check", *files],
            cwd=self.root,
        )
        if rc != 0:
            raise ReleaseError(f"twine check failed with exit code {rc}.")
        UI_INSTANCE.ok("Twine metadata validation passed.")

    def wheel_smoke(self) -> None:
        UI_INSTANCE.section("Wheel installation smoke")

        if self.config.dry_run:
            UI_INSTANCE.info("Would install the built wheel into an isolated venv.")
            return

        wheel = next((p for p in self.state.dist_files if p.suffix == ".whl"), None)
        if wheel is None:
            raise ReleaseError("Built wheel not found.")

        tmp = Path(tempfile.mkdtemp(prefix="termux-api-stc-wheel-"))
        try:
            venv.EnvBuilder(with_pip=True).create(tmp)
            python = tmp / ("Scripts/python.exe" if os.name == "nt" else "bin/python")

            run_command(
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--quiet",
                    "--no-deps",
                    str(wheel),
                ],
                capture=True,
            )

            script = textwrap.dedent(
                f"""
                import termux_api_stc
                actual = getattr(termux_api_stc, "__version__", None)
                expected = {self.metadata.version!r}
                if actual is not None and actual != expected:
                    raise SystemExit(f"installed version mismatch: {{actual!r}} != {{expected!r}}")
                print(termux_api_stc.__file__)
                print(actual or "version-not-exposed")
                """
            )

            result = run_command([str(python), "-c", script])
            UI_INSTANCE.info("Installed wheel: " + " | ".join(result.stdout.splitlines()))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

        UI_INSTANCE.ok("Wheel installation/import smoke passed.")

    def write_checksums(self) -> None:
        UI_INSTANCE.section("Checksums")

        if self.config.dry_run:
            UI_INSTANCE.info("Would generate dist/SHA256SUMS.")
            return

        sums = self.dist / "SHA256SUMS"
        lines = [f"{sha256_file(path)}  {path.name}" for path in self.state.dist_files]
        sums.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.state.checksums_file = sums
        UI_INSTANCE.artifacts([*self.state.dist_files, sums])
        UI_INSTANCE.ok("SHA256SUMS generated.")

    def pypi_base_url(self) -> str:
        if self.config.repository == "pypi":
            return "https://pypi.org"
        return "https://test.pypi.org"

    def pypi_upload_url(self) -> str:
        if self.config.repository == "pypi":
            return "https://upload.pypi.org/legacy/"
        return "https://test.pypi.org/legacy/"

    def check_pypi_version(self) -> None:
        UI_INSTANCE.section(f"{self.config.repository} version check")

        url = (
            f"{self.pypi_base_url()}/pypi/"
            f"{urllib.parse.quote(self.metadata.name, safe='')}/"
            f"{urllib.parse.quote(self.metadata.version, safe='')}/json"
        )
        request = urllib.request.Request(
            url,
            headers={"User-Agent": f"termux-api-stc-release-console/{APP_VERSION}"},
        )

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.status == 200:
                    raise ReleaseError(
                        f"{self.metadata.name} {self.metadata.version} already exists "
                        f"on {self.config.repository}. Releases are immutable."
                    )
                raise ReleaseError(
                    f"Unexpected {self.config.repository} HTTP status {response.status}."
                )
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                UI_INSTANCE.ok(
                    f"{self.metadata.name} {self.metadata.version} is available "
                    f"on {self.config.repository}."
                )
                return
            raise ReleaseError(
                f"Unable to query {self.config.repository}: HTTP {exc.code}."
            ) from exc
        except urllib.error.URLError as exc:
            raise ReleaseError(f"Unable to query {self.config.repository}: {exc}") from exc

    def _tag_commit(self, tag: str) -> str | None:
        result = run_command(
            ["git", "rev-list", "-n", "1", tag],
            cwd=self.root,
            check=False,
        )
        return result.stdout.strip() if result.ok and result.stdout.strip() else None

    def _local_tag_exists(self) -> bool:
        return run_command(
            ["git", "rev-parse", "-q", "--verify", f"refs/tags/{self.tag}"],
            cwd=self.root,
            check=False,
        ).ok

    def _remote_tag_commit(self) -> str | None:
        annotated = run_command(
            ["git", "ls-remote", "origin", f"refs/tags/{self.tag}^{{}}"],
            cwd=self.root,
            check=False,
        )
        if annotated.ok and annotated.stdout.strip():
            return annotated.stdout.split()[0]

        direct = run_command(
            ["git", "ls-remote", "origin", f"refs/tags/{self.tag}"],
            cwd=self.root,
            check=False,
        )
        if direct.ok and direct.stdout.strip():
            return direct.stdout.split()[0]
        return None

    def ensure_tag(self) -> None:
        UI_INSTANCE.section("Release tag")
        head = self.state.head_sha or run_command(
            ["git", "rev-parse", "HEAD"], cwd=self.root
        ).stdout.strip()

        if self._local_tag_exists():
            commit = self._tag_commit(self.tag)
            if commit != head:
                raise ReleaseError(
                    f"Local tag {self.tag} points to {commit}, current HEAD is {head}."
                )
            UI_INSTANCE.ok(f"Local tag {self.tag} points to HEAD.")
        else:
            if not self.config.create_tag:
                raise ReleaseError(
                    f"Tag {self.tag} does not exist locally. "
                    "Create it first or use --create-tag."
                )
            argv = ["git", "tag", "-a", self.tag, "-m", f"{self.metadata.name} {self.metadata.version}"]
            rc = stream_command(argv, cwd=self.root, dry_run=self.config.dry_run)
            if rc != 0:
                raise ReleaseError("Unable to create release tag.")
            UI_INSTANCE.ok(f"Created annotated tag {self.tag}.")

        remote = self._remote_tag_commit()
        if remote:
            if remote != head:
                raise ReleaseError(
                    f"Remote tag {self.tag} resolves to {remote}, current HEAD is {head}."
                )
            UI_INSTANCE.ok(f"Remote tag {self.tag} exists and matches HEAD.")
        else:
            if not self.config.create_tag:
                raise ReleaseError(
                    f"Tag {self.tag} does not exist on origin. "
                    "Push it first or use --create-tag."
                )
            rc = stream_command(
                ["git", "push", "origin", self.tag],
                cwd=self.root,
                dry_run=self.config.dry_run,
            )
            if rc != 0:
                raise ReleaseError("Unable to push release tag.")
            UI_INSTANCE.ok(f"Pushed tag {self.tag}.")

    def github_release_exists(self) -> bool:
        args = ["gh", "release", "view", self.tag]
        if self.config.github_repo:
            args += ["-R", self.config.github_repo]
        return run_command(args, check=False).ok

    def publish_github(self) -> None:
        UI_INSTANCE.section("GitHub Release")
        require_command("gh")

        if not (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")):
            auth = run_command(["gh", "auth", "status"], check=False)
            if not auth.ok:
                raise ReleaseError(
                    "GitHub CLI is not authenticated. Configure gh auth or GH_TOKEN/GITHUB_TOKEN."
                )

        self.ensure_tag()

        if not self.config.dry_run and self.github_release_exists():
            raise ReleaseError(f"GitHub Release {self.tag} already exists.")

        assets = [str(p) for p in self.state.dist_files]
        if self.state.checksums_file:
            assets.append(str(self.state.checksums_file))

        args = [
            "gh",
            "release",
            "create",
            self.tag,
            *assets,
            "--verify-tag",
            "--title",
            f"{self.metadata.name} {self.metadata.version}",
        ]

        if self.config.notes_file:
            if not self.config.notes_file.is_file():
                raise ReleaseError(f"Release notes file not found: {self.config.notes_file}")
            args += ["--notes-file", str(self.config.notes_file)]
        else:
            args += ["--generate-notes"]

        if self.metadata.is_prerelease:
            args.append("--prerelease")

        if self.config.github_target:
            args += ["--target", self.config.github_target]

        if self.config.github_repo:
            args += ["-R", self.config.github_repo]

        rc = stream_command(args, cwd=self.root, dry_run=self.config.dry_run)
        if rc != 0:
            raise ReleaseError(f"GitHub Release publication failed with exit code {rc}.")
        UI_INSTANCE.ok(f"GitHub Release {self.tag} published.")

    def publish_pypi(self) -> None:
        UI_INSTANCE.section("PyPI publication")
        self.check_pypi_version()

        if self.config.trusted_publishing:
            UI_INSTANCE.info(
                "Trusted Publishing mode: artifacts are ready, but this process will not "
                "exchange GitHub OIDC credentials itself."
            )
            UI_INSTANCE.info(
                "Publish dist/ from the GitHub Actions trusted-publisher step."
            )
            return

        env = os.environ.copy()
        token = env.get("PYPI_API_TOKEN")
        if token:
            env["TWINE_USERNAME"] = "__token__"
            env["TWINE_PASSWORD"] = token

        if not env.get("TWINE_PASSWORD") and not (Path.home() / ".pypirc").is_file():
            raise ReleaseError(
                "No PyPI credential found. Set PYPI_API_TOKEN/TWINE_PASSWORD, configure "
                "~/.pypirc, or use --trusted-publishing in GitHub Actions."
            )

        files = [str(p) for p in self.state.dist_files]
        args = [
            sys.executable,
            "-m",
            "twine",
            "upload",
            "--non-interactive",
            "--repository-url",
            self.pypi_upload_url(),
            *files,
        ]

        rc = stream_command(
            args,
            cwd=self.root,
            env=env,
            dry_run=self.config.dry_run,
        )
        if rc != 0:
            raise ReleaseError(f"PyPI publication failed with exit code {rc}.")
        UI_INSTANCE.ok(
            f"{self.metadata.name} {self.metadata.version} published to "
            f"{self.config.repository}."
        )

    def perform_checks(self) -> None:
        self.preflight()
        self.validate_sources()
        self.run_tests()

    def perform_build(self) -> None:
        self.clean_build()
        self.build()
        self.twine_check()
        self.wheel_smoke()
        self.write_checksums()

    def run(self) -> None:
        started = dt.datetime.now(dt.timezone.utc)
        UI_INSTANCE.banner()

        self.perform_checks()

        if self.config.mode == "check":
            elapsed = dt.datetime.now(dt.timezone.utc) - started
            UI_INSTANCE.summary(
                status="PASS",
                lines=[
                    ("Mode", "check"),
                    ("Version", self.metadata.version),
                    ("Commit", self.state.head_sha or "UNKNOWN"),
                    ("Elapsed", str(elapsed).split(".")[0]),
                ],
            )
            return

        self.perform_build()

        if self.config.mode == "build":
            if self.config.trusted_publishing:
                self.check_pypi_version()
            elapsed = dt.datetime.now(dt.timezone.utc) - started
            UI_INSTANCE.summary(
                status="PASS",
                lines=[
                    ("Mode", "build"),
                    ("Version", self.metadata.version),
                    ("Artifacts", str(len(self.state.dist_files))),
                    ("Directory", str(self.dist)),
                    ("Elapsed", str(elapsed).split(".")[0]),
                ],
            )
            return

        if self.config.mode in {"github", "both"}:
            self.publish_github()

        if self.config.mode in {"pypi", "both"}:
            self.publish_pypi()

        elapsed = dt.datetime.now(dt.timezone.utc) - started
        UI_INSTANCE.summary(
            status="PASS",
            lines=[
                ("Mode", self.config.mode),
                ("Version", self.metadata.version),
                ("Tag", self.tag),
                ("Repository", self.config.repository),
                ("Elapsed", str(elapsed).split(".")[0]),
            ],
        )


# ---------------------------------------------------------------------------
# Interactive wizard
# ---------------------------------------------------------------------------


def interactive_config(root: Path, base: argparse.Namespace) -> Config:
    UI_INSTANCE.banner()
    UI_INSTANCE.section("Interactive release configuration")

    mode = UI_INSTANCE.choose(
        "Release action",
        ("check", "build", "github", "pypi", "both"),
        "check",
    )

    repository = "pypi"
    trusted = False
    create_tag = False

    if mode in {"pypi", "both"}:
        repository = UI_INSTANCE.choose(
            "Python package repository",
            ("pypi", "testpypi"),
            "pypi",
        )
        if repository == "pypi":
            trusted = UI_INSTANCE.confirm(
                "Prepare for GitHub Actions Trusted Publishing instead of token upload?",
                default=False,
            )

    if mode in {"github", "both"}:
        create_tag = UI_INSTANCE.confirm(
            "Create and push the expected annotated tag if missing?",
            default=False,
        )

    skip_tests = UI_INSTANCE.confirm("Skip tests?", default=False)
    allow_dirty = UI_INSTANCE.confirm("Allow a dirty Git tree?", default=False)
    dry_run = UI_INSTANCE.confirm("Dry-run (no network publication/tag mutation)?", default=False)

    config = Config(
        mode=mode,
        project_root=root,
        allow_dirty=allow_dirty,
        skip_tests=skip_tests,
        dry_run=dry_run,
        create_tag=create_tag,
        trusted_publishing=trusted,
        repository=repository,
        notes_file=Path(base.notes_file).resolve() if base.notes_file else None,
        github_repo=base.github_repo,
        github_target=base.github_target,
        tag_prefix=base.tag_prefix,
        keep_tools=base.keep_tools,
        no_bootstrap=base.no_bootstrap,
        no_ui=base.no_ui,
    )

    UI_INSTANCE.section("Planned campaign")
    UI_INSTANCE.key_values(
        [
            ("Mode", config.mode),
            ("Repository", config.repository),
            ("Tests", "SKIP" if config.skip_tests else "REQUIRED"),
            ("Git tree", "DIRTY ALLOWED" if config.allow_dirty else "CLEAN REQUIRED"),
            ("Create tag", "YES" if config.create_tag else "NO"),
            ("Trusted Publishing", "YES" if config.trusted_publishing else "NO"),
            ("Dry run", "YES" if config.dry_run else "NO"),
        ]
    )

    if not UI_INSTANCE.confirm("Execute this release campaign?", default=False):
        raise ReleaseError("Cancelled by operator.")

    return config


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="publish.py",
        description="termux-api-stc deterministic release console",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
            Examples:
              ./scripts/publish.py
              ./scripts/publish.py check
              ./scripts/publish.py build
              ./scripts/publish.py github --create-tag
              PYPI_API_TOKEN='pypi-...' ./scripts/publish.py pypi
              PYPI_API_TOKEN='pypi-...' ./scripts/publish.py both --create-tag
              ./scripts/publish.py build --trusted-publishing

            CI:
              ./scripts/publish.py check --no-ui
              ./scripts/publish.py build --trusted-publishing --no-ui
            """
        ),
    )

    parser.add_argument(
        "mode",
        nargs="?",
        choices=("check", "build", "github", "pypi", "both"),
        help="Release mode. Omit for interactive terminal UI.",
    )
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--create-tag", action="store_true")
    parser.add_argument("--trusted-publishing", action="store_true")
    parser.add_argument(
        "--repository",
        choices=("pypi", "testpypi"),
        default="pypi",
    )
    parser.add_argument("--notes-file")
    parser.add_argument("--github-repo")
    parser.add_argument("--github-target")
    parser.add_argument(
        "--tag-prefix",
        default=os.environ.get("PUBLISH_TAG_PREFIX", DEFAULT_TAG_PREFIX),
    )
    parser.add_argument("--keep-tools", action="store_true")
    parser.add_argument("--no-bootstrap", action="store_true")
    parser.add_argument("--no-ui", action="store_true")
    parser.add_argument("--version", action="version", version=f"%(prog)s {APP_VERSION}")

    return parser


def namespace_to_config(ns: argparse.Namespace, root: Path) -> Config:
    return Config(
        mode=ns.mode,
        project_root=root,
        allow_dirty=ns.allow_dirty,
        skip_tests=ns.skip_tests,
        dry_run=ns.dry_run,
        create_tag=ns.create_tag,
        trusted_publishing=ns.trusted_publishing,
        repository=ns.repository,
        notes_file=Path(ns.notes_file).resolve() if ns.notes_file else None,
        github_repo=ns.github_repo or os.environ.get("GH_REPO"),
        github_target=ns.github_target,
        tag_prefix=ns.tag_prefix,
        keep_tools=ns.keep_tools,
        no_bootstrap=ns.no_bootstrap,
        no_ui=ns.no_ui,
    )


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    ns = parser.parse_args(argv)

    try:
        root = detect_project_root(Path(__file__).resolve().parent)
    except ReleaseError:
        try:
            root = detect_project_root(Path.cwd())
        except ReleaseError as exc:
            print(f"[FAIL] {exc}", file=sys.stderr)
            return 1

    bootstrap_if_needed(argv, root)

    global UI_INSTANCE
    UI_INSTANCE = UI(enabled=not ns.no_ui)

    # No explicit mode + terminal => rich interactive wizard.
    if ns.mode is None:
        if not sys.stdin.isatty():
            UI_INSTANCE.fail("No mode supplied in a non-interactive environment.")
            parser.print_usage()
            return 2

        try:
            config = interactive_config(root, ns)
        except (ReleaseError, KeyboardInterrupt) as exc:
            UI_INSTANCE.fail(str(exc) if str(exc) else "Cancelled.")
            return 130 if isinstance(exc, KeyboardInterrupt) else 1
    else:
        config = namespace_to_config(ns, root)

    if config.trusted_publishing and config.repository != "pypi":
        UI_INSTANCE.fail("--trusted-publishing is only valid for the PyPI workflow.")
        return 2

    if config.trusted_publishing and config.mode not in {"build", "pypi", "both"}:
        UI_INSTANCE.warn(
            "--trusted-publishing has no effect for this mode."
        )

    try:
        ReleaseApp(config).run()
        return 0
    except KeyboardInterrupt:
        UI_INSTANCE.fail("Interrupted by operator.")
        return 130
    except ReleaseError as exc:
        UI_INSTANCE.fail(str(exc))
        UI_INSTANCE.summary(
            status="FAIL",
            lines=[
                ("Mode", config.mode),
                ("Project", str(config.project_root)),
                ("Time", utc_now()),
            ],
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
