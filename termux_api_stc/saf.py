"""Wrapper de Storage Access Framework de Termux:API."""

from typing import Any, Optional, Union

from .core import run, run_bytes, run_text


def create(
    folder_uri: str,
    name: str,
    mime_type: Optional[str] = None,
) -> Any:
    """Crea un archivo SAF dentro de un directorio y devuelve su URI."""
    args = []
    if mime_type is not None:
        args += ["-t", mime_type]
    args += [folder_uri, name]
    return run("termux-saf-create", args)


def dirs() -> Any:
    """Lista los directorios gestionados mediante SAF."""
    return run("termux-saf-dirs")


def managedir() -> Any:
    """Solicita al usuario conceder acceso a un arbol de directorios."""
    return run("termux-saf-managedir")


def listdir(uri: str) -> Any:
    """Lista el contenido de un directorio SAF."""
    return run("termux-saf-ls", [uri])


def mkdir(uri: str, name: str) -> Any:
    """Crea un subdirectorio SAF."""
    return run("termux-saf-mkdir", [uri, name])


def read(uri: str, binary: bool = False) -> Union[bytes, Optional[str]]:
    """Lee un archivo SAF como texto o bytes."""
    if binary:
        return run_bytes("termux-saf-read", [uri])
    return run_text("termux-saf-read", [uri], strip=False)


def write(uri: str, data: Union[str, bytes]) -> Optional[str]:
    """Sobrescribe un archivo SAF con los datos recibidos."""
    return run_text("termux-saf-write", [uri], input_data=data)


def remove(uri: str) -> Optional[str]:
    """Elimina un archivo o directorio SAF mediante termux-saf-rm."""
    return run_text("termux-saf-rm", [uri])


def stat(uri: str) -> Any:
    """Devuelve metadatos de una entrada SAF."""
    return run("termux-saf-stat", [uri])
