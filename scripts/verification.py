#!/usr/bin/env python3
"""Verify a termux-api-stc checkout or installation and emit deterministic evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
import os
import subprocess
import sys
from pathlib import Path


def root_from(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "termux_api_stc").is_dir():
            return candidate
    raise SystemExit("ERROR: project root not found")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(argv: list[str], root: Path) -> tuple[int, str]:
    cp = subprocess.run(argv, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return cp.returncode, cp.stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--tests", action="store_true")
    parser.add_argument("--output", default=".verification-results")
    ns = parser.parse_args()

    root = root_from(Path(__file__).resolve().parent)
    out = root / ns.output
    out.mkdir(parents=True, exist_ok=True)

    code = r"""
import json
import importlib.metadata as md
import termux_api_stc
from termux_api_stc import inspect_environment

try:
    dist = md.version("termux-api-stc")
except md.PackageNotFoundError:
    dist = None

r = inspect_environment()
print(json.dumps({
    "runtime_version": termux_api_stc.__version__,
    "distribution_version": dist,
    "import_path": termux_api_stc.__file__,
    "is_termux": r.is_termux,
    "android_release": r.android_release,
    "android_sdk": r.android_sdk,
    "termux_version": r.termux_version,
    "termux_api_package_version": r.termux_api_package_version,
    "official_command_count": len(r.commands),
}, sort_keys=True))
"""
    cp = subprocess.run(
        [ns.python, "-c", code],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONPATH": str(root)},
    )
    (out / "runtime.json").write_text(cp.stdout, encoding="utf-8")
    (out / "runtime.stderr.txt").write_text(cp.stderr, encoding="utf-8")
    if cp.returncode != 0:
        (out / "status.txt").write_text("FAIL\n", encoding="utf-8")
        return cp.returncode

    data = json.loads(cp.stdout)
    if data["distribution_version"] is not None and data["distribution_version"] != data["runtime_version"]:
        (out / "status.txt").write_text("FAIL: version mismatch\n", encoding="utf-8")
        return 4

    rc = 0
    if ns.tests:
        rc, output = run([ns.python, "-m", "pytest", "-q", "tests/unit-test"], root)
        (out / "tests.txt").write_text(output, encoding="utf-8")

    status = "PASS" if rc == 0 else "FAIL"
    (out / "status.txt").write_text(status + "\n", encoding="utf-8")

    evidence = [p for p in out.iterdir() if p.is_file() and p.name != "SHA256SUMS"]
    (out / "SHA256SUMS").write_text(
        "".join(f"{sha256(p)}  {p.name}\n" for p in sorted(evidence)),
        encoding="utf-8",
    )

    print(json.dumps({"status": status, "evidence": str(out)}, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
