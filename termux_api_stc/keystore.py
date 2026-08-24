"""Wrapper de `termux-keystore` conforme al CLI oficial actual."""

from typing import Any, Optional, Union

from .core import run, run_bytes, run_text
from .core import run_async, run_bytes_async, run_text_async

_VALID_ALGORITHMS = {"RSA", "EC"}
_VALID_RSA_SIZES = {2048, 3072, 4096}
_VALID_EC_SIZES = {256, 384, 521}


def generate(
    alias: str,
    algorithm: str = "RSA",
    key_size: Optional[int] = None,
    validity: Optional[int] = None,
) -> Any:
    """Genera una clave RSA o EC dentro del Android Keystore."""
    normalized_algorithm = algorithm.upper()
    if normalized_algorithm not in _VALID_ALGORITHMS:
        raise ValueError("algorithm debe ser RSA o EC")

    if key_size is not None:
        valid_sizes = (
            _VALID_RSA_SIZES
            if normalized_algorithm == "RSA"
            else _VALID_EC_SIZES
        )
        if key_size not in valid_sizes:
            raise ValueError(
                "key_size invalido para {}: {}".format(
                    normalized_algorithm,
                    sorted(valid_sizes),
                )
            )

    args = ["generate", alias, "-a", normalized_algorithm]
    if key_size is not None:
        args += ["-s", str(key_size)]
    if validity is not None:
        args += ["-u", str(validity)]

    return run("termux-keystore", args)


def list_keys(detailed: bool = False) -> Any:
    """Lista las claves almacenadas; opcionalmente incluye detalles."""
    args = ["list"]
    if detailed:
        args.append("-d")
    return run("termux-keystore", args)


def delete(alias: str) -> Optional[str]:
    """Elimina permanentemente una clave por alias."""
    return run_text("termux-keystore", ["delete", alias])


def sign(
    alias: str,
    algorithm: str,
    input_data: Union[str, bytes],
) -> bytes:
    """Firma datos recibidos por stdin y devuelve la firma binaria."""
    return run_bytes(
        "termux-keystore",
        ["sign", alias, algorithm],
        input_data=input_data,
    )


def verify(
    alias: str,
    algorithm: str,
    signature_file: str,
    input_data: Union[str, bytes],
) -> Any:
    """Verifica una firma usando datos originales recibidos por stdin."""
    return run(
        "termux-keystore",
        ["verify", alias, algorithm, signature_file],
        input_data=input_data,
    )

# ==========
# Asynchronous API
# ==========
async def generate_async(
    alias: str,
    algorithm: str = "RSA",
    key_size: Optional[int] = None,
    validity: Optional[int] = None,
) -> Any:
    """Genera una clave RSA o EC dentro del Android Keystore."""
    normalized_algorithm = algorithm.upper()
    if normalized_algorithm not in _VALID_ALGORITHMS:
        raise ValueError("algorithm debe ser RSA o EC")

    if key_size is not None:
        valid_sizes = (
            _VALID_RSA_SIZES
            if normalized_algorithm == "RSA"
            else _VALID_EC_SIZES
        )
        if key_size not in valid_sizes:
            raise ValueError(
                "key_size invalido para {}: {}".format(
                    normalized_algorithm,
                    sorted(valid_sizes),
                )
            )

    args = ["generate", alias, "-a", normalized_algorithm]
    if key_size is not None:
        args += ["-s", str(key_size)]
    if validity is not None:
        args += ["-u", str(validity)]

    return await run_async("termux-keystore", args)


async def list_keys_async(detailed: bool = False) -> Any:
    """Lista las claves almacenadas; opcionalmente incluye detalles."""
    args = ["list"]
    if detailed:
        args.append("-d")
    return await run_async("termux-keystore", args)


async def delete_async(alias: str) -> Optional[str]:
    """Elimina permanentemente una clave por alias."""
    return await run_text_async("termux-keystore", ["delete", alias])


async def sign_async(
    alias: str,
    algorithm: str,
    input_data: Union[str, bytes],
) -> bytes:
    """Firma datos recibidos por stdin y devuelve la firma binaria."""
    return await run_bytes_async(
        "termux-keystore",
        ["sign", alias, algorithm],
        input_data=input_data,
    )


async def verify_async(
    alias: str,
    algorithm: str,
    signature_file: str,
    input_data: Union[str, bytes],
) -> Any:
    """Verifica una firma usando datos originales recibidos por stdin."""
    return await run_async(
        "termux-keystore",
        ["verify", alias, algorithm, signature_file],
        input_data=input_data,
    )
