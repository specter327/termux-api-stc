import termux_api_stc as stc

def test_version():
    assert stc.__version__=="3.0.0a2"

def test_core_exports():
    for name in [
        "TermuxAPI","Executor","Command","ExecutionResult",
        "CommandUnavailableError","ExecutionError","ExecutionTimeoutError","ProtocolError"
    ]:
        assert hasattr(stc,name)
