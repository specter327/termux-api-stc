__version__ = "3.0.0a1"

from .api import TermuxAPI
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
    "__version__","TermuxAPI","inspect_environment","OFFICIAL_COMMANDS",
    "OFFICIAL_COMMAND_SET","UPSTREAM_TERMUX_API_APP_VERSION",
    "UPSTREAM_TERMUX_API_PACKAGE_TREE","Command","Executor","ExecutionResult",
    "EnvironmentReport","TermuxAPIError","CommandUnavailableError",
    "ExecutionError","ExecutionTimeoutError","ProtocolError",
]
