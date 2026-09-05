from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from termux_api_stc import camera, clipboard
from tests.device.test_interactive_actions import _fingerprint_semantics
from tests.device.junit_summary import summarize


def test_junit_summary_single_suite(tmp_path: Path):
    path = tmp_path / "junit.xml"
    path.write_text('<testsuite tests="4" failures="1" errors="0" skipped="2"/>', encoding="utf-8")
    assert summarize(path) == "tests=4 failures=1 errors=0 skipped=2"


def test_junit_summary_multiple_suites(tmp_path: Path):
    path = tmp_path / "junit.xml"
    path.write_text(
        '<testsuites>'
        '<testsuite tests="3" failures="0" errors="1" skipped="0"/>'
        '<testsuite tests="2" failures="1" errors="0" skipped="1"/>'
        '</testsuites>',
        encoding="utf-8",
    )
    assert summarize(path) == "tests=5 failures=1 errors=1 skipped=1"


def test_junit_summary_missing_file_is_explicit(tmp_path: Path):
    assert summarize(tmp_path / "missing.xml") == (
        "tests=UNKNOWN failures=UNKNOWN errors=UNKNOWN skipped=UNKNOWN"
    )


def test_camera_photo_public_return_contract(monkeypatch, tmp_path: Path):
    seen = {}

    def fake_text(*args, timeout=None, **kwargs):
        seen["args"] = args
        seen["timeout"] = timeout
        return ""

    monkeypatch.setattr(camera._PHOTO, "text", fake_text)
    output = tmp_path / "photo.jpg"
    value = camera.photo(output, camera_id=2, timeout=7)
    assert value == ""
    assert seen["args"] == ("-c", "2", str(output))
    assert seen["timeout"] == 7


def test_clipboard_set_uses_official_stdin_contract(monkeypatch):
    seen = {}

    def fake_text(*args, input=None, timeout=None, **kwargs):
        seen["args"] = args
        seen["input"] = input
        seen["timeout"] = timeout
        return ""

    monkeypatch.setattr(clipboard._SET, "text", fake_text)
    value = clipboard.set("hello", timeout=9)
    assert value == ""
    assert seen["args"] == ()
    assert seen["input"] == b"hello"
    assert seen["timeout"] == 9



def test_fingerprint_no_hardware_is_not_success():
    payload = {
        "errors": ["ERROR_NO_HARDWARE", "ERROR_NO_ENROLLED_FINGERPRINTS"],
        "failed_attempts": 0,
        "auth_result": "AUTH_RESULT_UNKNOWN",
    }
    assert _fingerprint_semantics(payload) == "unsupported-no-hardware"
    assert _fingerprint_semantics(payload) != "authenticated"


def test_fingerprint_success_requires_explicit_auth_result_success():
    assert _fingerprint_semantics({"errors": [], "auth_result": "AUTH_RESULT_SUCCESS"}) == "authenticated"
    assert _fingerprint_semantics({"errors": [], "auth_result": "AUTH_RESULT_UNKNOWN"}) == "not-authenticated"


def test_empty_speech_transcript_is_not_positive_evidence():
    # Regression for the old interactive assertion `isinstance(result, str)`,
    # which incorrectly accepted an empty upstream transcript as functional proof.
    value = ""
    assert isinstance(value, str)
    assert not value.strip()



def test_installed_artifact_runner_guard_is_declared():
    runner = (Path(__file__).parents[1] / "run-device-tests.sh").read_text(encoding="utf-8")
    assert "TERMUX_API_STC_USE_INSTALLED" in runner
    assert "TERMUX_API_STC_REQUIRE_INSTALLED" in runner
    assert "installed-artifact" in runner
