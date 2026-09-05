import termux_api_stc as stc
from termux_api_stc._version import __version__ as source_version


def test_version_single_source():
    assert stc.__version__ == source_version
    assert stc.__version__ == "3.1.0a2"


def test_core_exports():
    for name in [
        "TermuxAPI", "Executor", "Command", "ExecutionResult",
        "CommandUnavailableError", "ExecutionError", "ExecutionTimeoutError",
        "ProtocolError", "PayloadState", "CapabilityState",
        "CapabilityObservation", "VersionReport", "version_report",
    ]:
        assert hasattr(stc, name)
