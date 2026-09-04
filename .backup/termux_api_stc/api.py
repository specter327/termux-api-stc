from __future__ import annotations
from .core.command import Command
from .core.executor import Executor
from .official import OFFICIAL_COMMAND_SET

class TermuxAPI:
    """Faithful low-level consumer of the pinned official command surface."""

    def __init__(self, executor: Executor | None = None) -> None:
        self.executor = executor or Executor()

    def command(self, binary: str) -> Command:
        if binary not in OFFICIAL_COMMAND_SET:
            raise KeyError(f"Not in pinned official baseline: {binary}")
        return Command(binary, self.executor)

    def __getitem__(self, binary: str) -> Command:
        return self.command(binary)
