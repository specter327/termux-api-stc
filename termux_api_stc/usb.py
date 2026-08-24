"""Wrapper de `termux-usb` conforme al CLI oficial actual."""

from typing import Any, Optional

from .core import run, run_text


def list_devices() -> Any:
    """Lista los dispositivos USB disponibles."""
    return run("termux-usb", ["-l"])


def request_permission(
    device: Optional[str] = None,
    vendor_id: Optional[int] = None,
    product_id: Optional[int] = None,
) -> Optional[str]:
    """Solicita permiso para un dispositivo indicado por ruta o VID/PID."""
    args = ["-r"] + _device_arguments(device, vendor_id, product_id)
    return run_text("termux-usb", args)


def open_device(
    command: str,
    device: Optional[str] = None,
    vendor_id: Optional[int] = None,
    product_id: Optional[int] = None,
    request_permission_if_needed: bool = False,
    export_fd: bool = False,
) -> Optional[str]:
    """Abre un USB y ejecuta un comando con su descriptor de archivo."""
    args = []
    if request_permission_if_needed:
        args.append("-r")
    if export_fd:
        args.append("-E")
    args += ["-e", command]
    args += _device_arguments(device, vendor_id, product_id)
    return run_text("termux-usb", args)


def _device_arguments(
    device: Optional[str],
    vendor_id: Optional[int],
    product_id: Optional[int],
) -> list:
    """Construye la identificacion posicional de un dispositivo USB."""
    if device is not None:
        if vendor_id is not None or product_id is not None:
            raise ValueError("Usa device o vendor_id/product_id, no ambos")
        return [device]

    if vendor_id is None or product_id is None:
        raise ValueError("Debes indicar device o vendor_id y product_id")

    return [str(vendor_id), str(product_id)]
