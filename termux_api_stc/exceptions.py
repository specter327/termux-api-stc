"""Excepciones utilizadas por TermuxAPI."""

from typing import List, Union


class TermuxAPIError(Exception):
    """Excepcion base para todos los errores de TermuxAPI."""


class TermuxAPICommandUnavailableError(TermuxAPIError):
    """Se lanza cuando un comando requerido no existe en el PATH."""


class TermuxAPINotInstalledError(TermuxAPICommandUnavailableError):
    """Alias compatible para codigo que esperaba la excepcion historica."""


class TermuxAPICompanionUnavailableError(TermuxAPIError):
    """Representa la ausencia o indisponibilidad de la app complementaria."""


class TermuxAPIPermissionError(TermuxAPIError):
    """Representa una operacion rechazada por falta de permisos."""


class TermuxAPIUnsupportedError(TermuxAPIError):
    """Representa una capacidad no soportada por el entorno actual."""


class TermuxAPIProtocolError(TermuxAPIError):
    """Se lanza cuando una respuesta no cumple el formato esperado."""


class TermuxAPIExecutionError(TermuxAPIError):
    """Se lanza cuando un comando termina con codigo distinto de cero."""

    def __init__(
        self,
        command: List[str],
        returncode: int,
        stderr: Union[str, bytes]
    ) -> None:
        """Inicializa el error con informacion del proceso ejecutado."""
        self.command = command
        self.returncode = returncode
        self.stderr = stderr

        if isinstance(stderr, bytes):
            stderr_message = stderr.decode("utf-8", errors="replace").strip()
        else:
            stderr_message = stderr.strip()

        super().__init__(
            "El comando '{}' fallo con codigo {}: {}".format(
                " ".join(command),
                returncode,
                stderr_message,
            )
        )


class TermuxAPITimeoutError(TermuxAPIError):
    """Se lanza cuando un comando excede el timeout especificado."""
