from __future__ import annotations

import shutil
import subprocess

import pytest

from termux_api_stc import TermuxAPI
from termux_api_stc import audio, battery, call_log, contacts, location, sensor

pytestmark = [pytest.mark.device, pytest.mark.conformance]


def require(binary: str):
    if shutil.which(binary) is None:
        pytest.skip(f"{binary} not installed")


def test_raw_battery_native_and_stc_succeed():
    require("termux-battery-status")
    native=subprocess.run(["termux-battery-status"],capture_output=True,check=False)
    stc=TermuxAPI()["termux-battery-status"].result()
    assert native.returncode == 0
    assert stc.returncode == 0
    assert battery.status() is not None


def test_audio_info_parseable():
    require("termux-audio-info")
    assert audio.info() is not None


def test_contacts_parseable_or_permission_failure_is_explicit():
    require("termux-contact-list")
    # If permission is denied the library must raise ExecutionError, not silently fabricate data.
    value=contacts.list_json()
    assert isinstance(value, (list, dict))


def test_call_log_default_query_parseable():
    require("termux-call-log")
    value=call_log.query_json(limit=1,offset=0)
    assert isinstance(value, (list, dict))


def test_location_last_gps_parseable():
    require("termux-location")
    value=location.get(provider="gps",request="last",timeout=30)
    assert isinstance(value, dict)


def test_sensor_inventory_parseable():
    require("termux-sensor")
    value=sensor.list_available(timeout=30)
    assert isinstance(value, (list, dict))
