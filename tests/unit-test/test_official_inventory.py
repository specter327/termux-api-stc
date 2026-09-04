from termux_api_stc.official import OFFICIAL_COMMANDS, OFFICIAL_COMMAND_SET, UPSTREAM_TERMUX_API_PACKAGE_TREE

def test_inventory_count():
    assert len(OFFICIAL_COMMANDS) == 57

def test_inventory_unique():
    assert len(OFFICIAL_COMMANDS) == len(OFFICIAL_COMMAND_SET)

def test_inventory_names_are_termux_commands():
    assert all(x.startswith("termux-") for x in OFFICIAL_COMMANDS)

def test_pinned_tree_sha():
    assert UPSTREAM_TERMUX_API_PACKAGE_TREE == "0e3f9222eea7760c76ea6368dadbdf884ab85fbf"

def test_every_expected_command_present():
    expected = ['termux-api-start', 'termux-api-stop', 'termux-audio-info', 'termux-battery-status', 'termux-brightness', 'termux-call-log', 'termux-camera-info', 'termux-camera-photo', 'termux-clipboard-get', 'termux-clipboard-set', 'termux-contact-list', 'termux-dialog', 'termux-download', 'termux-fingerprint', 'termux-infrared-frequencies', 'termux-infrared-transmit', 'termux-job-scheduler', 'termux-keystore', 'termux-location', 'termux-media-player', 'termux-media-scan', 'termux-microphone-record', 'termux-nfc', 'termux-notification', 'termux-notification-channel', 'termux-notification-list', 'termux-notification-remove', 'termux-saf-create', 'termux-saf-dirs', 'termux-saf-ls', 'termux-saf-managedir', 'termux-saf-mkdir', 'termux-saf-read', 'termux-saf-rm', 'termux-saf-stat', 'termux-saf-write', 'termux-sensor', 'termux-share', 'termux-sms-inbox', 'termux-sms-list', 'termux-sms-send', 'termux-speech-to-text', 'termux-storage-get', 'termux-telephony-call', 'termux-telephony-cellinfo', 'termux-telephony-deviceinfo', 'termux-toast', 'termux-torch', 'termux-tts-engines', 'termux-tts-speak', 'termux-usb', 'termux-vibrate', 'termux-volume', 'termux-wallpaper', 'termux-wifi-connectioninfo', 'termux-wifi-enable', 'termux-wifi-scaninfo']
    assert OFFICIAL_COMMANDS == expected
