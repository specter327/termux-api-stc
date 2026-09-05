from __future__ import annotations

from .core.command import Command
from .core.errors import CommandUnavailableError, ExecutionError
from .core.models import CapabilityObservation, CapabilityState


def observe_command(binary: str, *args: str, timeout: float | None = 15.0) -> CapabilityObservation:
    """Conservative capability observation.

    This function does not invent fine-grained error classifications. It only
    records what can be demonstrated from the command boundary.
    """
    command = Command(binary)
    try:
        result = command.result(*args, timeout=timeout)
    except CommandUnavailableError:
        return CapabilityObservation(
            command=binary,
            command_available=False,
            state=CapabilityState.UNAVAILABLE,
            evidence="command not found in PATH",
        )
    except ExecutionError as exc:
        return CapabilityObservation(
            command=binary,
            command_available=True,
            state=CapabilityState.UNKNOWN,
            evidence=f"command executed with non-zero exit code {exc.returncode}",
        )

    if result.stdout:
        return CapabilityObservation(
            command=binary,
            command_available=True,
            state=CapabilityState.AVAILABLE,
            evidence=f"command succeeded with {result.payload_state.value.lower()} stdout",
            result=result,
        )

    return CapabilityObservation(
        command=binary,
        command_available=True,
        state=CapabilityState.UNKNOWN,
        evidence="command succeeded with empty stdout; capability cannot be inferred",
        result=result,
    )


def infrared() -> CapabilityObservation:
    return observe_command("termux-infrared-frequencies")
