class TermuxAPIError(Exception):
    """Base error for termux-api-stc."""

class CommandUnavailableError(TermuxAPIError):
    def __init__(self, binary: str):
        self.binary = binary
        super().__init__(f"Command unavailable: {binary}")

class ExecutionError(TermuxAPIError):
    def __init__(self, argv, returncode: int, stdout: bytes, stderr: bytes):
        self.argv = tuple(argv)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        message = stderr.decode("utf-8", "replace").strip() or f"exit code {returncode}"
        super().__init__(f"{self.argv[0]} failed: {message}")

class ExecutionTimeoutError(TermuxAPIError):
    def __init__(self, argv, timeout):
        self.argv = tuple(argv)
        self.timeout = timeout
        super().__init__(f"{self.argv[0]} timed out after {timeout}s")

class ProtocolError(TermuxAPIError):
    pass
