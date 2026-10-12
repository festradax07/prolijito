"""Mediciones de un documento renderizado: lo que hay, sin juzgar si cumple.

Es el contrato entre cualquier medidor (hoy, el script de la cátedra) y las reglas.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class LineSpacingClass(StrEnum):
    SINGLE = "simple"
    ONE_AND_HALF = "1,5"
    DOUBLE = "doble"


class JustificationState(StrEnum):
    YES = "si"
    PARTIAL = "parcial"
    NO = "no"


class CaptionKind(StrEnum):
    FIGURE = "figura"
    TABLE = "tabla"


@dataclass(frozen=True, slots=True)
class Unmeasured:
    """Medición que no se pudo hacer (por ejemplo, pocos párrafos de cuerpo)."""

    reason: str


# ---------- tipografía y párrafo ----------


@dataclass(frozen=True, slots=True)
class FontUsage:
    family: str
    size_pt: float
    share_pct: float


@dataclass(frozen=True, slots=True)
class Typography:
    body: FontUsage
    others: tuple[FontUsage, ...] = ()


@dataclass(frozen=True, slots=True)
class LineSpacing:
    ratio: float
    spacing_class: LineSpacingClass
    page_classes: Mapping[int, LineSpacingClass] = field(default_factory=dict)
    """Clase de cada página con párrafos suficientes para medirla."""

    def pages_not(self, expected: LineSpacingClass) -> tuple[int, ...]:
        return tuple(sorted(n for n, c in self.page_classes.items() if c is not expected))


@dataclass(frozen=True, slots=True)
class Justification:
    state: JustificationState
    aligned_pct: int
    doubtful_pages: tuple[int, ...] = ()


# ---------- estructura e índice ----------


@dataclass(frozen=True, slots=True)
class Section:
    present: bool
    pages: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class TocEntry:
    title: str
    declared_page: int


@dataclass(frozen=True, slots=True)
class PageMismatch:
    title: str
    declared_page: int
    actual_pages: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class Heading:
    page: int
    text: str


@dataclass(frozen=True, slots=True)
class TocCheck:
    entries_without_heading: tuple[TocEntry, ...] = ()
    page_mismatches: tuple[PageMismatch, ...] = ()
    headings_without_entry: tuple[Heading, ...] = ()
    page_offset: int = 0


@dataclass(frozen=True, slots=True)
class Structure:
    cover_page: int | None
    """Primera página con aspecto de carátula antes del índice; `None` si no se encontró."""
    toc: Section
    figure_index: Section
    table_index: Section
    bibliography: Section
    appendix: Section
    toc_check: TocCheck = TocCheck()


# ---------- figuras y tablas ----------


@dataclass(frozen=True, slots=True)
class Caption:
    kind: CaptionKind
    number: int
    page: int
    text: str
    below: bool | None
    """`None` cuando no se pudo determinar (figura vectorial o en otra página)."""
    text_references: int
    in_index: bool
    prefix: str = ""
    """Letra de una numeración de apéndice: «A» en «Figura A1»."""

    @property
    def label(self) -> str:
        return f"{self.prefix}{self.number}"


@dataclass(frozen=True, slots=True)
class PageLocation:
    page: int
    top_pt: float


@dataclass(frozen=True, slots=True)
class Captions:
    items: tuple[Caption, ...] = ()
    figures_consecutive: bool = True
    tables_consecutive: bool = True
    uncaptioned_images: tuple[PageLocation, ...] = ()
    uncaptioned_tables: tuple[PageLocation, ...] = ()
    detected_tables: int = 0
    images_per_page: Mapping[int, int] = field(default_factory=dict)

    def of_kind(self, kind: CaptionKind) -> tuple[Caption, ...]:
        return tuple(c for c in self.items if c.kind is kind)

    @property
    def has_figures(self) -> bool:
        return bool(self.of_kind(CaptionKind.FIGURE)) or any(self.images_per_page.values())

    @property
    def has_tables(self) -> bool:
        return bool(self.of_kind(CaptionKind.TABLE)) or self.detected_tables > 0


# ---------- lenguaje ----------


@dataclass(frozen=True, slots=True)
class LanguageFinding:
    page: int
    kind: str
    word: str
    context: str


# ---------- raíz ----------


@dataclass(frozen=True, slots=True)
class Measurements:
    page_count: int
    typography: Typography
    line_spacing: LineSpacing | Unmeasured
    justification: Justification | Unmeasured
    structure: Structure
    captions: Captions = Captions()
    language: tuple[LanguageFinding, ...] = ()
