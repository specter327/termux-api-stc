from __future__ import annotations

import shutil

import pytest

from termux_api_stc import audio, battery, sensor

pytestmark = [pytest.mark.device, pytest.mark.conformance]


def _require(binary: str) -> None:
    if shutil.which(binary) is None:
        pytest.skip(f"{binary} not installed")


@pytest.mark.asyncio
async def test_real_android_async_audio_info():
    _require("termux-audio-info")
    value = await audio.info_async(timeout=30)
    assert value is not None


@pytest.mark.asyncio
async def test_real_android_async_battery_status():
    _require("termux-battery-status")
    value = await battery.status_async(timeout=30)
    assert isinstance(value, dict)


@pytest.mark.asyncio
async def test_real_android_async_sensor_inventory():
    _require("termux-sensor")
    value = await sensor.list_available_async(timeout=30)
    assert isinstance(value, (list, dict))
