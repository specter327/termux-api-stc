from __future__ import annotations

import os

import pytest


def _is_termux() -> bool:
    prefix = os.environ.get("PREFIX", "")
    return bool(prefix and "com.termux" in prefix)


def pytest_collection_modifyitems(config, items):
    if _is_termux():
        return
    skip = pytest.mark.skip(reason="requires real Termux environment")
    for item in items:
        if item.get_closest_marker("device"):
            item.add_marker(skip)


def pytest_sessionfinish(session, exitstatus):
    """Mandatory reference-device campaigns may not silently pass with SKIPs."""
    if os.environ.get("TERMUX_API_STC_FAIL_ON_SKIP") != "1":
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    skipped = list(getattr(reporter, "stats", {}).get("skipped", ())) if reporter else []
    if skipped and session.exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    if os.environ.get("TERMUX_API_STC_FAIL_ON_SKIP") != "1":
        return
    count = len(terminalreporter.stats.get("skipped", ()))
    if count:
        terminalreporter.write_sep(
            "!",
            f"MANDATORY CAMPAIGN INVALID: {count} skipped test(s); zero SKIP required",
        )
