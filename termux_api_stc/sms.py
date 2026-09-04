from __future__ import annotations
from collections.abc import Sequence
from typing import Literal
from .core.command import Command
from .core.models import ExecutionResult

_LIST = Command("termux-sms-list")
_SEND = Command("termux-sms-send")
MessageType = Literal["all", "inbox", "sent", "draft", "outbox", "failed", "queued"]


def _query_args(*, limit: int, offset: int, message_type: MessageType, address: str | None, conversation_list: bool) -> tuple[str, ...]:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError("limit must be a non-negative integer")
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    allowed = {"all", "inbox", "sent", "draft", "outbox", "failed", "queued"}
    if message_type not in allowed:
        raise ValueError(f"unsupported message_type: {message_type}")
    args: list[str] = ["-l", str(limit), "-o", str(offset), "-t", message_type]
    if address is not None:
        args.extend(("-f", address))
    if conversation_list:
        args.append("-c")
    return tuple(args)


def list_result(*, limit: int = 10, offset: int = 0, message_type: MessageType = "all", address: str | None = None, conversation_list: bool = False, timeout: float | None = 30.0) -> ExecutionResult:
    return _LIST.result(*_query_args(limit=limit, offset=offset, message_type=message_type, address=address, conversation_list=conversation_list), timeout=timeout)


def list_json(*, limit: int = 10, offset: int = 0, message_type: MessageType = "all", address: str | None = None, conversation_list: bool = False, timeout: float | None = 30.0):
    return _LIST.json(*_query_args(limit=limit, offset=offset, message_type=message_type, address=address, conversation_list=conversation_list), timeout=timeout)


async def list_result_async(*, limit: int = 10, offset: int = 0, message_type: MessageType = "all", address: str | None = None, conversation_list: bool = False, timeout: float | None = 30.0) -> ExecutionResult:
    return await _LIST.result_async(*_query_args(limit=limit, offset=offset, message_type=message_type, address=address, conversation_list=conversation_list), timeout=timeout)


async def list_json_async(*, limit: int = 10, offset: int = 0, message_type: MessageType = "all", address: str | None = None, conversation_list: bool = False, timeout: float | None = 30.0):
    return await _LIST.json_async(*_query_args(limit=limit, offset=offset, message_type=message_type, address=address, conversation_list=conversation_list), timeout=timeout)


def _recipients(value: str | Sequence[str]) -> str:
    if isinstance(value, str):
        result = value
    else:
        result = ",".join(value)
    if not result:
        raise ValueError("at least one recipient is required")
    return result


def send(recipients: str | Sequence[str], text: str, *, slot: int | None = None, timeout: float | None = 30.0) -> ExecutionResult:
    args: list[str] = ["-n", _recipients(recipients)]
    if slot is not None:
        if isinstance(slot, bool) or not isinstance(slot, int) or slot < 0:
            raise ValueError("slot must be a non-negative integer")
        args.extend(("-s", str(slot)))
    return _SEND.result(*args, input=text.encode("utf-8"), timeout=timeout)


async def send_async(recipients: str | Sequence[str], text: str, *, slot: int | None = None, timeout: float | None = 30.0) -> ExecutionResult:
    args: list[str] = ["-n", _recipients(recipients)]
    if slot is not None:
        if isinstance(slot, bool) or not isinstance(slot, int) or slot < 0:
            raise ValueError("slot must be a non-negative integer")
        args.extend(("-s", str(slot)))
    return await _SEND.result_async(*args, input=text.encode("utf-8"), timeout=timeout)
