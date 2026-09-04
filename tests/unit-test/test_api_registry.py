import pytest
from termux_api_stc import TermuxAPI, OFFICIAL_COMMANDS

def test_every_official_command_resolvable_as_facade():
    api=TermuxAPI()
    for name in OFFICIAL_COMMANDS:
        assert api.command(name).binary==name

def test_unknown_command_rejected():
    with pytest.raises(KeyError):
        TermuxAPI().command("rm")

def test_getitem():
    assert TermuxAPI()["termux-battery-status"].binary=="termux-battery-status"
