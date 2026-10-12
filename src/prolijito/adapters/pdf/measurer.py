"""Medidor de PDF de prolijito: implementa el puerto `Measurer` con poppler.

Fork de `analizar_pdf.py` de la cátedra Taller de Proyecto II (UNLP),
https://github.com/tpII/ia-guidelines-taller (commit 65d2258). MIT, ver NOTICE.md y ADR 0008.
"""

from __future__ import annotations

import shutil
from collections.abc import Sequence
from pathlib import Path

from prolijito.adapters.pdf.captions import measure_captions
from prolijito.adapters.pdf.language import find_language_issues
from prolijito.adapters.pdf.poppler import Document, extract
from prolijito.adapters.pdf.structure import scan_structure
from prolijito.adapters.pdf.typography import (
    measure_justification,
    measure_line_spacing,
    measure_typography,
)
from prolijito.application.errors import MissingDependencyError
from prolijito.domain import Measurements

REQUIRED_TOOLS = ("pdftohtml", "pdftotext")


class PdfMeasurer:
    def __init__(self, required_tools: Sequence[str] = REQUIRED_TOOLS) -> None:
        self._required_tools = tuple(required_tools)

    def measure(self, document: Path) -> Measurements:
        missing = [tool for tool in self._required_tools if shutil.which(tool) is None]
        if missing:
            raise MissingDependencyError(
                f"faltan herramientas de sistema: {', '.join(missing)} (paquete poppler-utils). "
                "La imagen Docker de prolijito ya las incluye."
            )
        return measure_document(extract(document))


def measure_document(document: Document) -> Measurements:
    """Todas las mediciones a partir de lo que extrajo poppler (sin I/O)."""
    pages, texts = document.pages, document.texts
    typography = measure_typography(pages)
    body = typography.body
    scan = scan_structure(pages, texts, body)
    excluded = {*scan.front_pages, *scan.index_pages, *scan.structure.bibliography.pages}
    return Measurements(
        page_count=len(pages),
        typography=typography,
        line_spacing=measure_line_spacing(pages, body),
        justification=measure_justification(pages, body),
        structure=scan.structure,
        captions=measure_captions(
            pages,
            texts,
            scan.index_pages,
            scan.entries,
            scan.front_pages,
        ),
        language=find_language_issues(texts, excluded),
    )
