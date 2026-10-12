"""PDFs de prueba propios (tests/fixtures/pdf/) medidos a partir de la salida guardada de poppler.

Así la cadena completa del medidor se prueba sin poppler instalado. `build.sh` regenera los PDFs y
esa salida; un test de sistema verifica que siga coincidiendo con poppler real.
"""

from pathlib import Path

from prolijito.adapters.pdf import measure_document
from prolijito.adapters.pdf.poppler import Document, parse_pdftohtml, split_pages
from prolijito.domain import Measurements

PDFS = Path(__file__).parent / "fixtures" / "pdf"
STORED = PDFS / "poppler"
NAMES = ("cumple", "interlineado-simple", "con-errores")


def stored_document(name: str) -> Document:
    pages = parse_pdftohtml((STORED / f"{name}.xml").read_bytes())
    texts = split_pages((STORED / f"{name}.txt").read_text(encoding="utf-8"), len(pages))
    return Document(pages=pages, texts=texts)


def stored_measurements(name: str) -> Measurements:
    return measure_document(stored_document(name))
