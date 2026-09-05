from __future__ import annotations

import termux_api_stc.versioning as versioning


def test_version_report_without_distribution(monkeypatch):
    monkeypatch.setattr(versioning, "distribution_version", lambda: None)
    report = versioning.version_report()
    assert report.runtime
    assert report.distribution is None
    assert report.consistent


def test_version_report_matching(monkeypatch):
    monkeypatch.setattr(versioning, "distribution_version", lambda: versioning.__version__)
    report = versioning.version_report()
    assert report.consistent


def test_version_report_mismatch(monkeypatch):
    monkeypatch.setattr(versioning, "distribution_version", lambda: "0.0.0")
    report = versioning.version_report()
    assert not report.consistent
