from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

import pytest

from termux_api_stc import camera, clipboard, notification, notification_channel, toast, tts, vibrate, volume

pytestmark = [pytest.mark.device, pytest.mark.side_effect, pytest.mark.reversible]


def _enabled() -> bool:
    return os.environ.get("TERMUX_API_STC_ENABLE_SAFE_EFFECTS") == "1"


def _gate(*binaries: str) -> None:
    if not _enabled():
        pytest.skip("set TERMUX_API_STC_ENABLE_SAFE_EFFECTS=1")
    for binary in binaries:
        if shutil.which(binary) is None:
            pytest.skip(f"{binary} not installed")


def _native(*argv: str, input_bytes: bytes | None = None, timeout: float = 30.0) -> subprocess.CompletedProcess[bytes]:
    cp = subprocess.run(
        argv,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        shell=False,
        check=False,
    )
    assert cp.returncode == 0, (
        f"native command failed: {argv!r}; rc={cp.returncode}; "
        f"stderr={cp.stderr!r}"
    )
    return cp


def _native_clipboard_get() -> str:
    return _native("termux-clipboard-get").stdout.decode("utf-8", "strict")


def _native_clipboard_set(text: str) -> None:
    # Exercise the official CLI's stdin contract, matching STC's wrapper path.
    _native("termux-clipboard-set", input_bytes=text.encode("utf-8"))


def _volume_entries(value):
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    if isinstance(value, dict):
        if isinstance(value.get("streams"), list):
            return [x for x in value["streams"] if isinstance(x, dict)]
        return [value]
    return []


def _find_stream(value, name: str):
    for item in _volume_entries(value):
        if str(item.get("stream", "")).lower() == name.lower():
            return item
    return None


def test_clipboard_native_stc_parity_and_restore():
    """Compare STC with the native CLI without inventing a round-trip guarantee.

    Android may legitimately expose an empty clipboard payload even immediately after
    a successful native set.  The conformance requirement is therefore parity with
    the official CLI on the same device, not a stronger STC-only semantic.
    """
    _gate("termux-clipboard-get", "termux-clipboard-set")
    original_native = _native_clipboard_get()
    original_stc = clipboard.get()
    assert original_stc == original_native

    native_marker = f"termux-api-stc-native-{uuid.uuid4()}"
    stc_marker = f"termux-api-stc-stc-{uuid.uuid4()}"
    try:
        _native_clipboard_set(native_marker)
        assert clipboard.get() == _native_clipboard_get()

        clipboard.set(stc_marker)
        assert clipboard.get() == _native_clipboard_get()
    finally:
        # Restoration is best-effort at the upstream CLI boundary; observation may
        # still be empty because that is the native behavior on some Android builds.
        _native_clipboard_set(original_native)
        assert clipboard.get() == _native_clipboard_get()


@pytest.mark.asyncio
async def test_clipboard_async_native_stc_parity_and_restore():
    _gate("termux-clipboard-get", "termux-clipboard-set")
    original_native = _native_clipboard_get()
    original_stc = await clipboard.get_async()
    assert original_stc == original_native

    marker = f"termux-api-stc-async-{uuid.uuid4()}"
    try:
        await clipboard.set_async(marker)
        native_after = await asyncio.to_thread(_native_clipboard_get)
        assert await clipboard.get_async() == native_after
    finally:
        await asyncio.to_thread(_native_clipboard_set, original_native)
        native_restored = await asyncio.to_thread(_native_clipboard_get)
        assert await clipboard.get_async() == native_restored


def test_camera_photo_tempfile_jpeg():
    _gate("termux-camera-photo")
    with tempfile.TemporaryDirectory(prefix="stc-camera-") as tmp:
        output = Path(tmp) / "photo.jpg"
        result = camera.photo(output, camera_id=0, timeout=60)
        # camera.photo() contractually returns decoded stdout; command failure is
        # already represented by ExecutionError before this point.
        assert isinstance(result, str)
        assert output.is_file()
        assert output.stat().st_size > 2
        assert output.read_bytes()[:2] == b"\xff\xd8"


def test_notification_create_list_remove():
    _gate("termux-notification", "termux-notification-list", "termux-notification-remove")
    notification_id = f"stc-{uuid.uuid4().hex[:12]}"
    title = "termux-api-stc conformance"
    try:
        result = notification.show(
            "temporary conformance notification",
            title=title,
            notification_id=notification_id,
            timeout=30,
        )
        assert result.returncode == 0
        listed = notification.list_json(timeout=30)
        assert listed is None or isinstance(listed, (list, dict))
        if listed is not None:
            assert notification_id in repr(listed) or title in repr(listed)
    finally:
        notification.remove(notification_id, timeout=30)


def test_notification_channel_create_delete():
    _gate("termux-notification-channel")
    channel_id = f"stc-{uuid.uuid4().hex[:12]}"
    try:
        created = notification_channel.create(channel_id, "STC conformance", timeout=30)
        assert created.returncode == 0
    finally:
        deleted = notification_channel.delete(channel_id, timeout=30)
        assert deleted.returncode == 0


@pytest.mark.asyncio
async def test_notification_channel_async_create_delete():
    _gate("termux-notification-channel")
    channel_id = f"stc-async-{uuid.uuid4().hex[:8]}"
    try:
        created = await notification_channel.create_async(channel_id, "STC async conformance", timeout=30)
        assert created.returncode == 0
    finally:
        deleted = await notification_channel.delete_async(channel_id, timeout=30)
        assert deleted.returncode == 0


def test_volume_music_roundtrip_and_restore():
    _gate("termux-volume")
    before = volume.get_all(timeout=30)
    music = _find_stream(before, "music")
    if music is None:
        pytest.skip("upstream volume payload has no identifiable music stream")
    current = music.get("volume")
    maximum = music.get("max_volume")
    if not isinstance(current, int) or not isinstance(maximum, int) or maximum < 1:
        pytest.skip("upstream volume payload lacks integer volume/max_volume")

    candidate = current + 1 if current < maximum else max(0, current - 1)
    if candidate == current:
        pytest.skip("no reversible alternate music volume available")

    try:
        volume.set("music", candidate, timeout=30)
        observed = _find_stream(volume.get_all(timeout=30), "music")
        assert observed is not None
        assert observed.get("volume") == candidate
    finally:
        volume.set("music", current, timeout=30)
        restored = _find_stream(volume.get_all(timeout=30), "music")
        assert restored is not None
        assert restored.get("volume") == current


def test_vibrate_command_success():
    _gate("termux-vibrate")
    result = vibrate.vibrate(50)
    assert isinstance(result, str)


def test_toast_command_success():
    _gate("termux-toast")
    result = toast.show("termux-api-stc conformance", short=True)
    assert result.returncode == 0


def test_tts_speak_command_success():
    _gate("termux-tts-speak")
    result = tts.speak("termux api stc conformance", timeout=60)
    assert isinstance(result, str)
