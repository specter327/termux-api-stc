from __future__ import annotations

from pathlib import Path
from .core.command import Command

_CREATE = Command("termux-notification")
_LIST = Command("termux-notification-list")
_REMOVE = Command("termux-notification-remove")

_PRIORITIES = {"high", "low", "max", "min", "default"}
_TYPES = {"default", "media"}


def _create_args(
    *,
    title: str | None = None,
    notification_id: str | None = None,
    channel: str | None = None,
    group: str | None = None,
    icon: str | None = None,
    image_path: str | Path | None = None,
    ongoing: bool = False,
    priority: str | None = None,
    sound: bool = False,
    notification_type: str | None = None,
) -> tuple[str, ...]:
    if ongoing and not notification_id:
        raise ValueError("ongoing notifications require notification_id")
    if priority is not None and priority not in _PRIORITIES:
        raise ValueError(f"unsupported priority: {priority}")
    if notification_type is not None and notification_type not in _TYPES:
        raise ValueError(f"unsupported notification_type: {notification_type}")

    args: list[str] = []
    if title is not None: args += ["--title", title]
    if notification_id is not None: args += ["--id", notification_id]
    if channel is not None: args += ["--channel", channel]
    if group is not None: args += ["--group", group]
    if icon is not None: args += ["--icon", icon]
    if image_path is not None: args += ["--image-path", str(Path(image_path).expanduser().resolve())]
    if ongoing: args += ["--ongoing"]
    if priority is not None: args += ["--priority", priority]
    if sound: args += ["--sound"]
    if notification_type is not None: args += ["--type", notification_type]
    return tuple(args)


def show(
    content: str,
    *,
    title: str | None = None,
    notification_id: str | None = None,
    channel: str | None = None,
    group: str | None = None,
    icon: str | None = None,
    image_path: str | Path | None = None,
    ongoing: bool = False,
    priority: str | None = None,
    sound: bool = False,
    notification_type: str | None = None,
    timeout: float | None = 15.0,
):
    args = _create_args(
        title=title, notification_id=notification_id, channel=channel, group=group,
        icon=icon, image_path=image_path, ongoing=ongoing, priority=priority,
        sound=sound, notification_type=notification_type,
    )
    return _CREATE.result(*args, input=content.encode("utf-8"), timeout=timeout)


async def show_async(content: str, **kwargs):
    timeout = kwargs.pop("timeout", 15.0)
    args = _create_args(**kwargs)
    return await _CREATE.result_async(*args, input=content.encode("utf-8"), timeout=timeout)


def list_result(*, timeout: float | None = 15.0):
    return _LIST.result(timeout=timeout)


def list_json(*, timeout: float | None = 15.0):
    return _LIST.json_if_present(timeout=timeout)


async def list_result_async(*, timeout: float | None = 15.0):
    return await _LIST.result_async(timeout=timeout)


async def list_json_async(*, timeout: float | None = 15.0):
    return await _LIST.json_if_present_async(timeout=timeout)


def remove(notification_id: str, *, timeout: float | None = 15.0):
    if not notification_id:
        raise ValueError("notification_id must not be empty")
    return _REMOVE.result(notification_id, timeout=timeout)


async def remove_async(notification_id: str, *, timeout: float | None = 15.0):
    if not notification_id:
        raise ValueError("notification_id must not be empty")
    return await _REMOVE.result_async(notification_id, timeout=timeout)
