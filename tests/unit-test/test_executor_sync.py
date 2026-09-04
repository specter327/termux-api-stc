import json, pytest
from termux_api_stc.core import Executor, CommandUnavailableError, ExecutionError, ExecutionTimeoutError

def test_missing_command(monkeypatch):
    monkeypatch.setenv("PATH", "")
    with pytest.raises(CommandUnavailableError):
        Executor().execute("termux-does-not-exist")

def test_stdout_bytes(env_with):
    _, make = env_with
    make("termux-x", "import sys; sys.stdout.buffer.write(b'abc')")
    r=Executor().execute("termux-x")
    assert r.stdout == b"abc" and r.stderr == b"" and r.returncode == 0

def test_stderr_is_preserved(env_with):
    _, make=env_with
    make("termux-x","import sys; sys.stderr.write('warning')")
    r=Executor().execute("termux-x")
    assert r.stderr == b"warning"

def test_nonzero_raises(env_with):
    _, make=env_with
    make("termux-x","import sys; sys.stderr.write('bad'); raise SystemExit(7)")
    with pytest.raises(ExecutionError) as e:
        Executor().execute("termux-x")
    assert e.value.returncode == 7
    assert e.value.stderr == b"bad"

def test_no_shell_interpretation(env_with, tmp_path):
    _, make=env_with
    marker=tmp_path/"PWNED"
    make("termux-x","import sys; print(sys.argv[1])")
    r=Executor().execute("termux-x",[f";touch {marker}"])
    assert not marker.exists()
    assert b";touch" in r.stdout

def test_stdin_bytes(env_with):
    _, make=env_with
    make("termux-x","import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())")
    r=Executor().execute("termux-x", input=b"\x00abc")
    assert r.stdout == b"\x00abc"

def test_timeout(env_with):
    _, make=env_with
    make("termux-x","import time; time.sleep(5)")
    with pytest.raises(ExecutionTimeoutError):
        Executor().execute("termux-x", timeout=0.05)

def test_duration_nonnegative(env_with):
    _, make=env_with
    make("termux-x","print('x')")
    assert Executor().execute("termux-x").duration >= 0
