import pytest
from termux_api_stc import OFFICIAL_COMMANDS, TermuxAPI

@pytest.mark.parametrize("binary", OFFICIAL_COMMANDS)
def test_official_command_facade_is_exact(binary):
    cmd=TermuxAPI().command(binary)
    assert cmd.binary == binary
