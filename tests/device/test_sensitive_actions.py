from __future__ import annotations

import os
import shutil

import pytest

from termux_api_stc import brightness, infrared, sms, telephony, torch, wifi

pytestmark = [pytest.mark.device, pytest.mark.side_effect, pytest.mark.sensitive]


def _enabled() -> bool:
    return os.environ.get("TERMUX_API_STC_ENABLE_SENSITIVE") == "1"


def _gate(binary: str) -> None:
    if not _enabled():
        pytest.skip("set TERMUX_API_STC_ENABLE_SENSITIVE=1")
    if shutil.which(binary) is None:
        pytest.skip(f"{binary} not installed")


def _bool_env(name: str) -> bool:
    value = os.environ.get(name)
    if value not in {"true", "false"}:
        pytest.skip(f"set {name}=true|false")
    return value == "true"


def test_brightness_operator_supplied_restore_value():
    _gate("termux-brightness")
    test_value = os.environ.get("TERMUX_API_STC_BRIGHTNESS_TEST_VALUE")
    restore_value = os.environ.get("TERMUX_API_STC_BRIGHTNESS_RESTORE_VALUE")
    if test_value is None or restore_value is None:
        pytest.skip("set TERMUX_API_STC_BRIGHTNESS_TEST_VALUE and TERMUX_API_STC_BRIGHTNESS_RESTORE_VALUE")
    try:
        brightness.set(test_value if test_value == "auto" else int(test_value))
    finally:
        brightness.set(restore_value if restore_value == "auto" else int(restore_value))


def test_torch_toggle_with_operator_supplied_restore_state():
    _gate("termux-torch")
    restore = _bool_env("TERMUX_API_STC_TORCH_RESTORE_STATE")
    try:
        torch.set(not restore, timeout=30)
    finally:
        torch.set(restore, timeout=30)


def test_wifi_toggle_with_operator_supplied_restore_state():
    _gate("termux-wifi-enable")
    restore = _bool_env("TERMUX_API_STC_WIFI_RESTORE_STATE")
    try:
        wifi.enable(not restore, timeout=30)
    finally:
        wifi.enable(restore, timeout=30)


def test_infrared_transmit_explicit_hardware_opt_in():
    _gate("termux-infrared-transmit")
    frequency = os.environ.get("TERMUX_API_STC_IR_FREQUENCY_HZ")
    pattern = os.environ.get("TERMUX_API_STC_IR_PATTERN")
    if not frequency or not pattern:
        pytest.skip("set TERMUX_API_STC_IR_FREQUENCY_HZ and TERMUX_API_STC_IR_PATTERN")
    result = infrared.transmit(int(frequency), pattern, timeout=30)
    assert result.returncode == 0


def test_sms_send_external_communication_explicit_opt_in():
    _gate("termux-sms-send")
    if os.environ.get("TERMUX_API_STC_ENABLE_EXTERNAL_COMMUNICATIONS") != "1":
        pytest.skip("set TERMUX_API_STC_ENABLE_EXTERNAL_COMMUNICATIONS=1")
    recipient = os.environ.get("TERMUX_API_STC_SMS_RECIPIENT")
    if not recipient:
        pytest.skip("set TERMUX_API_STC_SMS_RECIPIENT")
    result = sms.send(recipient, "termux-api-stc conformance test", timeout=30)
    assert result.returncode == 0


def test_telephony_call_external_communication_explicit_opt_in():
    _gate("termux-telephony-call")
    if os.environ.get("TERMUX_API_STC_ENABLE_EXTERNAL_COMMUNICATIONS") != "1":
        pytest.skip("set TERMUX_API_STC_ENABLE_EXTERNAL_COMMUNICATIONS=1")
    number = os.environ.get("TERMUX_API_STC_CALL_NUMBER")
    if not number:
        pytest.skip("set TERMUX_API_STC_CALL_NUMBER")
    result = telephony.call(number, timeout=30)
    assert isinstance(result, str)
