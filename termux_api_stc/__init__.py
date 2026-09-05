from ._version import __version__
from .api import TermuxAPI
from .versioning import distribution_version, version_report, VersionReport
from .capabilities import observe_command
from .contracts import INSPECTED_CONTRACTS, UpstreamCommandContract
from .environment import inspect_environment
from .official import (
    OFFICIAL_COMMANDS,
    OFFICIAL_COMMAND_SET,
    UPSTREAM_TERMUX_API_APP_VERSION,
    UPSTREAM_TERMUX_API_PACKAGE_TREE,
)
from .core import (
    Command,
    Executor,
    ExecutionResult,
    EnvironmentReport,
    TermuxAPIError,
    CommandUnavailableError,
    ExecutionError,
    ExecutionTimeoutError,
    ProtocolError,
)
from .core.models import CapabilityObservation, CapabilityState, PayloadState

__all__ = [
    "__version__", "TermuxAPI", "distribution_version", "version_report", "VersionReport", "observe_command", "INSPECTED_CONTRACTS",
    "UpstreamCommandContract", "inspect_environment", "OFFICIAL_COMMANDS",
    "OFFICIAL_COMMAND_SET", "UPSTREAM_TERMUX_API_APP_VERSION",
    "UPSTREAM_TERMUX_API_PACKAGE_TREE", "Command", "Executor", "ExecutionResult",
    "EnvironmentReport", "CapabilityObservation", "CapabilityState", "PayloadState",
    "TermuxAPIError", "CommandUnavailableError", "ExecutionError",
    "ExecutionTimeoutError", "ProtocolError",
]
