from __future__ import annotations

import os
import shutil
import tempfile
import time
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


def _volume_entries(value):
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    if isinstance(value, dict):
        # Preserve compatibility with any upstream object-shaped representation.
        if isinstance(value.get("streams"), list):
            return [x for x in value["streams"] if isinstance(x, dict)]
        return [value]
    return []


def _find_stream(value, name: str):
    for item in _volume_entries(value):
        if str(item.get("stream", "")).lower() == name.lower():
            return item
    return None


def test_clipboard_roundtrip_and_restore():
    _gate("termux-clipboard-get", "termux-clipboard-set")
    original = clipboard.get()
    marker = f"termux-api-stc-{uuid.uuid4()}"
    try:
        clipboard.set(marker)
        assert clipboard.get() == marker
    finally:
        clipboard.set(original)


@pytest.mark.asyncio
async def test_clipboard_async_roundtrip_and_restore():
    _gate("termux-clipboard-get", "termux-clipboard-set")
    original = await clipboard.get_async()
    marker = f"termux-api-stc-async-{uuid.uuid4()}"
    try:
        await clipboard.set_async(marker)
        assert await clipboard.get_async() == marker
    finally:
        await clipboard.set_async(original)


def test_camera_photo_tempfile_jpeg():
    _gate("termux-camera-photo")
    with tempfile.TemporaryDirectory(prefix="stc-camera-") as tmp:
        output = Path(tmp) / "photo.jpg"
        result = camera.photo(output, camera_id=0, timeout=60)
        assert result.returncode == 0
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
            # The upstream list schema is not elevated to a stronger STC contract here;
            # use textual containment only as observational evidence.
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
