from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from termux_api_stc import fingerprint, microphone, share, speech_to_text, storage

pytestmark = [pytest.mark.device, pytest.mark.side_effect, pytest.mark.interactive]


def _enabled() -> bool:
    return os.environ.get("TERMUX_API_STC_ENABLE_INTERACTIVE") == "1"


def _gate(binary: str) -> None:
    if not _enabled():
        pytest.skip("set TERMUX_API_STC_ENABLE_INTERACTIVE=1")
    if shutil.which(binary) is None:
        pytest.skip(f"{binary} not installed")


def test_fingerprint_operator_authentication():
    _gate("termux-fingerprint")
    result = fingerprint.authenticate(title="termux-api-stc conformance", timeout=120)
    assert result.returncode == 0


def test_speech_to_text_operator_interaction():
    _gate("termux-speech-to-text")
    result = speech_to_text.transcribe(timeout=120)
    assert isinstance(result, str)


def test_share_text_android_chooser():
    _gate("termux-share")
    result = share.share_text("termux-api-stc conformance", action="send", timeout=120)
    assert result.returncode == 0


def test_storage_get_android_picker():
    _gate("termux-storage-get")
    with tempfile.TemporaryDirectory(prefix="stc-storage-") as tmp:
        output = Path(tmp) / "selected-content"
        result = storage.get(output, timeout=180)
        assert result.returncode == 0
        assert output.exists()
        assert output.is_file()


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
