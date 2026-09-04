import pytest
from termux_api_stc.core import Executor, ProtocolError

def test_text_strict_utf8(env_with):
    _, make=env_with
    make("termux-x","print('á')")
    ex=Executor()
    assert ex.text(ex.execute("termux-x")).strip()=="á"

def test_text_empty_is_empty_string(env_with):
    _, make=env_with
    make("termux-x","pass")
    ex=Executor()
    assert ex.text(ex.execute("termux-x"))==""

def test_json_object(env_with):
    _, make=env_with
    make("termux-x","print('{\"a\": 1}')")
    ex=Executor()
    assert ex.json(ex.execute("termux-x"))=={"a":1}

def test_json_array(env_with):
    _, make=env_with
    make("termux-x","print('[1,2]')")
    ex=Executor()
    assert ex.json(ex.execute("termux-x"))==[1,2]

def test_invalid_json(env_with):
    _, make=env_with
    make("termux-x","print('not json')")
    ex=Executor()
    with pytest.raises(ProtocolError):
        ex.json(ex.execute("termux-x"))
