__version__ = "3.0.0a2"

from .api import TermuxAPI
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

__all__ = [
    "__version__","TermuxAPI","INSPECTED_CONTRACTS","UpstreamCommandContract","inspect_environment","OFFICIAL_COMMANDS",
    "OFFICIAL_COMMAND_SET","UPSTREAM_TERMUX_API_APP_VERSION",
    "UPSTREAM_TERMUX_API_PACKAGE_TREE","Command","Executor","ExecutionResult",
    "EnvironmentReport","TermuxAPIError","CommandUnavailableError",
    "ExecutionError","ExecutionTimeoutError","ProtocolError",
]
