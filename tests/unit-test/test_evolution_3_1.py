from __future__ import annotations

import json

from termux_api_stc.capabilities import observe_command
from termux_api_stc.core import Command, Executor
from termux_api_stc.core.models import CapabilityState, ExecutionResult, PayloadState


def test_execution_result_empty_payload():
    result = ExecutionResult(("x",), 0, b"", b"", 0.0)
    assert result.payload_state is PayloadState.EMPTY
    assert not result.has_stdout
    assert not result.has_stderr


def test_execution_result_nonempty_payload():
    result = ExecutionResult(("x",), 0, b"{}", b"warn", 0.0)
    assert result.payload_state is PayloadState.NONEMPTY
    assert result.has_stdout
    assert result.has_stderr


def test_json_if_present_empty():
    result = ExecutionResult(("x",), 0, b"", b"", 0.0)
    assert Executor().json_if_present(result) is None


def test_json_if_present_payload():
    result = ExecutionResult(("x",), 0, b'{"ok": true}', b"", 0.0)
    assert Executor().json_if_present(result) == {"ok": True}


def test_observe_command_missing(monkeypatch):
    monkeypatch.setenv("PATH", "")
    observation = observe_command("termux-missing-test")
    assert observation.command_available is False
    assert observation.state is CapabilityState.UNAVAILABLE
    assert observation.result is None


def test_observe_command_empty_success(env_with):
    _, make = env_with
    make("termux-observe-empty", "pass")
    observation = observe_command("termux-observe-empty")
    assert observation.command_available is True
    assert observation.state is CapabilityState.UNKNOWN
    assert observation.result is not None
    assert observation.result.payload_state is PayloadState.EMPTY


def test_observe_command_payload_success(env_with):
    _, make = env_with
    make("termux-observe-data", "print('{}')")
    observation = observe_command("termux-observe-data")
    assert observation.command_available is True
    assert observation.state is CapabilityState.AVAILABLE
    assert observation.result is not None
    assert observation.result.payload_state is PayloadState.NONEMPTY
