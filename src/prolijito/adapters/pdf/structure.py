"""Estructura: carátula, títulos, secciones (índices, bibliografía, anexo) y cotejo del índice.

Basado en `analizar_pdf.py` de la cátedra Taller de Proyecto II (UNLP),
https://github.com/tpII/ia-guidelines-taller (commit 65d2258). MIT, ver NOTICE.md.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise

from prolijito.adapters.pdf.poppler import Line, Page
from prolijito.adapters.pdf.text import (
    CAPTION,
    INVISIBLE,
    NUMBERED,
    TOC_LINE,
    normalize,
    squash,
    strip_accents,
)
from prolijito.domain import (
    FontUsage,
    Heading,
    PageMismatch,
    Section,
    Structure,
    TocCheck,
    TocEntry,
)

COVER_MAX_LINES = 25
COVER_MAX_LINE_CHARS = 100
MIN_HEADING_CHARS, MAX_HEADING_CHARS = 2, 120
MAX_HEADING_WORDS = 14
COLUMN_GAP_PT = 25  # fragmentos de una misma línea separados por más de 25 pt: fila de tabla
BIG_HEADING_PT = 1.5  # un título es al menos 1,5 pt más grande que el cuerpo...
BOLD_HEADING_SLACK_PT = 0.6  # ...o va en negrita con un tamaño parecido al del cuerpo
REPEATED_PAGES = 3  # texto repetido en 3 o más páginas: encabezado o pie, no un título
MIN_FUZZY_KEY_CHARS = 12
MIN_ENTRY_TITLE_CHARS = 2  # títulos largos: se aceptan coincidencias parciales con el índice

_TOC = re.compile(r"^(indice|tabla de contenido|contenido)s?( general)?$")
_FIGURE_INDEX = re.compile(r"^(indice|lista|tabla) de (figuras|ilustraciones|imagenes)")
_TABLE_INDEX = re.compile(r"^(indice|lista|tabla) de tablas")
_BIBLIOGRAPHY = re.compile(r"^(bibliografia|referencias)( bibliograficas)?$")
_APPENDIX = re.compile(r"^(anexos?|apendices?)( [a-z0-9]+)?( |$)")
_NOT_IN_TOC = re.compile(r"^(indice|bibliografia|referencias|anexo|apendice)")
_SECTION_NUMBER = re.compile(r"^(\d+(\.\d+)*\.?|[a-z]\.|[ivx]+\.)\s+")


@dataclass(frozen=True, slots=True)
class DetectedHeading:
    page: int
    text: str
    size: float
    bold: bool


@dataclass(frozen=True, slots=True)
class IndexEntry:
    index_page: int
    title: str
    declared_page: int


@dataclass(frozen=True, slots=True)
class StructureScan:
    structure: Structure
    index_pages: frozenset[int]
    """Páginas de índices (general, de figuras, de tablas): no se analizan como cuerpo."""
    entries: tuple[IndexEntry, ...]
    front_pages: frozenset[int]
    """Páginas previas al índice (carta, carátula): no son cuerpo ni tienen figuras."""


def scan_structure(pages: Sequence[Page], texts: Sequence[str], body: FontUsage) -> StructureScan:
    headings = detect_headings(pages, body)
    toc, figure_index, table_index = (
        _find(headings, p) for p in (_TOC, _FIGURE_INDEX, _TABLE_INDEX)
    )
    bibliography, appendix = _find(headings, _BIBLIOGRAPHY), _find(headings, _APPENDIX)
    index_pages = frozenset(toc.pages + figure_index.pages + table_index.pages)
    entries = _index_entries(sorted(index_pages), texts)
    front = _front_pages(pages, toc)
    body_headings = [h for h in headings if h.page not in index_pages | front]
    structure = Structure(
        cover_page=next((p.number for p in pages if p.number in front and _is_cover(p)), None),
        toc=toc,
        figure_index=figure_index,
        table_index=table_index,
        bibliography=_or_numbered(bibliography, body_headings, _BIBLIOGRAPHY),
        appendix=_or_numbered(appendix, body_headings, _APPENDIX),
        toc_check=_check_toc(entries, body_headings, body),
    )
    return StructureScan(structure, index_pages, entries, front)


def _front_pages(pages: Sequence[Page], toc: Section) -> frozenset[int]:
    """Las páginas antes del índice; sin índice, solo la primera."""
    if not pages:
        return frozenset()
    if not toc.present:
        return frozenset({pages[0].number})
    return frozenset(p.number for p in pages if p.number < min(toc.pages))


# ---------- títulos ----------


def detect_headings(pages: Sequence[Page], body: FontUsage) -> list[DetectedHeading]:
    headings = [
        DetectedHeading(page.number, squash(line.text), round(line.size, 1), line.bold)
        for page in pages
        for line in page.lines
        if _is_heading(line, body)
    ]
    counts = Counter(normalize(h.text) for h in headings)
    return [h for h in headings if counts[normalize(h.text)] < REPEATED_PAGES]


def _is_heading(line: Line, body: FontUsage) -> bool:
    text = line.text
    if (
        not MIN_HEADING_CHARS <= len(text) <= MAX_HEADING_CHARS
        or CAPTION.match(text)
        or "http" in text
    ):
        return False
    if is_multicolumn(line):
        return False
    big = line.size >= body.size_pt + BIG_HEADING_PT
    bold = (
        line.bold
        and line.size >= body.size_pt - BOLD_HEADING_SLACK_PT
        and not text.endswith((".", ",", ";"))
    )
    return (big or bold) and len(text.split()) <= MAX_HEADING_WORDS


def is_multicolumn(line: Line) -> bool:
    """Varios fragmentos en la misma línea separados por huecos grandes: fila de tabla."""
    fragments = sorted(line.fragments, key=lambda f: f.left)
    return any(
        b.left - (a.left + a.width) > COLUMN_GAP_PT
        for a, b in pairwise(fragments)
        if a.text.strip() and b.text.strip()
    )


def _find(headings: Sequence[DetectedHeading], pattern: re.Pattern[str]) -> Section:
    found = sorted({h.page for h in headings if pattern.search(normalize(h.text))})
    return Section(present=bool(found), pages=tuple(found))


def _or_numbered(
    section: Section, headings: Sequence[DetectedHeading], pattern: re.Pattern[str]
) -> Section:
    """Secciones numeradas ("6. Bibliografía"): se buscan sin el número adelante."""
    if section.present:
        return section
    found = tuple(h.page for h in headings if pattern.search(_unnumbered_key(h.text)))
    return Section(present=True, pages=found) if found else section


def _unnumbered_key(text: str) -> str:
    plain = _SECTION_NUMBER.sub("", strip_accents(text.lower()).strip())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", plain)).strip()


def _is_cover(page: Page) -> bool:
    """Una carátula tiene poco texto y sin líneas largas de párrafo."""
    return len(page.lines) <= COVER_MAX_LINES and not any(
        len(line.text) > COVER_MAX_LINE_CHARS for line in page.lines
    )


# ---------- índice ----------


def _index_entries(index_pages: Sequence[int], texts: Sequence[str]) -> tuple[IndexEntry, ...]:
    """Líneas con un número de página al final, en las páginas de índice."""
    entries = []
    for page in index_pages:
        for raw in texts[page - 1].splitlines():
            match = TOC_LINE.match(INVISIBLE.sub(" ", raw).strip())
            if (
                match
                and len(match.group("t")) > MIN_ENTRY_TITLE_CHARS
                and not match.group("t").strip().isdigit()
            ):
                entries.append(IndexEntry(page, squash(match.group("t")), int(match.group("p"))))
    return tuple(entries)


def toc_key(text: str) -> str:
    return normalize(NUMBERED.sub("", text))


def _matches(key: str, heading: DetectedHeading) -> bool:
    other = toc_key(heading.text)
    return other == key or (len(key) > MIN_FUZZY_KEY_CHARS and (key in other or other in key))


def _check_toc(
    entries: Sequence[IndexEntry], headings: Sequence[DetectedHeading], body: FontUsage
) -> TocCheck:
    missing: list[TocEntry] = []
    pairs: list[tuple[IndexEntry, list[int]]] = []
    for entry in entries:
        if CAPTION.match(entry.title):
            continue
        key = toc_key(entry.title)
        pages = sorted({h.page for h in headings if _matches(key, h)})
        if pages:
            pairs.append((entry, pages))
        else:
            missing.append(TocEntry(entry.title, entry.declared_page))
    # La numeración impresa puede arrancar después de la carátula y el índice: se admite un
    # desfasaje constante.
    offsets = Counter(min(pages) - entry.declared_page for entry, pages in pairs)
    offset = offsets.most_common(1)[0][0] if offsets else 0
    mismatches = tuple(
        PageMismatch(entry.title, entry.declared_page, tuple(pages))
        for entry, pages in pairs
        if not any(p == entry.declared_page + offset for p in pages)
    )
    return TocCheck(
        entries_without_heading=tuple(missing),
        page_mismatches=mismatches,
        headings_without_entry=_headings_without_entry(entries, headings, body),
        page_offset=offset,
    )


def _headings_without_entry(
    entries: Sequence[IndexEntry], headings: Sequence[DetectedHeading], body: FontUsage
) -> tuple[Heading, ...]:
    keys = {toc_key(e.title) for e in entries}

    def in_index(heading: DetectedHeading) -> bool:
        key = toc_key(heading.text)
        return key in keys or any(
            key in k or k in key for k in keys if len(k) > MIN_FUZZY_KEY_CHARS
        )

    return tuple(
        Heading(h.page, h.text)
        for h in headings
        if h.size >= body.size_pt + BIG_HEADING_PT
        and not in_index(h)
        and not _NOT_IN_TOC.search(normalize(h.text))
    )
