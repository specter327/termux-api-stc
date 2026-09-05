from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

from termux_api_stc import fingerprint, microphone, share, speech_to_text, storage

pytestmark = [pytest.mark.device, pytest.mark.side_effect, pytest.mark.interactive]


def _enabled() -> bool:
    return os.environ.get("TERMUX_API_STC_ENABLE_INTERACTIVE") == "1"


def _gate(*binaries: str) -> None:
    if not _enabled():
        pytest.skip("set TERMUX_API_STC_ENABLE_INTERACTIVE=1")
    for binary in binaries:
        if shutil.which(binary) is None:
            pytest.skip(f"{binary} not installed")


def _native(*argv: str, timeout: float = 180.0) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        shell=False,
        check=False,
    )


def _decode_json(data: bytes, *, source: str):
    try:
        return json.loads(data.decode("utf-8", "strict"))
    except Exception as exc:  # pragma: no cover - diagnostic detail matters on device
        pytest.fail(f"{source} did not return valid JSON: {data!r}; {exc}")


def _fingerprint_semantics(payload) -> str:
    if not isinstance(payload, dict):
        return "invalid-payload"
    errors = payload.get("errors")
    error_set = {str(x) for x in errors} if isinstance(errors, list) else set()
    if "ERROR_NO_HARDWARE" in error_set:
        return "unsupported-no-hardware"
    if "ERROR_NO_ENROLLED_FINGERPRINTS" in error_set:
        return "unavailable-no-enrollment"
    if payload.get("auth_result") == "AUTH_RESULT_SUCCESS":
        return "authenticated"
    return "not-authenticated"


def test_fingerprint_operator_authentication():
    """Require semantic authentication evidence; exit code 0 alone is insufficient."""
    _gate("termux-fingerprint")

    native = _native("termux-fingerprint", timeout=120)
    assert native.returncode == 0, native.stderr.decode("utf-8", "replace")
    native_payload = _decode_json(native.stdout, source="native termux-fingerprint")
    native_semantics = _fingerprint_semantics(native_payload)

    result = fingerprint.authenticate(title="termux-api-stc conformance", timeout=120)
    assert result.returncode == 0
    stc_payload = _decode_json(result.stdout, source="STC fingerprint.authenticate")
    stc_semantics = _fingerprint_semantics(stc_payload)

    # Hardware/enrollment absence is a property of the reference device, not a
    # successful biometric-authentication claim.  Require STC to preserve the same
    # semantic class and record an explicit SKIP instead of a false PASS.
    if native_semantics in {"unsupported-no-hardware", "unavailable-no-enrollment"}:
        assert stc_semantics == native_semantics
        pytest.skip(f"reference device fingerprint state: {native_semantics}")

    assert native_semantics == "authenticated", (
        "native fingerprint command did not demonstrate successful authentication: "
        f"{native_payload!r}"
    )
    assert stc_semantics == "authenticated", (
        "STC fingerprint wrapper did not demonstrate successful authentication: "
        f"{stc_payload!r}"
    )


def test_speech_to_text_operator_interaction():
    """A string type is not sufficient: interactive recognition needs non-empty text."""
    _gate("termux-speech-to-text")

    native = _native("termux-speech-to-text", timeout=120)
    assert native.returncode == 0, native.stderr.decode("utf-8", "replace")
    native_text = native.stdout.decode("utf-8", "strict").strip()

    stc_text = speech_to_text.transcribe(timeout=120).strip()

    # If the official command itself cannot produce a transcript on the reference
    # device, STC must not turn that absence into positive conformance evidence.
    if not native_text:
        if not stc_text:
            pytest.skip("native termux-speech-to-text produced an empty transcript")
        pytest.skip(
            "native transcript was empty while STC produced text; separate operator "
            "interactions are not deterministically comparable"
        )

    assert stc_text, "native speech recognition worked but STC returned an empty transcript"


def test_share_text_android_chooser():
    """Separate command execution from operator-observed Android chooser behavior."""
    _gate("termux-share")
    result = share.share_text("termux-api-stc conformance", action="send", timeout=120)
    assert result.returncode == 0

    if os.environ.get("TERMUX_API_STC_CONFIRM_SHARE_UI") != "1":
        pytest.skip(
            "command executed successfully; set TERMUX_API_STC_CONFIRM_SHARE_UI=1 "
            "only when the operator will verify that the Android chooser appears"
        )


def test_storage_get_android_picker():
    """Compare material output against the official CLI before attributing failure to STC."""
    _gate("termux-storage-get")

    with tempfile.TemporaryDirectory(prefix="stc-storage-native-") as native_tmp, tempfile.TemporaryDirectory(
        prefix="stc-storage-stc-"
    ) as stc_tmp:
        native_output = Path(native_tmp) / "selected-content"
        stc_output = Path(stc_tmp) / "selected-content"

        native = _native("termux-storage-get", str(native_output), timeout=180)
        assert native.returncode == 0, native.stderr.decode("utf-8", "replace")
        native_materialized = native_output.is_file()

        result = storage.get(stc_output, timeout=180)
        assert result.returncode == 0
        stc_materialized = stc_output.is_file()

        if not native_materialized:
            if not stc_materialized:
                pytest.skip(
                    "native termux-storage-get returned success without materializing "
                    "the selected file on this reference device"
                )
            pytest.skip(
                "native StorageGet did not materialize a file while STC did; separate "
                "picker interactions are not deterministically comparable"
            )

        assert stc_materialized, (
            "native termux-storage-get materialized a file but STC storage.get did not"
        )
        assert stc_output.stat().st_size >= 0


def test_microphone_short_recording_to_tempfile():
    _gate("termux-microphone-record")
    with tempfile.TemporaryDirectory(prefix="stc-mic-") as tmp:
        output = Path(tmp) / "sample.m4a"
        try:
            started = microphone.start(file=output, limit_seconds=2, encoder="aac", timeout=30)
            assert started.returncode == 0
            time.sleep(3)
        finally:
            # Safe cleanup even if the upstream recorder already stopped because of -l.
            try:
                microphone.stop(timeout=30)
            except Exception:
                pass
        assert output.is_file()
        assert output.stat().st_size > 0
