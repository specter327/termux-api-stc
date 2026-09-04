from __future__ import annotations
import os, shutil
import pytest
from termux_api_stc import brightness, toast, vibrate

pytestmark=[pytest.mark.device,pytest.mark.side_effect]


def enabled():
    return os.environ.get("TERMUX_API_STC_ENABLE_SIDE_EFFECTS") == "1"


def gate(binary: str):
    if not enabled(): pytest.skip("set TERMUX_API_STC_ENABLE_SIDE_EFFECTS=1")
    if shutil.which(binary) is None: pytest.skip(f"{binary} not installed")


def test_vibrate_short_pulse():
    gate("termux-vibrate")
    vibrate.vibrate(50)


def test_toast_visible():
    gate("termux-toast")
    toast.show("termux-api-stc conformance",short=True)


@pytest.mark.interactive
def test_brightness_manual_guarded():
    gate("termux-brightness")
    # Deliberately avoid changing brightness automatically because the official CLI
    # provides no read-current-value operation needed for safe restoration.
    pytest.skip("manual campaign required: no safe restore source in this baseline")
