"""Pinned official command inventory.

Source:
termux/termux-api-package CMakeLists.txt, master tree
baseline tree SHA: 0e3f9222eea7760c76ea6368dadbdf884ab85fbf
"""
UPSTREAM_TERMUX_API_APP_VERSION = "0.53.0"
UPSTREAM_TERMUX_API_PACKAGE_TREE = "0e3f9222eea7760c76ea6368dadbdf884ab85fbf"

OFFICIAL_COMMANDS = ['termux-api-start', 'termux-api-stop', 'termux-audio-info', 'termux-battery-status', 'termux-brightness', 'termux-call-log', 'termux-camera-info', 'termux-camera-photo', 'termux-clipboard-get', 'termux-clipboard-set', 'termux-contact-list', 'termux-dialog', 'termux-download', 'termux-fingerprint', 'termux-infrared-frequencies', 'termux-infrared-transmit', 'termux-job-scheduler', 'termux-keystore', 'termux-location', 'termux-media-player', 'termux-media-scan', 'termux-microphone-record', 'termux-nfc', 'termux-notification', 'termux-notification-channel', 'termux-notification-list', 'termux-notification-remove', 'termux-saf-create', 'termux-saf-dirs', 'termux-saf-ls', 'termux-saf-managedir', 'termux-saf-mkdir', 'termux-saf-read', 'termux-saf-rm', 'termux-saf-stat', 'termux-saf-write', 'termux-sensor', 'termux-share', 'termux-sms-inbox', 'termux-sms-list', 'termux-sms-send', 'termux-speech-to-text', 'termux-storage-get', 'termux-telephony-call', 'termux-telephony-cellinfo', 'termux-telephony-deviceinfo', 'termux-toast', 'termux-torch', 'termux-tts-engines', 'termux-tts-speak', 'termux-usb', 'termux-vibrate', 'termux-volume', 'termux-wallpaper', 'termux-wifi-connectioninfo', 'termux-wifi-enable', 'termux-wifi-scaninfo']
OFFICIAL_COMMAND_SET = frozenset(OFFICIAL_COMMANDS)
