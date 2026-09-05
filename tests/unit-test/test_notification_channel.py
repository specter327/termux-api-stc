from __future__ import annotations

import pytest

import termux_api_stc.notification_channel as channels


def test_create_exact_argv(monkeypatch):
    captured = {}
    class Fake:
        def result(self, *args, **kwargs):
            captured["args"] = args
            return object()
    monkeypatch.setattr(channels, "_COMMAND", Fake())
    channels.create("alerts", "Critical alerts")
    assert captured["args"] == ("alerts", "Critical alerts")


def test_delete_exact_argv(monkeypatch):
    captured = {}
    class Fake:
        def result(self, *args, **kwargs):
            captured["args"] = args
            return object()
    monkeypatch.setattr(channels, "_COMMAND", Fake())
    channels.delete("alerts")
    assert captured["args"] == ("-d", "alerts")


@pytest.mark.parametrize("value", ["", " ", "\t"])
def test_create_rejects_empty_id(value):
    with pytest.raises(ValueError):
        channels.create(value, "name")


@pytest.mark.parametrize("value", ["", " ", "\t"])
def test_create_rejects_empty_name(value):
    with pytest.raises(ValueError):
        channels.create("id", value)


@pytest.mark.asyncio
async def test_create_async_exact(monkeypatch):
    captured = {}
    class Fake:
        async def result_async(self, *args, **kwargs):
            captured["args"] = args
            return object()
    monkeypatch.setattr(channels, "_COMMAND", Fake())
    await channels.create_async("alerts", "Alerts")
    assert captured["args"] == ("alerts", "Alerts")


@pytest.mark.asyncio
async def test_delete_async_exact(monkeypatch):
    captured = {}
    class Fake:
        async def result_async(self, *args, **kwargs):
            captured["args"] = args
            return object()
    monkeypatch.setattr(channels, "_COMMAND", Fake())
    await channels.delete_async("alerts")
    assert captured["args"] == ("-d", "alerts")
