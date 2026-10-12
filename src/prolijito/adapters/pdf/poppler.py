"""Extracción del PDF con poppler: fragmentos de texto, imágenes y texto plano por página.

Basado en `analizar_pdf.py` de la cátedra Taller de Proyecto II (UNLP),
https://github.com/tpII/ia-guidelines-taller (commit 65d2258). MIT, ver NOTICE.md.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from prolijito.application.errors import MeasurementError

ZOOM = 3  # pdftohtml redondea los tamaños a entero y limita el zoom a 3: precisión ≈0,3 pt
SAME_LINE_PT = 2  # fragmentos con el mismo top (±2 pt) forman una línea visual
TEMPLATE_IMAGE_PAGES = 3  # la misma imagen en 3 o más páginas es logo o adorno de plantilla

_SUBSET_PREFIX = re.compile(r"^[A-Z]{6}\+")
_STYLE_SUFFIX = re.compile(r"(PSMT|PS|MT|Regular|Bold|Italic|BoldItalic|BoldMT|ItalicMT)+$")
_KNOWN_FAMILIES = (
    (re.compile(r"timesnewroman|times", re.IGNORECASE), "Times New Roman"),
    (re.compile(r"^arial", re.IGNORECASE), "Arial"),
    (re.compile(r"liberationserif", re.IGNORECASE), "Liberation Serif"),
    (re.compile(r"liberationsans", re.IGNORECASE), "Liberation Sans"),
    (re.compile(r"^libertinus", re.IGNORECASE), "Libertinus"),
    (re.compile(r"^carlito", re.IGNORECASE), "Carlito"),
)


def font_family(name: str) -> str:
    """Nombre de familia legible a partir del nombre interno de la fuente en el PDF."""
    base = re.split(r"[-,]", _SUBSET_PREFIX.sub("", name))[0]
    base = _STYLE_SUFFIX.sub("", base)
    for pattern, family in _KNOWN_FAMILIES:
        if pattern.search(base):
            return family
    return base


@dataclass(frozen=True, slots=True)
class Fragment:
    top: float
    left: float
    width: float
    height: float
    size: float
    family: str
    bold: bool
    text: str


@dataclass(frozen=True, slots=True)
class Image:
    top: float
    left: float
    width: float
    height: float

    @property
    def signature(self) -> tuple[int, int, int, int]:
        return round(self.top), round(self.left), round(self.width), round(self.height)


@dataclass(frozen=True, slots=True)
class Line:
    top: float
    left: float
    right: float
    fragments: tuple[Fragment, ...]
    text: str
    size: float
    family: str
    bold: bool


@dataclass(frozen=True)
class Page:
    number: int
    height: float
    width: float
    fragments: tuple[Fragment, ...]
    images: tuple[Image, ...]

    @cached_property
    def lines(self) -> tuple[Line, ...]:
        return group_lines(self.fragments)


@dataclass(frozen=True, slots=True)
class Document:
    pages: tuple[Page, ...]
    texts: tuple[str, ...]
    """Texto de cada página con `pdftotext -layout`."""


def group_lines(fragments: Iterable[Fragment]) -> tuple[Line, ...]:
    """Agrupa fragmentos en líneas visuales: mismo top (±2 pt), ordenados de izquierda a derecha."""
    groups: list[list[Fragment]] = []
    for fragment in sorted(fragments, key=lambda f: (round(f.top), f.left)):
        if groups and abs(groups[-1][0].top - fragment.top) <= SAME_LINE_PT:
            groups[-1].append(fragment)
        else:
            groups.append([fragment])
    return tuple(_line(group) for group in groups)


def _line(group: Sequence[Fragment]) -> Line:
    # El orden por top redondeado puede invertir fragmentos de una misma línea con tops apenas
    # distintos (100 y 101,5): dentro de la línea se ordenan de izquierda a derecha.
    fragments = sorted(group, key=lambda f: f.left)
    main = max(fragments, key=lambda f: len(f.text))
    return Line(
        top=group[0].top,
        left=fragments[0].left,
        right=max(f.left + f.width for f in fragments),
        fragments=tuple(fragments),
        text="".join(f.text for f in fragments).strip(),
        size=main.size,
        family=main.family,
        bold=all(f.bold for f in fragments if f.text.strip()),
    )


# ---------- poppler ----------


def extract(pdf: Path) -> Document:
    with tempfile.TemporaryDirectory(prefix="prolijito_") as tmp:
        base = Path(tmp) / "doc"
        _run(["pdftohtml", "-xml", "-zoom", str(ZOOM), "-q", str(pdf), str(base)])
        xml = base.with_suffix(".xml").read_bytes()
    pages = parse_pdftohtml(xml)
    texts = split_pages(_run(["pdftotext", "-layout", str(pdf), "-"]), len(pages))
    return Document(pages=pages, texts=texts)


def _run(command: list[str]) -> str:
    # Lista de argumentos, sin shell: el nombre del archivo no se interpreta.
    result = subprocess.run(command, capture_output=True, text=True, check=False)  # noqa: S603
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()[-1:] or ["¿es un PDF válido?"]
        raise MeasurementError(f"{command[0]} no pudo leer el PDF: {detail[0]}")
    return result.stdout


def split_pages(text: str, page_count: int) -> tuple[str, ...]:
    """`pdftotext` separa las páginas con un salto de página (\\f)."""
    pages = text.split("\f")[:page_count]
    return tuple(pages + [""] * (page_count - len(pages)))


def parse_pdftohtml(xml: bytes) -> tuple[Page, ...]:
    """Páginas a partir de la salida `pdftohtml -xml`, sin las imágenes de plantilla."""
    # XML generado localmente por pdftohtml a partir del PDF del usuario.
    root = ET.fromstring(xml)  # noqa: S314
    fonts: dict[str, tuple[float, str]] = {}  # los fontspec se declaran una vez y se reutilizan
    pages = [_page(element, fonts) for element in root.findall("page")]
    return _without_template_images(pages)


def _page(element: ET.Element, fonts: dict[str, tuple[float, str]]) -> Page:
    for spec in element.findall("fontspec"):
        fonts[spec.get("id", "")] = (
            int(spec.get("size", "0")) / ZOOM,
            font_family(spec.get("family", "")),
        )
    fragments = []
    for node in element.findall("text"):
        text = "".join(node.itertext())
        if text.strip():
            size, family = fonts[node.get("font", "")]
            fragments.append(
                Fragment(
                    *_box(node),
                    size=size,
                    family=family,
                    bold=node.find(".//b") is not None,
                    text=text,
                )
            )
    images = tuple(Image(*_box(node)) for node in element.findall("image"))
    return Page(
        number=int(element.get("number", "0")),
        height=int(element.get("height", "0")) / ZOOM,
        width=int(element.get("width", "0")) / ZOOM,
        fragments=tuple(fragments),
        images=images,
    )


def _box(node: ET.Element) -> tuple[float, float, float, float]:
    return tuple(int(node.get(k, "0")) / ZOOM for k in ("top", "left", "width", "height"))  # type: ignore[return-value]


def _without_template_images(pages: list[Page]) -> tuple[Page, ...]:
    """Logos y adornos: la misma imagen (posición y tamaño) en 3 o más páginas no es una figura."""
    counts = Counter(image.signature for page in pages for image in page.images)
    return tuple(
        Page(
            number=page.number,
            height=page.height,
            width=page.width,
            fragments=page.fragments,
            images=tuple(i for i in page.images if counts[i.signature] < TEMPLATE_IMAGE_PAGES),
        )
        for page in pages
    )
