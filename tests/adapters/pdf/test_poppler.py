import pytest

from prolijito.adapters.pdf.poppler import (
    Fragment,
    font_family,
    group_lines,
    parse_pdftohtml,
    split_pages,
)


@pytest.mark.parametrize(
    ("internal", "family"),
    [
        ("ABCDEF+TimesNewRomanPSMT", "Times New Roman"),
        ("Times-Bold", "Times New Roman"),
        ("ArialMT", "Arial"),
        ("LiberationSerif-Regular", "Liberation Serif"),
        ("XYZABC+LiberationSans-Bold", "Liberation Sans"),
        ("LibertinusSerif-Regular", "Libertinus"),
        ("Carlito-Italic", "Carlito"),
        ("ABCDEF+DejaVuSansMono", "DejaVuSansMono"),
        ("Calibri,Bold", "Calibri"),
    ],
)
def test_font_family(internal: str, family: str) -> None:
    assert font_family(internal) == family


def fragment(
    top: float, left: float, text: str, *, bold: bool = False, size: float = 12
) -> Fragment:
    return Fragment(top, left, len(text) * 5, 12, size, "Arial", bold, text)


def test_group_lines_joins_fragments_on_the_same_line() -> None:
    lines = group_lines(
        [fragment(100.0, 200, "mundo"), fragment(100.4, 50, "Hola "), fragment(120, 50, "Otra")]
    )

    assert [line.text for line in lines] == ["Hola mundo", "Otra"]
    assert lines[0].left == 50
    assert lines[0].right == 200 + 25


def test_line_is_bold_only_if_every_fragment_is() -> None:
    [mixed] = group_lines(
        [fragment(10, 0, "2. Palabras clave: ", bold=True), fragment(10, 95, "x")]
    )

    assert not mixed.bold


XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<pdf2xml>
<page number="1" height="2526" width="1786">
  <fontspec id="0" size="36" family="ABCDEF+TimesNewRomanPSMT"/>
  <text top="300" left="300" width="900" height="40" font="0"><b>Informe</b></text>
  <text top="360" left="300" width="900" height="40" font="0">   </text>
  <image top="30" left="30" width="300" height="150"/>
</page>
<page number="2" height="2526" width="1786">
  <text top="300" left="300" width="900" height="40" font="0">cuerpo</text>
  <image top="30" left="30" width="300" height="150"/>
  <image top="900" left="300" width="900" height="600"/>
</page>
<page number="3" height="2526" width="1786">
  <image top="30" left="30" width="300" height="150"/>
</page>
</pdf2xml>"""


def test_parse_pdftohtml() -> None:
    pages = parse_pdftohtml(XML)

    first = pages[0]
    assert first.number == 1
    assert first.width == pytest.approx(595.33, abs=0.01)
    [title] = first.fragments  # los fragmentos en blanco se descartan
    assert (title.text, title.bold, title.size, title.family) == (
        "Informe",
        True,
        12.0,
        "Times New Roman",
    )
    assert pages[1].fragments[0].family == "Times New Roman"  # el fontspec se reutiliza
    # El logo repetido en 3 páginas se descarta; la figura de la página 2 queda.
    assert [len(p.images) for p in pages] == [0, 1, 0]


def test_split_pages_pads_missing_pages() -> None:
    assert split_pages("uno\fdos\f", 3) == ("uno", "dos", "")
