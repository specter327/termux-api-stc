from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from termux_api_stc import camera, clipboard, fingerprint, share, sms, speech_to_text

pytestmark = [pytest.mark.device, pytest.mark.side_effect]


def _enabled() -> bool:
    return os.environ.get("TERMUX_API_STC_ENABLE_SIDE_EFFECTS") == "1"


def _gate(binary: str) -> None:
    if not _enabled():
        pytest.skip("set TERMUX_API_STC_ENABLE_SIDE_EFFECTS=1")
    if shutil.which(binary) is None:
        pytest.skip(f"{binary} not installed")


def test_clipboard_roundtrip_and_restore():
    _gate("termux-clipboard-get")
    _gate("termux-clipboard-set")
    original = clipboard.get()
    marker = "termux-api-stc-device-conformance"
    try:
        clipboard.set(marker)
        assert clipboard.get() == marker
    finally:
        clipboard.set(original)


def test_camera_photo_creates_nonempty_file():
    _gate("termux-camera-photo")
    with tempfile.TemporaryDirectory(prefix="stc-camera-") as tmp:
        output = Path(tmp) / "photo.jpg"
        camera.photo(output, camera_id=0, timeout=60)
        assert output.is_file()
        assert output.stat().st_size > 0
        assert output.read_bytes()[:2] == b"\xff\xd8"


@pytest.mark.interactive
def test_fingerprint_interactive():
    _gate("termux-fingerprint")
    result = fingerprint.authenticate(title="termux-api-stc conformance", timeout=120)
    assert result.returncode == 0


@pytest.mark.interactive
def test_speech_to_text_interactive():
    _gate("termux-speech-to-text")
    result = speech_to_text.transcribe(timeout=120)
    assert isinstance(result, str)


@pytest.mark.interactive
def test_share_text_interactive():
    _gate("termux-share")
    result = share.share_text("termux-api-stc conformance", action="send", timeout=60)
    assert result.returncode == 0


def test_sms_send_explicitly_guarded():
    _gate("termux-sms-send")
    if os.environ.get("TERMUX_API_STC_ENABLE_COMMUNICATION_SIDE_EFFECTS") != "1":
        pytest.skip("set TERMUX_API_STC_ENABLE_COMMUNICATION_SIDE_EFFECTS=1")
    recipient = os.environ.get("TERMUX_API_STC_SMS_RECIPIENT")
    if not recipient:
        pytest.skip("set TERMUX_API_STC_SMS_RECIPIENT")
    result = sms.send(recipient, "termux-api-stc conformance test", timeout=30)
    assert result.returncode == 0
