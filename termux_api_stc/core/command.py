from __future__ import annotations
from typing import AsyncIterator, Sequence
from .executor import Executor
from .models import ExecutionResult

class Command:
    def __init__(self, binary: str, executor: Executor | None = None) -> None:
        self.binary = binary
        self.executor = executor or Executor()

    def result(self, *args: str, input: bytes | None = None, timeout: float | None = None) -> ExecutionResult:
        return self.executor.execute(self.binary, args, input=input, timeout=timeout)

    def bytes(self, *args: str, input: bytes | None = None, timeout: float | None = None) -> bytes:
        return self.result(*args, input=input, timeout=timeout).stdout

    def text(self, *args: str, input: bytes | None = None, timeout: float | None = None) -> str:
        return self.executor.text(self.result(*args, input=input, timeout=timeout))

    def json(self, *args: str, input: bytes | None = None, timeout: float | None = None):
        return self.executor.json(self.result(*args, input=input, timeout=timeout))

    async def result_async(self, *args: str, input: bytes | None = None, timeout: float | None = None) -> ExecutionResult:
        return await self.executor.execute_async(self.binary, args, input=input, timeout=timeout)

    async def bytes_async(self, *args: str, input: bytes | None = None, timeout: float | None = None) -> bytes:
        return (await self.result_async(*args, input=input, timeout=timeout)).stdout

    async def text_async(self, *args: str, input: bytes | None = None, timeout: float | None = None) -> str:
        return self.executor.text(await self.result_async(*args, input=input, timeout=timeout))

    async def json_async(self, *args: str, input: bytes | None = None, timeout: float | None = None):
        return self.executor.json(await self.result_async(*args, input=input, timeout=timeout))


    def json_if_present(self, *args: str, input: bytes | None = None, timeout: float | None = None):
        return self.executor.json_if_present(self.result(*args, input=input, timeout=timeout))

    async def json_if_present_async(self, *args: str, input: bytes | None = None, timeout: float | None = None):
        return self.executor.json_if_present(await self.result_async(*args, input=input, timeout=timeout))

    def stream_lines(self, *args: str, startup_timeout: float | None = None) -> AsyncIterator[str]:
        return self.executor.stream_lines(self.binary, args, startup_timeout=startup_timeout)
