"""Libreria Python para Termux:API y utilidades Termux relacionadas."""

from . import (
    audio,
    battery,
    brightness,
    call_log,
    camera,
    clipboard,
    contacts,
    dialog,
    download,
    fingerprint,
    infrared,
    job_scheduler,
    keystore,
    location,
    media_player,
    media_scanner,
    microphone,
    nfc,
    notification,
    opener,
    saf,
    sensor,
    share,
    sms,
    speech_to_text,
    storage,
    telephony,
    toast,
    torch,
    tts,
    usb,
    vibrate,
    volume,
    wallpaper,
    wifi,
)
from .core import (
    is_available,
    is_command_available,
    run,
    run_async,
    run_bytes,
    run_bytes_async,
    run_json,
    run_json_async,
    run_text,
    run_text_async,
    stream_bytes_async,
    stream_text_async,
)
from .exceptions import (
    TermuxAPICommandUnavailableError,
    TermuxAPICompanionUnavailableError,
    TermuxAPIError,
    TermuxAPIExecutionError,
    TermuxAPINotInstalledError,
    TermuxAPIPermissionError,
    TermuxAPIProtocolError,
    TermuxAPITimeoutError,
    TermuxAPIUnsupportedError,
)

__version__ = "2.1.0"

TERMUX_API_COMPATIBILITY = {
    "tested_against_termux_api_package": "0.59.1",
    "official_package": "termux-api",
}

TERMUX_API_BINARIES = [
    "termux-api-start", "termux-api-stop", "termux-audio-info",
    "termux-battery-status", "termux-brightness", "termux-call-log",
    "termux-camera-info", "termux-camera-photo", "termux-clipboard-get",
    "termux-clipboard-set", "termux-contact-list", "termux-dialog",
    "termux-download", "termux-fingerprint", "termux-infrared-frequencies",
    "termux-infrared-transmit", "termux-job-scheduler", "termux-keystore",
    "termux-location", "termux-media-player", "termux-media-scan",
    "termux-microphone-record", "termux-nfc", "termux-notification",
    "termux-notification-channel", "termux-notification-list",
    "termux-notification-remove", "termux-saf-create", "termux-saf-dirs",
    "termux-saf-ls", "termux-saf-managedir", "termux-saf-mkdir",
    "termux-saf-read", "termux-saf-rm", "termux-saf-stat",
    "termux-saf-write", "termux-sensor", "termux-share", "termux-sms-inbox",
    "termux-sms-list",
    "termux-sms-send", "termux-speech-to-text", "termux-storage-get",
    "termux-telephony-call", "termux-telephony-cellinfo",
    "termux-telephony-deviceinfo", "termux-toast", "termux-torch",
    "termux-tts-engines", "termux-tts-speak", "termux-usb",
    "termux-vibrate", "termux-volume", "termux-wallpaper",
    "termux-wifi-connectioninfo", "termux-wifi-enable", "termux-wifi-scaninfo",
]

TERMUX_TOOL_BINARIES = [
    "termux-open",
    "termux-open-url",
]


def available_apis():
    """Indica que comandos oficiales de Termux:API existen en PATH."""
    return {
        binary: is_command_available(binary)
        for binary in TERMUX_API_BINARIES
    }


def available_tools():
    """Indica que utilidades Termux adicionales existen en PATH."""
    return {
        binary: is_command_available(binary)
        for binary in TERMUX_TOOL_BINARIES
    }


__all__ = [
    "audio", "battery", "brightness", "call_log", "camera", "clipboard",
    "contacts", "dialog", "download", "fingerprint", "infrared",
    "job_scheduler", "keystore", "location", "media_player", "media_scanner",
    "microphone", "nfc", "notification", "opener", "saf", "sensor", "share",
    "sms", "speech_to_text", "storage", "telephony", "toast", "torch", "tts",
    "usb", "vibrate", "volume", "wallpaper", "wifi",
    "TERMUX_API_COMPATIBILITY", "TERMUX_API_BINARIES", "TERMUX_TOOL_BINARIES",
    "available_apis", "available_tools", "is_available", "is_command_available",
    "run", "run_async", "run_bytes", "run_bytes_async", "run_json",
    "run_json_async", "run_text", "run_text_async", "stream_bytes_async",
    "stream_text_async",
    "TermuxAPIError", "TermuxAPICommandUnavailableError",
    "TermuxAPICompanionUnavailableError", "TermuxAPIExecutionError",
    "TermuxAPINotInstalledError", "TermuxAPIPermissionError",
    "TermuxAPIProtocolError", "TermuxAPITimeoutError", "TermuxAPIUnsupportedError",
]
