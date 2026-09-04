from typing import Literal
from .core.command import Command
_COMMAND = Command("termux-location")
Provider = Literal["gps","network","passive"]
Request = Literal["once","last","updates"]

def _args(provider: Provider, request: Request) -> tuple[str,...]:
    if provider not in {"gps","network","passive"}:
        raise ValueError(f"Unsupported provider: {provider}")
    if request not in {"once","last","updates"}:
        raise ValueError(f"Unsupported request: {request}")
    return ("-p", provider, "-r", request)

def get(*, provider: Provider="gps", request: Literal["once","last"]="once", timeout: float | None=30.0):
    return _COMMAND.json(*_args(provider,request), timeout=timeout)

async def get_async(*, provider: Provider="gps", request: Literal["once","last"]="once", timeout: float | None=30.0):
    return await _COMMAND.json_async(*_args(provider,request), timeout=timeout)

def stream_updates(*, provider: Provider="gps", startup_timeout: float | None=30.0):
    return _COMMAND.stream_lines(*_args(provider,"updates"), startup_timeout=startup_timeout)
