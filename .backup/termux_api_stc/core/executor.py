from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import time
from contextlib import suppress
from typing import AsyncIterator, Mapping, Sequence

from .errors import CommandUnavailableError, ExecutionError, ExecutionTimeoutError, ProtocolError
from .models import ExecutionResult

class Executor:
    """Strict subprocess executor for official Termux CLI commands.

    Invariants:
    - never invokes a shell;
    - argv is passed as a sequence;
    - stdout/stderr remain bytes at the execution boundary;
    - non-zero return codes raise ExecutionError;
    - timeout/cancellation terminates child processes.
    """

    def __init__(
        self,
        *,
        env: Mapping[str, str] | None = None,
        cwd: str | os.PathLike[str] | None = None,
        encoding: str = "utf-8",
    ) -> None:
        self._env = dict(env) if env is not None else None
        self._cwd = cwd
        self.encoding = encoding

    def resolve(self, binary: str) -> str:
        resolved = shutil.which(binary, path=(self._env or os.environ).get("PATH"))
        if not resolved:
            raise CommandUnavailableError(binary)
        return resolved

    def execute(
        self,
        binary: str,
        args: Sequence[str] = (),
        *,
        input: bytes | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        executable = self.resolve(binary)
        argv = (executable, *(str(x) for x in args))
        started = time.monotonic()
        try:
            cp = subprocess.run(
                argv,
                input=input,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self._cwd,
                env=self._env,
                shell=False,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ExecutionTimeoutError(argv, timeout) from exc

        result = ExecutionResult(
            argv=tuple(argv),
            returncode=cp.returncode,
            stdout=cp.stdout,
            stderr=cp.stderr,
            duration=time.monotonic() - started,
        )
        if not result.ok:
            raise ExecutionError(result.argv, result.returncode, result.stdout, result.stderr)
        return result

    async def execute_async(
        self,
        binary: str,
        args: Sequence[str] = (),
        *,
        input: bytes | None = None,
        timeout: float | None = None,
    ) -> ExecutionResult:
        executable = self.resolve(binary)
        argv = (executable, *(str(x) for x in args))
        started = time.monotonic()
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.PIPE if input is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self._cwd,
            env=self._env,
        )
        try:
            operation = process.communicate(input)
            if timeout is None:
                stdout, stderr = await operation
            else:
                stdout, stderr = await asyncio.wait_for(operation, timeout)
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.wait()
            raise ExecutionTimeoutError(argv, timeout) from exc
        except asyncio.CancelledError:
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), 1.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
            raise

        result = ExecutionResult(
            argv=tuple(argv),
            returncode=process.returncode or 0,
            stdout=stdout,
            stderr=stderr,
            duration=time.monotonic() - started,
        )
        if not result.ok:
            raise ExecutionError(result.argv, result.returncode, result.stdout, result.stderr)
        return result

    async def stream_lines(
        self,
        binary: str,
        args: Sequence[str] = (),
        *,
        startup_timeout: float | None = None,
    ) -> AsyncIterator[str]:
        executable = self.resolve(binary)
        argv = (executable, *(str(x) for x in args))
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self._cwd,
            env=self._env,
        )
        assert process.stdout is not None
        assert process.stderr is not None
        stderr_task = asyncio.create_task(process.stderr.read())

        try:
            first = True
            while True:
                read = process.stdout.readline()
                if first and startup_timeout is not None:
                    try:
                        line = await asyncio.wait_for(read, startup_timeout)
                    except asyncio.TimeoutError as exc:
                        process.kill()
                        await process.wait()
                        raise ExecutionTimeoutError(argv, startup_timeout) from exc
                else:
                    line = await read
                first = False
                if not line:
                    break
                yield line.decode(self.encoding, "strict").rstrip("\n")

            rc = await process.wait()
            stderr = await stderr_task
            if rc != 0:
                raise ExecutionError(argv, rc, b"", stderr)
        except asyncio.CancelledError:
            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), 1.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
            raise
        finally:
            if not stderr_task.done():
                stderr_task.cancel()
                with suppress(asyncio.CancelledError):
                    await stderr_task

    def text(self, result: ExecutionResult) -> str:
        return result.stdout.decode(self.encoding, "strict")

    def json(self, result: ExecutionResult):
        try:
            return json.loads(self.text(result))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProtocolError(f"Invalid JSON from {result.argv[0]}") from exc
