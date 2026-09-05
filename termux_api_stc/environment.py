from __future__ import annotations

import os
import shutil
import subprocess

from .core.models import EnvironmentReport
from .official import OFFICIAL_COMMANDS


def _capture(argv: list[str]) -> str | None:
    try:
        cp = subprocess.run(argv, text=True, capture_output=True, check=False)
    except OSError:
        return None
    value = cp.stdout.strip()
    return value or None


def _getprop(name: str) -> str | None:
    executable = shutil.which("getprop")
    return _capture([executable, name]) if executable else None


def _package_version(package: str) -> str | None:
    executable = shutil.which("dpkg-query")
    if not executable:
        return None
    return _capture([executable, "-W", "-f=${Version}", package])


def inspect_environment() -> EnvironmentReport:
    prefix = os.environ.get("PREFIX")
    commands = {name: shutil.which(name) is not None for name in OFFICIAL_COMMANDS}
    return EnvironmentReport(
        is_termux=bool(prefix and "com.termux" in prefix),
        prefix=prefix,
        home=os.environ.get("HOME"),
        android_release=_getprop("ro.build.version.release"),
        android_sdk=_getprop("ro.build.version.sdk"),
        device_manufacturer=_getprop("ro.product.manufacturer"),
        device_model=_getprop("ro.product.model"),
        device_name=_getprop("ro.product.device"),
        device_abi=_getprop("ro.product.cpu.abi"),
        termux_version=os.environ.get("TERMUX_VERSION"),
        termux_api_package_version=_package_version("termux-api"),
        commands=commands,
    )
