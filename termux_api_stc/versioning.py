from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata

from ._version import __version__


@dataclass(frozen=True, slots=True)
class VersionReport:
    runtime: str
    distribution: str | None

    @property
    def consistent(self) -> bool:
        return self.distribution is None or self.distribution == self.runtime


def distribution_version() -> str | None:
    """Return installed distribution version, or None for an uninstalled source tree."""
    try:
        return metadata.version("termux-api-stc")
    except metadata.PackageNotFoundError:
        return None


def version_report() -> VersionReport:
    return VersionReport(runtime=__version__, distribution=distribution_version())
