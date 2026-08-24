"""Nucleo de ejecucion para comandos Termux:API y utilidades Termux."""

import asyncio
import json
import shutil
import subprocess
from typing import Any, AsyncIterator, List, Optional, Union

from .exceptions import (
    TermuxAPICommandUnavailableError,
    TermuxAPIExecutionError,
    TermuxAPINotInstalledError,
    TermuxAPIProtocolError,
    TermuxAPITimeoutError,
)

InputData = Optional[Union[str, bytes]]


def is_command_available(binary: str) -> bool:
    """Indica si un comando existe en el PATH actual."""
    return shutil.which(binary) is not None


def is_available(binary: str) -> bool:
    """Mantiene compatibilidad con el nombre historico de disponibilidad."""
    return is_command_available(binary)


def _require_command(binary: str) -> None:
    """Valida que un comando se encuentre disponible."""
    if is_command_available(binary):
        return

    raise TermuxAPINotInstalledError(
        "'{}' no se encontro en el PATH. Instala el paquete que proporciona "
        "el comando y verifica que el proceso se ejecute dentro de Termux.".format(
            binary
        )
    )


def _normalize_input(input_data: InputData) -> Optional[bytes]:
    """Convierte la entrada opcional al formato binario de subprocess."""
    if input_data is None:
        return None
    if isinstance(input_data, bytes):
        return input_data
    return input_data.encode("utf-8")


def _execute_bytes(
    binary: str,
    args: Optional[List[str]] = None,
    input_data: InputData = None,
    timeout: Optional[float] = None,
) -> bytes:
    """Ejecuta sincronicamente un comando y devuelve stdout binario."""
    _require_command(binary)
    command = [binary] + (args or [])

    try:
        process = subprocess.run(
            command,
            input=_normalize_input(input_data),
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise TermuxAPITimeoutError(
            "El comando '{}' supero el timeout de {}s".format(
                " ".join(command),
                timeout,
            )
        ) from exc

    if process.returncode != 0:
        raise TermuxAPIExecutionError(
            command,
            process.returncode,
            process.stderr or b"",
        )

    return process.stdout or b""


def run_bytes(
    binary: str,
    args: Optional[List[str]] = None,
    input_data: InputData = None,
    timeout: Optional[float] = None,
) -> bytes:
    """Ejecuta un comando y devuelve stdout exactamente como bytes."""
    return _execute_bytes(
        binary=binary,
        args=args,
        input_data=input_data,
        timeout=timeout,
    )


def run_text(
    binary: str,
    args: Optional[List[str]] = None,
    input_data: InputData = None,
    timeout: Optional[float] = None,
    strip: bool = True,
) -> Optional[str]:
    """Ejecuta un comando y devuelve stdout como texto UTF-8."""
    output = _execute_bytes(
        binary=binary,
        args=args,
        input_data=input_data,
        timeout=timeout,
    ).decode("utf-8", errors="replace")

    if strip:
        output = output.strip()

    return output if output else None


def run_json(
    binary: str,
    args: Optional[List[str]] = None,
    input_data: InputData = None,
    timeout: Optional[float] = None,
) -> Any:
    """Ejecuta un comando que debe responder JSON valido."""
    output = run_text(
        binary=binary,
        args=args,
        input_data=input_data,
        timeout=timeout,
    )

    if output is None:
        return None

    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise TermuxAPIProtocolError(
            "El comando '{}' devolvio una respuesta JSON invalida".format(binary)
        ) from exc


def run(
    binary: str,
    args: Optional[List[str]] = None,
    input_data: InputData = None,
    timeout: Optional[float] = None,
    parse_json: bool = True,
) -> Any:
    """Ejecuta un comando conservando la semantica compatible de la v1."""
    output = run_text(
        binary=binary,
        args=args,
        input_data=input_data,
        timeout=timeout,
    )

    if not parse_json or output is None:
        return output

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return output


async def _execute_bytes_async(
    binary: str,
    args: Optional[List[str]] = None,
    input_data: InputData = None,
    timeout: Optional[float] = None,
) -> bytes:
    """Ejecuta asincronicamente un comando y devuelve stdout binario."""
    _require_command(binary)
    command = [binary] + (args or [])

    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE if input_data is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        communication = process.communicate(_normalize_input(input_data))
        if timeout is None:
            stdout, stderr = await communication
        else:
            stdout, stderr = await asyncio.wait_for(communication, timeout=timeout)
    except asyncio.TimeoutError as exc:
        process.kill()
        await process.wait()
        raise TermuxAPITimeoutError(
            "El comando '{}' supero el timeout de {}s".format(
                " ".join(command),
                timeout,
            )
        ) from exc

    if process.returncode != 0:
        raise TermuxAPIExecutionError(
            command,
            int(process.returncode or 0),
            stderr or b"",
        )

    return stdout or b""


async def run_bytes_async(
    binary: str,
    args: Optional[List[str]] = None,
    input_data: InputData = None,
    timeout: Optional[float] = None,
) -> bytes:
    """Ejecuta asincronicamente y devuelve stdout binario."""
    return await _execute_bytes_async(
        binary=binary,
        args=args,
        input_data=input_data,
        timeout=timeout,
    )


async def run_text_async(
    binary: str,
    args: Optional[List[str]] = None,
    input_data: InputData = None,
    timeout: Optional[float] = None,
    strip: bool = True,
) -> Optional[str]:
    """Ejecuta asincronicamente y devuelve stdout como texto."""
    output = (
        await _execute_bytes_async(
            binary=binary,
            args=args,
            input_data=input_data,
            timeout=timeout,
        )
    ).decode("utf-8", errors="replace")

    if strip:
        output = output.strip()

    return output if output else None


async def run_json_async(
    binary: str,
    args: Optional[List[str]] = None,
    input_data: InputData = None,
    timeout: Optional[float] = None,
) -> Any:
    """Ejecuta asincronicamente un comando que debe responder JSON."""
    output = await run_text_async(
        binary=binary,
        args=args,
        input_data=input_data,
        timeout=timeout,
    )

    if output is None:
        return None

    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise TermuxAPIProtocolError(
            "El comando '{}' devolvio una respuesta JSON invalida".format(binary)
        ) from exc


async def run_async(
    binary: str,
    args: Optional[List[str]] = None,
    input_data: InputData = None,
    timeout: Optional[float] = None,
    parse_json: bool = True,
) -> Any:
    """Ejecuta asincronicamente conservando la semantica compatible de run()."""
    output = await run_text_async(
        binary=binary,
        args=args,
        input_data=input_data,
        timeout=timeout,
    )

    if not parse_json or output is None:
        return output

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return output

async def stream_bytes_async(
    binary: str,
    args: Optional[List[str]] = None,
    input_data: InputData = None,
    chunk_size: int = 4096,
) -> AsyncIterator[bytes]:
    """Transmite stdout binario incrementalmente sin bloquear el event loop."""
    if chunk_size < 1:
        raise ValueError("chunk_size debe ser >= 1")

    _require_command(binary)
    command = [binary] + (args or [])

    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE if input_data is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    if process.stdout is None or process.stderr is None:
        process.kill()
        await process.wait()
        raise TermuxAPIProtocolError(
            "No fue posible abrir los canales del proceso '{}'".format(binary)
        )

    if input_data is not None and process.stdin is not None:
        process.stdin.write(_normalize_input(input_data) or b"")
        await process.stdin.drain()
        process.stdin.close()

    stderr_task = asyncio.create_task(process.stderr.read())

    try:
        while True:
            chunk = await process.stdout.read(chunk_size)
            if not chunk:
                break
            yield chunk

        return_code = await process.wait()
        stderr = await stderr_task

        if return_code != 0:
            raise TermuxAPIExecutionError(
                command,
                int(return_code),
                stderr or b"",
            )
    except asyncio.CancelledError:
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

        if not stderr_task.done():
            stderr_task.cancel()

        raise
    finally:
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

        if not stderr_task.done():
            stderr_task.cancel()


async def stream_text_async(
    binary: str,
    args: Optional[List[str]] = None,
    input_data: InputData = None,
    encoding: str = "utf-8",
) -> AsyncIterator[str]:
    """Transmite stdout incrementalmente por lineas de texto."""
    _require_command(binary)
    command = [binary] + (args or [])

    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE if input_data is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    if process.stdout is None or process.stderr is None:
        process.kill()
        await process.wait()
        raise TermuxAPIProtocolError(
            "No fue posible abrir los canales del proceso '{}'".format(binary)
        )

    if input_data is not None and process.stdin is not None:
        process.stdin.write(_normalize_input(input_data) or b"")
        await process.stdin.drain()
        process.stdin.close()

    stderr_task = asyncio.create_task(process.stderr.read())

    try:
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            yield line.decode(encoding, errors="replace").rstrip("\r\n")

        return_code = await process.wait()
        stderr = await stderr_task

        if return_code != 0:
            raise TermuxAPIExecutionError(
                command,
                int(return_code),
                stderr or b"",
            )
    except asyncio.CancelledError:
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

        if not stderr_task.done():
            stderr_task.cancel()

        raise
    finally:
        if process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

        if not stderr_task.done():
            stderr_task.cancel()

