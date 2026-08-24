"""Wrappers de notificaciones de Termux:API."""

from typing import Any, Optional

from .core import run, run_text
from .core import run_async, run_text_async


def show(
    content: str,
    title: Optional[str] = None,
    notif_id: Optional[str] = None,
    group: Optional[str] = None,
    priority: Optional[str] = None,
    ongoing: bool = False,
    alert_once: bool = False,
    led_color: Optional[str] = None,
    led_on: Optional[int] = None,
    led_off: Optional[int] = None,
    vibrate_pattern: Optional[str] = None,
    sound: bool = False,
    icon: Optional[str] = None,
    image_path: Optional[str] = None,
    channel: Optional[str] = None,
    action: Optional[str] = None,
    button1: Optional[str] = None,
    button1_action: Optional[str] = None,
    button2: Optional[str] = None,
    button2_action: Optional[str] = None,
    button3: Optional[str] = None,
    button3_action: Optional[str] = None,
    on_delete_action: Optional[str] = None,
    notification_type: Optional[str] = None,
    media_previous: Optional[str] = None,
    media_next: Optional[str] = None,
    media_play: Optional[str] = None,
    media_pause: Optional[str] = None,
) -> Optional[str]:
    """Muestra una notificacion del sistema con opciones oficiales actuales."""
    if ongoing and notif_id is None:
        raise ValueError("Una notificacion ongoing requiere notif_id")

    args = ["-c", content]

    option_values = (
        ("-t", title),
        ("--id", notif_id),
        ("--group", group),
        ("--priority", priority),
        ("--led-color", led_color),
        ("--led-on", led_on),
        ("--led-off", led_off),
        ("--vibrate", vibrate_pattern),
        ("--icon", icon),
        ("--image-path", image_path),
        ("--channel", channel),
        ("--action", action),
        ("--button1", button1),
        ("--button1-action", button1_action),
        ("--button2", button2),
        ("--button2-action", button2_action),
        ("--button3", button3),
        ("--button3-action", button3_action),
        ("--on-delete", on_delete_action),
        ("--type", notification_type),
        ("--media-previous", media_previous),
        ("--media-next", media_next),
        ("--media-play", media_play),
        ("--media-pause", media_pause),
    )

    for flag, value in option_values:
        if value is not None:
            args += [flag, str(value)]

    if ongoing:
        args.append("--ongoing")
    if alert_once:
        args.append("--alert-once")
    if sound:
        args.append("--sound")

    return run_text("termux-notification", args)


def remove(notif_id: str) -> Optional[str]:
    """Elimina una notificacion por identificador."""
    return run_text("termux-notification-remove", [str(notif_id)])


def list_notifications() -> Any:
    """Lista las notificaciones activas creadas por Termux."""
    return run("termux-notification-list")


def create_channel(channel_id: str, channel_name: str) -> Optional[str]:
    """Crea o actualiza un canal de notificacion."""
    return run_text(
        "termux-notification-channel",
        [channel_id, channel_name],
    )


def delete_channel(channel_id: str) -> Optional[str]:
    """Elimina un canal de notificacion."""
    return run_text(
        "termux-notification-channel",
        ["-d", channel_id],
    )

# ==========
# Asynchronous API
# ==========
async def show_async(
    content: str,
    title: Optional[str] = None,
    notif_id: Optional[str] = None,
    group: Optional[str] = None,
    priority: Optional[str] = None,
    ongoing: bool = False,
    alert_once: bool = False,
    led_color: Optional[str] = None,
    led_on: Optional[int] = None,
    led_off: Optional[int] = None,
    vibrate_pattern: Optional[str] = None,
    sound: bool = False,
    icon: Optional[str] = None,
    image_path: Optional[str] = None,
    channel: Optional[str] = None,
    action: Optional[str] = None,
    button1: Optional[str] = None,
    button1_action: Optional[str] = None,
    button2: Optional[str] = None,
    button2_action: Optional[str] = None,
    button3: Optional[str] = None,
    button3_action: Optional[str] = None,
    on_delete_action: Optional[str] = None,
    notification_type: Optional[str] = None,
    media_previous: Optional[str] = None,
    media_next: Optional[str] = None,
    media_play: Optional[str] = None,
    media_pause: Optional[str] = None,
) -> Optional[str]:
    """Muestra una notificacion del sistema con opciones oficiales actuales."""
    if ongoing and notif_id is None:
        raise ValueError("Una notificacion ongoing requiere notif_id")

    args = ["-c", content]

    option_values = (
        ("-t", title),
        ("--id", notif_id),
        ("--group", group),
        ("--priority", priority),
        ("--led-color", led_color),
        ("--led-on", led_on),
        ("--led-off", led_off),
        ("--vibrate", vibrate_pattern),
        ("--icon", icon),
        ("--image-path", image_path),
        ("--channel", channel),
        ("--action", action),
        ("--button1", button1),
        ("--button1-action", button1_action),
        ("--button2", button2),
        ("--button2-action", button2_action),
        ("--button3", button3),
        ("--button3-action", button3_action),
        ("--on-delete", on_delete_action),
        ("--type", notification_type),
        ("--media-previous", media_previous),
        ("--media-next", media_next),
        ("--media-play", media_play),
        ("--media-pause", media_pause),
    )

    for flag, value in option_values:
        if value is not None:
            args += [flag, str(value)]

    if ongoing:
        args.append("--ongoing")
    if alert_once:
        args.append("--alert-once")
    if sound:
        args.append("--sound")

    return await run_text_async("termux-notification", args)


async def remove_async(notif_id: str) -> Optional[str]:
    """Elimina una notificacion por identificador."""
    return await run_text_async("termux-notification-remove", [str(notif_id)])


async def list_notifications_async() -> Any:
    """Lista las notificaciones activas creadas por Termux."""
    return await run_async("termux-notification-list")


async def create_channel_async(channel_id: str, channel_name: str) -> Optional[str]:
    """Crea o actualiza un canal de notificacion."""
    return await run_text_async(
        "termux-notification-channel",
        [channel_id, channel_name],
    )


async def delete_channel_async(channel_id: str) -> Optional[str]:
    """Elimina un canal de notificacion."""
    return await run_text_async(
        "termux-notification-channel",
        ["-d", channel_id],
    )
