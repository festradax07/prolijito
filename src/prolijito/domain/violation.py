"""Violación: resultado de comparar una medición contra el perfil."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum


class Severity(StrEnum):
    ERROR = "error"  # corregir
    REVIEW = "revisar"  # criterio humano
    INFO = "info"  # no se penaliza


class Category(StrEnum):
    TYPOGRAPHY = "tipografia"
    STRUCTURE = "estructura"
    HEADINGS = "titulos"
    FIGURES = "figuras"
    LANGUAGE = "lenguaje"
    REFERENCES = "referencias"
    PRIVACY = "privacidad"


CATEGORY_BY_PREFIX: Mapping[str, Category] = {
    "TIP": Category.TYPOGRAPHY,
    "EST": Category.STRUCTURE,
    "TIT": Category.HEADINGS,
    "FIG": Category.FIGURES,
    "LEN": Category.LANGUAGE,
    "REF": Category.REFERENCES,
    "PRI": Category.PRIVACY,
}

RULE_ID_PATTERN = re.compile(rf"^({'|'.join(CATEGORY_BY_PREFIX)})-\d{{2}}$")


@dataclass(frozen=True, slots=True)
class Occurrence:
    """Un lugar puntual del documento que dispara la violación."""

    page: int | None
    text: str


@dataclass(frozen=True, slots=True)
class Violation:
    rule_id: str
    severity: Severity
    message: str
    page: int | None = None
    expected: str | None = None
    measured: str | None = None
    how_to_fix: Mapping[str, str] = field(default_factory=dict)
    autofixable: bool = False
    occurrences: tuple[Occurrence, ...] = ()

    def __post_init__(self) -> None:
        if not RULE_ID_PATTERN.match(self.rule_id):
            raise ValueError(f"ID de regla inválido: {self.rule_id!r}")

    @property
    def category(self) -> Category:
        """La categoría sale del prefijo del ID, así nunca se contradicen."""
        return CATEGORY_BY_PREFIX[self.rule_id[:3]]

    def with_severity(self, severity: Severity) -> Violation:
        return replace(self, severity=severity)
