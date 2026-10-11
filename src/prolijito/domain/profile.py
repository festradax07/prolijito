"""Perfil: la norma contra la que se valida, ya resuelta (herencia aplicada)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from prolijito.domain.measurements import LineSpacingClass
from prolijito.domain.violation import Severity

PROFILE_ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Requirement(StrEnum):
    REQUIRED = "obligatorio"
    NOT_REQUIRED = "no_requerido"
    OPTIONAL = "opcional"  # no se exige, pero se informa si falta
    IF_CONTENT = "si_hay_contenido"  # obligatorio si el documento tiene figuras o tablas

    def is_required(self, *, has_content: bool = True) -> bool:
        if self is Requirement.IF_CONTENT:
            return has_content
        return self is Requirement.REQUIRED


class CaptionPosition(StrEnum):
    BELOW = "debajo"
    ABOVE = "arriba"


@dataclass(frozen=True, slots=True)
class Layout:
    fonts: tuple[str, ...]
    equivalents: tuple[str, ...]
    body_size_pt: float
    size_tolerance_pt: float
    line_spacing: LineSpacingClass
    justified: bool
    caption_position: CaptionPosition = CaptionPosition.BELOW

    def allows_font(self, family: str) -> bool:
        allowed = {f.casefold() for f in (*self.fonts, *self.equivalents)}
        return family.casefold() in allowed

    def size_within_tolerance(self, size_pt: float) -> bool:
        return abs(size_pt - self.body_size_pt) <= self.size_tolerance_pt


@dataclass(frozen=True, slots=True)
class StructureRequirements:
    cover: Requirement
    toc: Requirement
    figure_index: Requirement
    table_index: Requirement
    bibliography: Requirement
    appendix: Requirement


@dataclass(frozen=True, slots=True)
class Profile:
    id: str
    version: str
    description: str
    layout: Layout
    structure: StructureRequirements
    severity_overrides: Mapping[str, Severity] = field(default_factory=dict)
    norm_source: str | None = None

    def __post_init__(self) -> None:
        if not PROFILE_ID_PATTERN.match(self.id):
            raise ValueError(f"ID de perfil inválido (debe ser kebab-case): {self.id!r}")

    @property
    def reference(self) -> str:
        """Forma `id@version` que se muestra en los reportes."""
        return f"{self.id}@{self.version}"

    def severity_for(self, rule_id: str, default: Severity) -> Severity:
        return self.severity_overrides.get(rule_id, default)
