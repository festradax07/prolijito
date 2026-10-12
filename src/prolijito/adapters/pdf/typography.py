"""Tipografía y párrafo: fuente y tamaño del cuerpo, interlineado y justificado.

Basado en `analizar_pdf.py` de la cátedra Taller de Proyecto II (UNLP),
https://github.com/tpII/ia-guidelines-taller (commit 65d2258). MIT, ver NOTICE.md.
Se quitó el juicio contra una norma fija: acá solo se mide; las reglas comparan con el perfil.
"""

from __future__ import annotations

import statistics
from collections import Counter
from collections.abc import Sequence
from itertools import pairwise

from prolijito.adapters.pdf.poppler import Line, Page
from prolijito.adapters.pdf.text import BULLET
from prolijito.application.errors import MeasurementError
from prolijito.domain import (
    FontUsage,
    Justification,
    JustificationState,
    LineSpacing,
    LineSpacingClass,
    Typography,
    Unmeasured,
)

BODY_SIZE_SLACK_PT = 0.6  # una línea es del cuerpo si su tamaño difiere ≤ 0,6 pt del cuerpo
MIN_SHARE = 0.01  # otras fuentes: solo las que cubren al menos el 1 % del texto

# Interlineado: el salto entre líneas sobre el tamaño de fuente. Word/Docs "simple" ≈ 1,15-1,2x,
# "múltiple 1,15" ≈ 1,32x, LaTeX \linespread{1.15} ≈ 1,39x; "1,5" real ≈ 1,5x (Typst) a 1,72x
# (Word); "doble" ≈ 2,3x. El corte en 1,45 hace que 1,15 y 1,39 caigan en simple.
SINGLE_MAX_RATIO = 1.45
ONE_AND_HALF_MAX_RATIO = 1.95
MIN_SPACING_LINE_CHARS = 40
MIN_GAP_PT, MAX_GAP_PT = 8, 45
SAME_COLUMN_PT = 3
MIN_GAPS_PER_PAGE = 6  # con menos líneas, el espacio entre párrafos domina la mediana

# Justificado
MIN_BODY_LINES_PER_PAGE = 4
LONG_LINE_SHARE = 0.75  # una línea es "larga" si ocupa más del 75 % del ancho de la caja
PARAGRAPH_BREAK_FACTOR = 1.4  # un salto 1,4 veces mayor que el normal separa párrafos
DEFAULT_GAP_PT = 20
ALIGNED_PT = 2.5
MIN_LONG_LINES = 5
MIN_LONG_LINES_PER_PAGE = 4
JUSTIFIED_SHARE = 0.75
PARTIAL_SHARE = 0.45
DOUBLE_SPACE_SHARE = 0.3
DOUBTFUL_PAGE_PCT = 75


def measure_typography(pages: Sequence[Page]) -> Typography:
    chars: Counter[tuple[str, float]] = Counter()
    for page in pages:
        for fragment in page.fragments:
            chars[(fragment.family, round(fragment.size * 2) / 2)] += len(fragment.text.strip())
    if not chars:
        raise MeasurementError("el PDF no tiene texto extraíble (¿es una imagen escaneada?).")
    total = sum(chars.values()) or 1
    (family, size), count = chars.most_common(1)[0]
    others = tuple(
        FontUsage(f, s, round(100 * c / total, 1))
        for (f, s), c in chars.most_common()
        if c / total >= MIN_SHARE and (f, s) != (family, size)
    )
    return Typography(body=FontUsage(family, size, round(100 * count / total, 1)), others=others)


def body_lines(page: Page, body: FontUsage) -> list[Line]:
    return [
        line
        for line in page.lines
        if line.family == body.family and abs(line.size - body.size_pt) <= BODY_SIZE_SLACK_PT
    ]


def classify_spacing(ratio: float) -> LineSpacingClass:
    if ratio < SINGLE_MAX_RATIO:
        return LineSpacingClass.SINGLE
    if ratio < ONE_AND_HALF_MAX_RATIO:
        return LineSpacingClass.ONE_AND_HALF
    return LineSpacingClass.DOUBLE


def measure_line_spacing(pages: Sequence[Page], body: FontUsage) -> LineSpacing | Unmeasured:
    gaps: list[float] = []
    per_page: dict[int, float] = {}
    for page in pages:
        lines = [line for line in body_lines(page, body) if len(line.text) > MIN_SPACING_LINE_CHARS]
        page_gaps = [
            b.top - a.top
            for a, b in pairwise(lines)
            if MIN_GAP_PT <= b.top - a.top <= MAX_GAP_PT and abs(a.left - b.left) <= SAME_COLUMN_PT
        ]
        gaps += page_gaps
        if len(page_gaps) >= MIN_GAPS_PER_PAGE:
            per_page[page.number] = statistics.median(page_gaps)
    if not gaps:
        return Unmeasured("no se encontraron párrafos de cuerpo suficientes")
    ratio = statistics.median(gaps) / body.size_pt
    return LineSpacing(
        ratio=round(ratio, 2),
        spacing_class=classify_spacing(ratio),
        page_classes={n: classify_spacing(gap / body.size_pt) for n, gap in per_page.items()},
    )


def measure_justification(pages: Sequence[Page], body: FontUsage) -> Justification | Unmeasured:
    right_gaps: list[float] = []
    double_spaced = 0
    per_page: dict[int, int] = {}
    for page in pages:
        lines = body_lines(page, body)
        if len(lines) < MIN_BODY_LINES_PER_PAGE:
            continue
        box_right = max(line.right for line in lines)
        long_lines = _long_inner_lines(lines, box_right)
        gaps = [box_right - line.right for line in long_lines]
        right_gaps += gaps
        double_spaced += sum(1 for line in long_lines if "  " in line.text.strip())
        if len(long_lines) >= MIN_LONG_LINES_PER_PAGE:
            per_page[page.number] = round(100 * sum(g <= ALIGNED_PT for g in gaps) / len(gaps))
    if len(right_gaps) < MIN_LONG_LINES:
        return Unmeasured("pocas líneas largas para evaluar")
    aligned = sum(1 for g in right_gaps if g <= ALIGNED_PT) / len(right_gaps)
    return Justification(
        state=_justification_state(aligned, double_spaced / len(right_gaps)),
        aligned_pct=round(100 * aligned),
        doubtful_pages=tuple(sorted(n for n, pct in per_page.items() if pct < DOUBTFUL_PAGE_PCT)),
    )


def _justification_state(aligned: float, double_spaced: float) -> JustificationState:
    if aligned >= JUSTIFIED_SHARE:
        return JustificationState.YES
    if aligned >= PARTIAL_SHARE or double_spaced >= DOUBLE_SPACE_SHARE:
        return JustificationState.PARTIAL
    return JustificationState.NO


def _long_inner_lines(lines: Sequence[Line], box_right: float) -> list[Line]:
    """Líneas largas que no cierran párrafo ni son viñetas: las que deberían llegar al margen."""
    gaps = [b.top - a.top for a, b in pairwise(lines) if MIN_GAP_PT <= b.top - a.top <= MAX_GAP_PT]
    usual_gap = statistics.median(gaps) if gaps else DEFAULT_GAP_PT
    box_left = min(line.left for line in lines)
    selected = []
    for i, line in enumerate(lines):
        if line.right - line.left <= LONG_LINE_SHARE * (box_right - box_left):
            continue
        following = lines[i + 1] if i + 1 < len(lines) else None
        if BULLET.match(line.text) or _closes_paragraph(line, following, usual_gap):
            continue
        selected.append(line)
    return selected


def _closes_paragraph(line: Line, following: Line | None, usual_gap: float) -> bool:
    """La última línea de un párrafo justificado queda corta: no se cuenta."""
    return (
        following is None
        or following.top - line.top > PARAGRAPH_BREAK_FACTOR * usual_gap
        or abs(following.left - line.left) > SAME_COLUMN_PT
        or BULLET.match(following.text) is not None
    )
