from __future__ import annotations
import os, shutil, subprocess
from .core.models import EnvironmentReport
from .official import OFFICIAL_COMMANDS

def inspect_environment() -> EnvironmentReport:
    prefix = os.environ.get("PREFIX")
    is_termux = bool(prefix and "com.termux" in prefix)
    android_release = android_sdk = None
    getprop = shutil.which("getprop")
    if getprop:
        def q(name: str) -> str | None:
            cp = subprocess.run([getprop, name], text=True, capture_output=True)
            value = cp.stdout.strip()
            return value or None
        android_release = q("ro.build.version.release")
        android_sdk = q("ro.build.version.sdk")
    commands = {name: shutil.which(name) is not None for name in OFFICIAL_COMMANDS}
    return EnvironmentReport(
        is_termux=is_termux,
        prefix=prefix,
        home=os.environ.get("HOME"),
        android_release=android_release,
        android_sdk=android_sdk,
        commands=commands,
    )
