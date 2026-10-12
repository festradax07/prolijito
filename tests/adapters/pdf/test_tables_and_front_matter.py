"""Mejoras propias del medidor (ADR 0008), con páginas sintéticas."""

from collections.abc import Sequence

from prolijito.adapters.pdf.captions import measure_captions
from prolijito.adapters.pdf.poppler import Fragment, Line, Page
from prolijito.adapters.pdf.structure import scan_structure
from prolijito.domain import CaptionKind, Captions, FontUsage

BODY = FontUsage("Arial", 12.0, 90.0)
COLUMNS = (70, 220, 370)  # tres columnas alineadas, separadas por más de 25 pt


def fragment(top: float, left: float, text: str, *, size: float = 12) -> Fragment:
    return Fragment(top, left, len(text) * 5, size, size, "Arial", False, text)


def row(top: float, *cells: str) -> list[Fragment]:
    return [fragment(top, left, cell) for left, cell in zip(COLUMNS, cells, strict=False)]


def table(top: float, rows: int, *, step: float = 20) -> list[Fragment]:
    return [f for i in range(rows) for f in row(top + i * step, f"a{i}", f"b{i}", f"c{i}")]


def text(top: float, content: str, *, size: float = 12) -> list[Fragment]:
    return [fragment(top, 70, content, size=size)]


def page(number: int, *parts: Sequence[Fragment]) -> Page:
    return Page(number, 842, 595, tuple(f for part in parts for f in part), ())


def captions(*pages: Page) -> Captions:
    return measure_captions(pages, ["" for _ in pages], (), ())


def test_caption_below_its_table() -> None:
    result = captions(page(2, table(100, 4), text(190, "Tabla 1. Debajo"), text(240, "Párrafo.")))

    [caption] = result.items
    assert caption.below is True
    assert result.uncaptioned_tables == ()


def test_caption_above_its_table_counts_as_captioned() -> None:
    result = captions(page(2, text(80, "Tabla 1. Arriba"), table(100, 4)))

    [caption] = result.items
    assert caption.below is False
    assert result.uncaptioned_tables == ()


def test_caption_between_two_tables_belongs_to_the_nearest() -> None:
    """Tabla 2 termina, su epígrafe va debajo, y enseguida empieza la Tabla 3 con el suyo."""
    result = captions(
        page(
            8,
            table(80, 3),
            text(140, "Tabla 2. Debajo de la primera"),
            text(200, "Un párrafo entre las dos tablas."),
            table(260, 3),
            text(320, "Tabla 3. Debajo de la segunda"),
        )
    )

    assert [c.below for c in result.items] == [True, True]


def test_cells_with_several_lines_do_not_split_the_table() -> None:
    wrapped = [
        *row(100, "a", "b", "c"),
        *text(112, "sigue"),
        *text(124, "sigue"),
        *text(136, "sigue"),
    ]
    rows = [*wrapped, *row(160, "a", "b", "c"), *row(180, "a", "b", "c")]

    result = captions(page(2, rows, text(210, "Tabla 1. Una sola tabla")))

    assert result.detected_tables == 1
    assert result.uncaptioned_tables == ()


def test_table_continued_on_the_next_page_shares_its_caption() -> None:
    first = page(4, text(60, "Párrafo."), table(700, 4))  # termina al pie
    rest = page(5, table(60, 2), text(110, "Tabla 1. Al final de la continuación"))

    result = captions(first, rest)

    assert result.uncaptioned_tables == ()
    assert result.detected_tables == 1  # la continuación corta no cuenta como otra tabla


def test_uncaptioned_table_is_reported() -> None:
    result = captions(page(3, text(60, "Párrafo."), table(100, 4), text(300, "Otro párrafo.")))

    assert [t.page for t in result.uncaptioned_tables] == [3]


def test_justified_text_with_wide_gaps_is_not_a_table() -> None:
    def spaced(top: float, *lefts: float) -> list[Fragment]:
        return [fragment(top, left, "palabra") for left in lefts]

    lines = [*spaced(100, 70, 200, 330), *spaced(120, 70, 160, 300, 420), *spaced(140, 70, 250)]

    assert captions(page(8, lines)).detected_tables == 0


def test_appendix_numbering_is_its_own_series() -> None:
    result = captions(
        page(3, table(100, 3), text(170, "Tabla 1. Principal")),
        page(9, table(100, 3), text(170, "Tabla A1. Del apéndice")),
    )

    labels = [(c.kind, c.label) for c in result.items]
    assert labels == [(CaptionKind.TABLE, "1"), (CaptionKind.TABLE, "A1")]
    assert result.tables_consecutive


def test_cover_after_a_letter_and_front_matter_is_not_body() -> None:
    letter = page(1, *[text(80 + i * 20, "Texto de la carta " * 7) for i in range(30)])
    cover = page(2, text(200, "Título del informe", size=18), text(400, "Autor"))
    toc = page(3, text(80, "Índice", size=16))
    body = page(4, text(80, "1. Introducción", size=16))

    scan = scan_structure([letter, cover, toc, body], ["", "", "", ""], BODY)

    assert scan.structure.cover_page == 2
    assert scan.front_pages == {1, 2}
    titles = [h.text for h in scan.structure.toc_check.headings_without_entry]
    assert titles == ["1. Introducción"]  # el título de la carátula no se toma como cuerpo


def test_no_cover_before_the_index() -> None:
    letter = page(1, *[text(80 + i * 20, "Texto largo de la carta " * 6) for i in range(30)])
    toc = page(2, text(80, "Índice", size=16))

    assert scan_structure([letter, toc], ["", ""], BODY).structure.cover_page is None


def test_line_fragments_are_ordered_left_to_right() -> None:
    line: Line = page(1, [fragment(101.5, 50, "Hola "), fragment(100, 200, "mundo")]).lines[0]

    assert line.text == "Hola mundo"
