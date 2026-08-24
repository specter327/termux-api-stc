"""Wrappers de `termux-open` y `termux-open-url` de termux-tools."""

from typing import Optional

from .core import run_text


def open_file(
    path_or_url: str,
    content_type: Optional[str] = None,
    action: str = "view",
    chooser: bool = False,
) -> Optional[str]:
    """Abre o comparte un archivo/URL usando termux-open."""
    if action not in {"view", "send"}:
        raise ValueError("action debe ser 'view' o 'send'")

    args = ["--{}".format(action)]
    if content_type is not None:
        args += ["--content-type", content_type]
    if chooser:
        args.append("--chooser")
    args.append(path_or_url)

    return run_text("termux-open", args)


def open_url(
    url: str,
    app_package_or_component: Optional[str] = None,
) -> Optional[str]:
    """Abre una URL con la aplicacion predeterminada o una especifica."""
    args = [url]
    if app_package_or_component is not None:
        args.append(app_package_or_component)
    return run_text("termux-open-url", args)
