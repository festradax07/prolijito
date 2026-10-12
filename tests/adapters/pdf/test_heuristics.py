"""Heurísticas puntuales con datos sintéticos."""

import pytest

from prolijito.adapters.pdf import PdfMeasurer
from prolijito.adapters.pdf.captions import measure_captions
from prolijito.adapters.pdf.language import find_language_issues
from prolijito.adapters.pdf.poppler import Fragment, Image, Page
from prolijito.adapters.pdf.structure import scan_structure
from prolijito.adapters.pdf.typography import (
    classify_spacing,
    measure_justification,
    measure_line_spacing,
    measure_typography,
)
from prolijito.application.errors import MeasurementError, MissingDependencyError
from prolijito.domain import FontUsage, LineSpacingClass, Unmeasured

BODY = FontUsage("Arial", 12.0, 90.0)


def text(
    top: float, content: str, *, size: float = 12, bold: bool = False, left: float = 70
) -> Fragment:
    return Fragment(top, left, len(content) * 6, size, size, "Arial", bold, content)


def page(number: int, *fragments: Fragment, images: tuple[Image, ...] = ()) -> Page:
    return Page(number, 842, 595, fragments, images)


@pytest.mark.parametrize(
    ("ratio", "spacing"),
    [
        (1.15, LineSpacingClass.SINGLE),
        (1.39, LineSpacingClass.SINGLE),
        (1.5, LineSpacingClass.ONE_AND_HALF),
        (1.72, LineSpacingClass.ONE_AND_HALF),
        (2.3, LineSpacingClass.DOUBLE),
    ],
)
def test_classify_spacing(ratio: float, spacing: LineSpacingClass) -> None:
    assert classify_spacing(ratio) is spacing


def test_document_without_text_is_a_measurement_error() -> None:
    with pytest.raises(MeasurementError, match="escaneada"):
        measure_typography([page(1)])


def test_too_little_body_text_is_unmeasured() -> None:
    pages = [page(1, text(100, "Título corto"))]

    assert isinstance(measure_line_spacing(pages, BODY), Unmeasured)
    assert isinstance(measure_justification(pages, BODY), Unmeasured)


def test_numbered_bibliography_and_appendix_are_found() -> None:
    pages = [
        page(1, text(100, "Carátula")),
        page(5, text(100, "6. Bibliografía", size=16), text(140, "Autor. Título. 2024.")),
        page(6, text(100, "A. Anexo técnico", size=16)),
    ]

    s = scan_structure(pages, ["", "", ""], BODY).structure

    assert (s.bibliography.present, s.bibliography.pages) == (True, (5,))
    assert (s.appendix.present, s.appendix.pages) == (True, (6,))


def test_repeated_header_is_not_a_heading() -> None:
    pages = [page(n, text(20, "Proyecto de ejemplo", bold=True)) for n in range(1, 5)]

    s = scan_structure(pages, [""] * 4, BODY).structure

    assert s.toc_check.headings_without_entry == ()


def test_figure_caption_position_from_images() -> None:
    image = Image(top=200, left=70, width=300, height=150)
    below = page(2, text(360, "Figura 1. Debajo de la imagen"), images=(image,))
    above = page(3, text(180, "Figura 2. Arriba de la imagen"), images=(image,))
    vector = page(4, text(500, "Figura 3. Sin imagen cerca"))

    captions = measure_captions([below, above, vector], ["", "", ""], (), ())

    assert [c.below for c in captions.items] == [True, False, None]
    assert captions.images_per_page == {2: 1, 3: 1}


def test_large_image_without_caption() -> None:
    lonely = page(2, images=(Image(top=200, left=70, width=300, height=150),))

    captions = measure_captions([page(1), lonely], ["", ""], (), (), front_pages={1})

    assert [(i.page, i.top_pt) for i in captions.uncaptioned_images] == [(2, 200.0)]


def test_language_findings_skip_excluded_pages() -> None:
    texts = ["Carátula: quiero agradecer", "Se propone y nosotros decidimos.", "Además, después."]

    findings = find_language_issues(texts, excluded_pages={1})

    assert [(f.page, f.word) for f in findings] == [(2, "nosotros"), (2, "decidimos")]


def test_words_ending_like_first_plural_are_not_flagged() -> None:
    assert find_language_issues(["Los mismos tramos y ambos extremos."], ()) == ()


def test_missing_poppler_is_reported(tmp_path: object) -> None:
    with pytest.raises(MissingDependencyError, match="poppler-utils"):
        PdfMeasurer(required_tools=("no-existe-xyz",)).measure(tmp_path / "x.pdf")  # type: ignore[operator]
