"""Errores de ejecución: terminan con exit code 2 y un mensaje claro para quien usa la CLI."""


class ProlijitoError(Exception):
    """Base de los errores esperables (no son bugs)."""


class ProfileError(ProlijitoError):
    """El perfil no existe, no se puede leer o no cumple el esquema."""


class MeasurementError(ProlijitoError):
    """El medidor falló o devolvió algo que no se puede interpretar."""


class MissingDependencyError(ProlijitoError):
    """Falta una herramienta de sistema (por ejemplo, poppler)."""
