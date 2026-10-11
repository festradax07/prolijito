"""Puertos: lo que los casos de uso necesitan del exterior. Los implementan los adaptadores."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from prolijito.domain import Measurements, Profile


class Measurer(Protocol):
    def measure(self, document: Path) -> Measurements:
        """Mide el documento renderizado. Lanza `MeasurementError` o `MissingDependencyError`."""
        ...


@dataclass(frozen=True, slots=True)
class ProfileSummary:
    id: str
    version: str
    description: str
    path: Path


class ProfileRepository(Protocol):
    def load(self, reference: str) -> Profile:
        """Resuelve un ID o una ruta a `.yaml`, con herencia aplicada. Lanza `ProfileError`."""
        ...

    def available(self) -> tuple[ProfileSummary, ...]:
        """Perfiles que se pueden usar por ID, en orden de búsqueda."""
        ...


class FixCatalog(Protocol):
    def how_to_fix(self) -> Mapping[str, Mapping[str, str]]:
        """Indicaciones por ID de regla y por herramienta (docs, word, latex, typst)."""
        ...
