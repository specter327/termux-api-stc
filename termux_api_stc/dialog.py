"""Wrapper de `termux-dialog` conforme a los widgets oficiales actuales."""

from typing import Any, List, Optional

from .core import run
from .core import run_async

_WIDGETS = {
    "confirm", "checkbox", "counter", "date", "radio",
    "sheet", "spinner", "speech", "text", "time",
}


def dialog(
    widget: str,
    title: Optional[str] = None,
    hint: Optional[str] = None,
    values: Optional[List[str]] = None,
    extra_args: Optional[List[str]] = None,
) -> Any:
    """Ejecuta un widget generico de termux-dialog."""
    if widget not in _WIDGETS:
        raise ValueError(
            "widget desconocido '{}'. Se esperaba uno de {}".format(
                widget,
                sorted(_WIDGETS),
            )
        )

    args = [widget]
    if title is not None:
        args += ["-t", title]
    if hint is not None:
        args += ["-i", hint]
    if values is not None:
        args += ["-v", ",".join(values)]
    if extra_args:
        args += extra_args

    return run("termux-dialog", args)


def confirm(title: str = "", hint: str = "") -> Any:
    """Muestra un dialogo de confirmacion."""
    return dialog("confirm", title=title, hint=hint)


def text_input(
    title: str = "",
    hint: str = "",
    multiple_lines: bool = False,
    password: bool = False,
    numeric: bool = False,
) -> Any:
    """Muestra entrada de texto con opciones compatibles."""
    if multiple_lines and numeric:
        raise ValueError("multiple_lines y numeric no pueden combinarse")

    extra = []
    if multiple_lines:
        extra.append("-m")
    if password:
        extra.append("-p")
    if numeric:
        extra.append("-n")

    return dialog(
        "text",
        title=title,
        hint=hint,
        extra_args=extra or None,
    )


def checkbox(values: List[str], title: str = "") -> Any:
    """Muestra un selector multiple."""
    return dialog("checkbox", title=title, values=values)


def radio(values: List[str], title: str = "") -> Any:
    """Muestra un selector unico con radio buttons."""
    return dialog("radio", title=title, values=values)


def spinner(values: List[str], title: str = "") -> Any:
    """Muestra un selector desplegable."""
    return dialog("spinner", title=title, values=values)


def sheet(values: List[str], title: str = "") -> Any:
    """Muestra un selector bottom sheet."""
    return dialog("sheet", title=title, values=values)


def counter(title: str = "", range_: Optional[str] = None) -> Any:
    """Muestra un contador numerico con rango opcional."""
    extra = ["-r", range_] if range_ else None
    return dialog("counter", title=title, extra_args=extra)


def date(title: str = "", date_format: Optional[str] = None) -> Any:
    """Muestra un selector de fecha."""
    extra = ["-d", date_format] if date_format else None
    return dialog("date", title=title, extra_args=extra)


def time(title: str = "") -> Any:
    """Muestra un selector de hora."""
    return dialog("time", title=title)


def speech(title: str = "", hint: str = "") -> Any:
    """Muestra reconocimiento de voz; el CLI actual no acepta idioma."""
    return dialog("speech", title=title, hint=hint)

# ==========
# Asynchronous API
# ==========
async def dialog_async(
    widget: str,
    title: Optional[str] = None,
    hint: Optional[str] = None,
    values: Optional[List[str]] = None,
    extra_args: Optional[List[str]] = None,
) -> Any:
    """Ejecuta un widget generico de termux-dialog."""
    if widget not in _WIDGETS:
        raise ValueError(
            "widget desconocido '{}'. Se esperaba uno de {}".format(
                widget,
                sorted(_WIDGETS),
            )
        )

    args = [widget]
    if title is not None:
        args += ["-t", title]
    if hint is not None:
        args += ["-i", hint]
    if values is not None:
        args += ["-v", ",".join(values)]
    if extra_args:
        args += extra_args

    return await run_async("termux-dialog", args)


async def confirm_async(title: str = "", hint: str = "") -> Any:
    """Muestra un dialogo de confirmacion."""
    return await dialog_async("confirm", title=title, hint=hint)


async def text_input_async(
    title: str = "",
    hint: str = "",
    multiple_lines: bool = False,
    password: bool = False,
    numeric: bool = False,
) -> Any:
    """Muestra entrada de texto con opciones compatibles."""
    if multiple_lines and numeric:
        raise ValueError("multiple_lines y numeric no pueden combinarse")

    extra = []
    if multiple_lines:
        extra.append("-m")
    if password:
        extra.append("-p")
    if numeric:
        extra.append("-n")

    return await dialog_async(
        "text",
        title=title,
        hint=hint,
        extra_args=extra or None,
    )


async def checkbox_async(values: List[str], title: str = "") -> Any:
    """Muestra un selector multiple."""
    return await dialog_async("checkbox", title=title, values=values)


async def radio_async(values: List[str], title: str = "") -> Any:
    """Muestra un selector unico con radio buttons."""
    return await dialog_async("radio", title=title, values=values)


async def spinner_async(values: List[str], title: str = "") -> Any:
    """Muestra un selector desplegable."""
    return await dialog_async("spinner", title=title, values=values)


async def sheet_async(values: List[str], title: str = "") -> Any:
    """Muestra un selector bottom sheet."""
    return await dialog_async("sheet", title=title, values=values)


async def counter_async(title: str = "", range_: Optional[str] = None) -> Any:
    """Muestra un contador numerico con rango opcional."""
    extra = ["-r", range_] if range_ else None
    return await dialog_async("counter", title=title, extra_args=extra)


async def date_async(title: str = "", date_format: Optional[str] = None) -> Any:
    """Muestra un selector de fecha."""
    extra = ["-d", date_format] if date_format else None
    return await dialog_async("date", title=title, extra_args=extra)


async def time_async(title: str = "") -> Any:
    """Muestra un selector de hora."""
    return await dialog_async("time", title=title)


async def speech_async(title: str = "", hint: str = "") -> Any:
    """Muestra reconocimiento de voz; el CLI actual no acepta idioma."""
    return await dialog_async("speech", title=title, hint=hint)
