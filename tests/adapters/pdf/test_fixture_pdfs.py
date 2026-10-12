"""Cadena completa del medidor sobre los PDFs de prueba (salida de poppler guardada)."""

import shutil

import pytest

from prolijito.adapters.pdf import PdfMeasurer
from prolijito.domain import (
    CaptionKind,
    Justification,
    JustificationState,
    LineSpacing,
    LineSpacingClass,
)
from tests.stored_pdfs import NAMES, PDFS, stored_measurements


def test_compliant_report_measures_as_written() -> None:
    m = stored_measurements("cumple")

    assert m.page_count == 6
    assert (m.typography.body.family, m.typography.body.size_pt) == ("Libertinus", 12.0)
    assert isinstance(m.line_spacing, LineSpacing)
    assert m.line_spacing.spacing_class is LineSpacingClass.ONE_AND_HALF
    assert m.line_spacing.pages_not(LineSpacingClass.ONE_AND_HALF) == ()
    assert isinstance(m.justification, Justification)
    assert m.justification.state is JustificationState.YES
    s = m.structure
    assert s.cover_page == 1
    assert (s.toc.present, s.toc.pages) == (True, (2,))
    assert s.bibliography.present
    assert not s.appendix.present
    assert s.toc_check.entries_without_heading == ()
    assert s.toc_check.page_mismatches == ()
    assert m.captions.items == ()
    assert m.language == ()


def test_single_spacing_is_measured_as_single() -> None:
    spacing = stored_measurements("interlineado-simple").line_spacing

    assert isinstance(spacing, LineSpacing)
    assert spacing.spacing_class is LineSpacingClass.SINGLE
    assert spacing.ratio < 1.45


def test_report_with_errors_shows_each_planted_error() -> None:
    m = stored_measurements("con-errores")

    assert "DejaVuSansMono" in {f.family for f in m.typography.others}
    toc = m.structure.toc_check
    assert [e.title for e in toc.entries_without_heading] == ["4. Trabajo futuro"]
    assert [(x.title, x.declared_page, x.actual_pages) for x in toc.page_mismatches] == [
        ("3. Resultados", 3, (4,))
    ]
    assert toc.page_offset == 2  # la numeración impresa empieza después de carátula e índice
    assert not m.structure.bibliography.present
    [table] = m.captions.items
    assert (table.kind, table.number, table.below, table.text_references) == (
        CaptionKind.TABLE,
        1,
        False,
        0,
    )
    assert m.captions.has_tables
    assert {f.word for f in m.language} == {"nuestro", "decidimos"}


@pytest.mark.system
@pytest.mark.skipif(shutil.which("pdftohtml") is None, reason="poppler no instalado")
@pytest.mark.parametrize("name", NAMES)
def test_stored_poppler_output_matches_real_poppler(name: str) -> None:
    assert PdfMeasurer().measure(PDFS / f"{name}.pdf") == stored_measurements(name)
