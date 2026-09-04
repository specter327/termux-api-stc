from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from termux_api_stc import TermuxAPI

pytestmark = [pytest.mark.device, pytest.mark.conformance]

STABLE_JSON_COMMANDS = [
    ("termux-audio-info", ()),
    ("termux-camera-info", ()),
    ("termux-contact-list", ()),
    ("termux-infrared-frequencies", ()),
    ("termux-sensor", ("-l",)),
    ("termux-tts-engines", ()),
    ("termux-volume", ()),
]


def _require(binary: str) -> None:
    if shutil.which(binary) is None:
        pytest.skip(f"{binary} not installed")


def _native_json(binary: str, args: tuple[str, ...]):
    cp = subprocess.run([binary, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    assert cp.returncode == 0, cp.stderr.decode("utf-8", "replace")
    return json.loads(cp.stdout.decode("utf-8", "strict"))


@pytest.mark.parametrize("binary,args", STABLE_JSON_COMMANDS)
def test_native_vs_stc_json_equality(binary: str, args: tuple[str, ...]):
    _require(binary)
    native = _native_json(binary, args)
    stc = TermuxAPI()[binary].json(*args)
    assert stc == native


def test_battery_native_and_stc_schema_compatible():
    binary = "termux-battery-status"
    _require(binary)
    native = _native_json(binary, ())
    stc = TermuxAPI()[binary].json()
    assert isinstance(native, dict)
    assert isinstance(stc, dict)
    # Values can change between sequential calls; keys should remain compatible.
    assert set(stc) == set(native)
