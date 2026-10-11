"""Reglas FIG: numeración, epígrafes, referencias e índices de figuras y tablas."""

from __future__ import annotations

from collections.abc import Iterator

from prolijito.domain import (
    Caption,
    CaptionKind,
    CaptionPosition,
    Measurements,
    Profile,
    Severity,
    Violation,
)

_NAMES = {CaptionKind.FIGURE: "figura", CaptionKind.TABLE: "tabla"}


def check_figures(m: Measurements, p: Profile) -> Iterator[Violation]:
    c = m.captions
    if not c.figures_consecutive:
        yield Violation("FIG-01", Severity.ERROR, "La numeración de figuras no es 1, 2, 3…")
    if not c.tables_consecutive:
        yield Violation("FIG-02", Severity.ERROR, "La numeración de tablas no es 1, 2, 3…")
    indexes = {
        CaptionKind.FIGURE: m.structure.figure_index.present,
        CaptionKind.TABLE: m.structure.table_index.present,
    }
    for caption in c.items:
        yield from _position(caption, p.layout.caption_position)
        yield from _referenced(caption)
        # Sin el índice, ya lo marca EST-03/EST-04: no se repite por cada epígrafe.
        if indexes[caption.kind]:
            yield from _in_index(caption)
    for image in c.uncaptioned_images:
        yield Violation(
            "FIG-06", Severity.REVIEW, "Hay una imagen grande sin epígrafe.", page=image.page
        )
    for table in c.uncaptioned_tables:
        yield Violation(
            "FIG-07",
            Severity.ERROR,
            "Hay una tabla sin epígrafe (o un bloque que parece tabla).",
            page=table.page,
        )


def _label(caption: Caption) -> str:
    return f"{_NAMES[caption.kind].capitalize()} {caption.number}"


def _position(caption: Caption, position: CaptionPosition) -> Iterator[Violation]:
    if caption.below is None:
        yield Violation(
            "FIG-03",
            Severity.REVIEW,
            f"No se pudo determinar si el epígrafe de la {_label(caption)} está {position}.",
            page=caption.page,
            expected=position.value,
        )
    elif caption.below != (position is CaptionPosition.BELOW):
        measured = CaptionPosition.BELOW if caption.below else CaptionPosition.ABOVE
        yield Violation(
            "FIG-03",
            Severity.ERROR,
            f"El epígrafe de la {_label(caption)} está {measured}.",
            page=caption.page,
            expected=position.value,
            measured=measured.value,
            autofixable=True,
        )


def _referenced(caption: Caption) -> Iterator[Violation]:
    if caption.text_references == 0:
        yield Violation(
            "FIG-04",
            Severity.ERROR,
            f"La {_label(caption)} no se menciona en el texto.",
            page=caption.page,
        )


def _in_index(caption: Caption) -> Iterator[Violation]:
    if not caption.in_index:
        yield Violation(
            "FIG-05",
            Severity.ERROR,
            f"La {_label(caption)} no figura en el índice de {_NAMES[caption.kind]}s.",
            page=caption.page,
            autofixable=True,
        )
