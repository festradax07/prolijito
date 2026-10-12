"""Figuras y tablas: epígrafes, posición, referencias desde el texto, índices y numeración.

Basado en `analizar_pdf.py` de la cátedra Taller de Proyecto II (UNLP),
https://github.com/tpII/ia-guidelines-taller (commit 65d2258). MIT, ver NOTICE.md.
Cambios propios (ADR 0008): numeración de apéndice («Figura A1»), epígrafes arriba de la tabla o
imagen (estilo APA), páginas previas al índice excluidas, tablas con celdas de varias líneas o
partidas entre páginas, y posición del epígrafe según la tabla más cercana.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from collections.abc import Collection, Sequence
from dataclasses import dataclass, replace

from prolijito.adapters.pdf.poppler import Line, Page
from prolijito.adapters.pdf.structure import IndexEntry, is_multicolumn
from prolijito.adapters.pdf.text import CAPTION
from prolijito.domain import Caption, CaptionKind, Captions, PageLocation

CAPTION_TEXT_CHARS = 90
NEAR_PT = 120  # un epígrafe corresponde a una imagen o tabla a menos de 120 pt
EDGE_SLACK_PT = 5
TABLE_CONTEXT_PT = 220  # una tabla a más de 220 pt del epígrafe no es la suya
MIN_TABLE_ROWS = 3  # 3 o más filas con varias columnas: tabla
MAX_WRAPPED_LINES = 4  # líneas de una sola columna dentro de una tabla: celdas de varias líneas
EDGE_LINES = 1  # una tabla toca el borde de la página si a lo sumo la separa 1 línea (el número)
COLUMN_ALIGN_PT = 3  # dos filas comparten columna si una celda empieza a ±3 pt
ALIGNED_ROWS_SHARE = 0.6  # en una tabla, al menos el 60 % de las filas comparte una columna
ROW_HEIGHT_PT = 15
LARGE_IMAGE_WIDTH_PT, LARGE_IMAGE_HEIGHT_PT = 100, 60
REFERENCE_LOOKAHEAD = 60
_TABLE_WORDS = ("tabla", "cuadro")
_REFERENCE_WORDS = {
    CaptionKind.FIGURE: r"Figura|Fig\.|Imagen|Gr[aá]fico|Ilustraci[oó]n",
    CaptionKind.TABLE: r"Tabla|Cuadro",
}

CaptionKey = tuple[CaptionKind, str, int]


@dataclass(frozen=True, slots=True)
class _Found:
    caption: Caption
    top: float


@dataclass(frozen=True, slots=True)
class _Context:
    """Lo que hace falta para interpretar cada epígrafe."""

    in_index: set[CaptionKey]
    texts: Sequence[str]
    tables: Sequence[_Table]


@dataclass(frozen=True, slots=True)
class _Table:
    page: int
    top: float
    bottom: float
    rows: int
    at_page_top: bool
    at_page_bottom: bool
    captioned: bool = False

    @property
    def partial(self) -> bool:
        """Pocas filas en un borde de la página: continuación de una tabla, no una tabla aparte."""
        return self.rows < MIN_TABLE_ROWS


def measure_captions(
    pages: Sequence[Page],
    texts: Sequence[str],
    index_pages: Collection[int],
    entries: Sequence[IndexEntry],
    front_pages: Collection[int] = (),
) -> Captions:
    """`front_pages`: carta y carátula; sus imágenes (logos) no cuentan como figuras."""
    tables = _geometric_tables(pages, index_pages)
    context = _Context(_indexed(entries), texts, tables)
    found = [
        _Found(_caption(page, line, match, context), _line_top(page, line.text))
        for page in pages
        if page.number not in index_pages
        for line in page.lines
        if (match := CAPTION.match(line.text))
    ]
    tables = _join_across_pages(
        [
            replace(t, captioned=_has_caption(found, t.page, t.top, t.bottom, CaptionKind.TABLE))
            for t in tables
        ]
    )
    whole = [t for t in tables if not t.partial]
    return Captions(
        items=tuple(f.caption for f in found),
        figures_consecutive=_consecutive(found, CaptionKind.FIGURE),
        tables_consecutive=_consecutive(found, CaptionKind.TABLE),
        uncaptioned_images=_uncaptioned_images(pages, {*index_pages, *front_pages}, found),
        uncaptioned_tables=tuple(PageLocation(t.page, t.top) for t in whole if not t.captioned),
        detected_tables=len(whole),
        images_per_page={
            p.number: len(p.images) for p in pages if p.images and p.number not in front_pages
        },
    )


# ---------- epígrafes ----------


def _key(match: re.Match[str]) -> CaptionKey:
    word = match.group(1).lower()
    kind = CaptionKind.TABLE if word in _TABLE_WORDS else CaptionKind.FIGURE
    return kind, match.group(2).upper(), int(match.group(3))


def _indexed(entries: Sequence[IndexEntry]) -> set[CaptionKey]:
    return {_key(m) for e in entries if (m := CAPTION.match(e.title))}


def _caption(page: Page, line: Line, match: re.Match[str], context: _Context) -> Caption:
    kind, prefix, number = key = _key(match)
    below = (
        _figure_below(page, line)
        if kind is CaptionKind.FIGURE
        else _table_below(line, [t for t in context.tables if t.page == page.number])
    )
    return Caption(
        kind=kind,
        number=number,
        page=page.number,
        text=line.text[:CAPTION_TEXT_CHARS],
        below=below,
        text_references=_references(kind, f"{prefix}{number}", context.texts),
        in_index=key in context.in_index,
        prefix=prefix,
    )


def _line_top(page: Page, text: str) -> float:
    prefix = text[:CAPTION_TEXT_CHARS]
    return next((line.top for line in page.lines if line.text[:CAPTION_TEXT_CHARS] == prefix), 0)


def _figure_below(page: Page, line: Line) -> bool | None:
    """¿El epígrafe está debajo de una imagen? `None`: figura vectorial o en otra página."""
    above = any(
        im.top + im.height <= line.top + EDGE_SLACK_PT and line.top - (im.top + im.height) < NEAR_PT
        for im in page.images
    )
    under = any(
        im.top >= line.top - EDGE_SLACK_PT and im.top - line.top < NEAR_PT for im in page.images
    )
    if above:
        return True
    return False if under else None


def _table_below(caption: Line, tables: Sequence[_Table]) -> bool | None:
    """¿El epígrafe está debajo de su tabla? Su tabla es la más cercana, arriba o abajo."""
    gap_above = min(
        (caption.top - t.bottom for t in tables if t.bottom <= caption.top + EDGE_SLACK_PT),
        default=None,
    )
    gap_below = min(
        (t.top - caption.top for t in tables if t.top >= caption.top - EDGE_SLACK_PT),
        default=None,
    )
    if gap_above is not None and gap_above > TABLE_CONTEXT_PT:
        gap_above = None
    if gap_below is not None and gap_below > TABLE_CONTEXT_PT:
        gap_below = None
    if gap_above is None:
        return None if gap_below is None else False
    return gap_below is None or gap_above <= gap_below


def _has_caption(
    found: Sequence[_Found], page: int, top: float, bottom: float, kind: CaptionKind
) -> bool:
    """Un epígrafe cerca del borde inferior, o justo arriba del borde superior (estilo APA)."""
    return any(
        f.caption.page == page
        and f.caption.kind is kind
        and (-NEAR_PT <= f.top - bottom <= NEAR_PT or 0 <= top - f.top <= NEAR_PT)
        for f in found
    )


# ---------- tablas por geometría ----------


def _geometric_tables(pages: Sequence[Page], index_pages: Collection[int]) -> list[_Table]:
    """Bloques de filas con varias columnas alineadas. Las celdas de varias líneas no cortan el
    bloque; un epígrafe sí."""
    tables = []
    for page in pages:
        if page.number in index_pages:
            continue
        rows: list[int] = []
        for i, line in enumerate(page.lines):
            if is_multicolumn(line):
                rows.append(i)
            elif rows and (CAPTION.match(line.text) or i - rows[-1] > MAX_WRAPPED_LINES):
                tables += _table(page, rows)
                rows = []
        tables += _table(page, rows)
    return tables


def _table(page: Page, rows: Sequence[int]) -> list[_Table]:
    if not rows:
        return []
    at_top = rows[0] <= EDGE_LINES
    at_bottom = len(page.lines) - 1 - rows[-1] <= EDGE_LINES
    partial = len(rows) < MIN_TABLE_ROWS
    if (partial and not (at_top or at_bottom)) or (not partial and not _aligned(page, rows)):
        return []
    return [
        _Table(
            page=page.number,
            top=page.lines[rows[0]].top,
            bottom=page.lines[rows[-1]].top + ROW_HEIGHT_PT,
            rows=len(rows),
            at_page_top=at_top,
            at_page_bottom=at_bottom,
        )
    ]


def _aligned(page: Page, rows: Sequence[int]) -> bool:
    """Las columnas de una tabla están alineadas; los huecos de un texto justificado, no."""
    starts = [
        [f.left for f in sorted(page.lines[i].fragments, key=lambda f: f.left)[1:]] for i in rows
    ]
    needed = max(2, math.ceil(ALIGNED_ROWS_SHARE * len(rows)))
    return any(
        sum(any(abs(x - left) <= COLUMN_ALIGN_PT for x in row) for row in starts) >= needed
        for row in starts
        for left in row
    )


def _join_across_pages(tables: list[_Table]) -> list[_Table]:
    """Una tabla que termina al pie de una página y sigue al principio de la siguiente es una sola:
    alcanza con que una de sus partes tenga epígrafe."""
    joined = list(tables)
    for i, end in enumerate(joined):
        for j, start in enumerate(joined):
            continues = end.at_page_bottom and start.at_page_top and start.page == end.page + 1
            if continues and (end.captioned or start.captioned):
                joined[i] = replace(end, captioned=True)
                joined[j] = replace(start, captioned=True)
    return joined


# ---------- imágenes, referencias y numeración ----------


def _uncaptioned_images(
    pages: Sequence[Page], skipped_pages: Collection[int], found: Sequence[_Found]
) -> tuple[PageLocation, ...]:
    return tuple(
        PageLocation(page.number, float(round(im.top)))
        for page in pages
        if page.number not in skipped_pages
        for im in page.images
        if im.width > LARGE_IMAGE_WIDTH_PT
        and im.height > LARGE_IMAGE_HEIGHT_PT
        and not _has_caption(found, page.number, im.top, im.top + im.height, CaptionKind.FIGURE)
    )


def _references(kind: CaptionKind, label: str, texts: Sequence[str]) -> int:
    """Menciones por número ("como muestra la Figura 2"), sin contar la línea del epígrafe."""
    text = "\n".join(texts)
    pattern = re.compile(rf"\b({_REFERENCE_WORDS[kind]})\s*{label}\b", re.IGNORECASE)
    return sum(
        1
        for m in pattern.finditer(text)
        if not CAPTION.match(
            text[text.rfind("\n", 0, m.start()) + 1 : m.end() + REFERENCE_LOOKAHEAD].strip()
        )
    )


def _consecutive(found: Sequence[_Found], kind: CaptionKind) -> bool:
    """Cada serie (la principal y cada apéndice: A1, A2…) numera 1, 2, 3…"""
    series: defaultdict[str, list[int]] = defaultdict(list)
    for f in found:
        if f.caption.kind is kind:
            series[f.caption.prefix].append(f.caption.number)
    return all(numbers == list(range(1, len(numbers) + 1)) for numbers in series.values())
