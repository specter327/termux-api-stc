import pytest
from termux_api_stc.core import Command

def test_command_result(env_with):
    _,make=env_with; make("termux-x","print('ok')")
    assert Command("termux-x").result().stdout.strip()==b"ok"

def test_command_bytes(env_with):
    _,make=env_with; make("termux-x","import sys;sys.stdout.buffer.write(b'xx')")
    assert Command("termux-x").bytes()==b"xx"

def test_command_text(env_with):
    _,make=env_with; make("termux-x","print('hello')")
    assert Command("termux-x").text().strip()=="hello"

def test_command_json(env_with):
    _,make=env_with; make("termux-x","print('{\"ok\":true}')")
    assert Command("termux-x").json()=={"ok":True}

@pytest.mark.asyncio
async def test_command_async_text(env_with):
    _,make=env_with; make("termux-x","print('hello')")
    assert (await Command("termux-x").text_async()).strip()=="hello"

@pytest.mark.asyncio
async def test_command_async_json(env_with):
    _,make=env_with; make("termux-x","print('{\"ok\":true}')")
    assert await Command("termux-x").json_async()=={"ok":True}
