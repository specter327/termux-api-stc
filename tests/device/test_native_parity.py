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
    ("termux-sensor", ("-l",)),
    ("termux-tts-engines", ()),
    ("termux-volume", ()),
]

OPTIONAL_PAYLOAD_COMMANDS = [
    ("termux-infrared-frequencies", ()),
]


def _require(binary: str) -> None:
    if shutil.which(binary) is None:
        pytest.skip(f"{binary} not installed")


def _native(binary: str, args: tuple[str, ...]) -> subprocess.CompletedProcess[bytes]:
    cp = subprocess.run(
        [binary, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert cp.returncode == 0, cp.stderr.decode("utf-8", "replace")
    return cp


def _json(data: bytes):
    return json.loads(data.decode("utf-8", "strict"))


@pytest.mark.parametrize("binary,args", STABLE_JSON_COMMANDS)
def test_native_vs_stc_json_equality(binary: str, args: tuple[str, ...]):
    _require(binary)
    native = _native(binary, args)
    assert native.stdout, f"{binary} returned empty stdout where JSON was expected"
    stc = TermuxAPI()[binary].json(*args)
    assert stc == _json(native.stdout)


@pytest.mark.parametrize("binary,args", OPTIONAL_PAYLOAD_COMMANDS)
def test_native_vs_stc_optional_payload_parity(binary: str, args: tuple[str, ...]):
    _require(binary)
    native = _native(binary, args)
    stc = TermuxAPI()[binary].result(*args)

    # Raw success and payload presence are the normative comparison first.
    assert stc.returncode == native.returncode == 0
    assert bool(stc.stdout) == bool(native.stdout)

    # Only assert JSON semantics when the native command produced a payload.
    if native.stdout:
        assert TermuxAPI()[binary].json_if_present(*args) == _json(native.stdout)
    else:
        assert TermuxAPI()[binary].json_if_present(*args) is None


def test_battery_native_and_stc_schema_compatible():
    binary = "termux-battery-status"
    _require(binary)
    native = _native(binary, ())
    stc = TermuxAPI()[binary].json()
    assert isinstance(_json(native.stdout), dict)
    assert isinstance(stc, dict)
    assert set(stc) == set(_json(native.stdout))
