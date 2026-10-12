"""Normalización de texto y patrones compartidos por el medidor.

Basado en `analizar_pdf.py` de la cátedra Taller de Proyecto II (UNLP),
https://github.com/tpII/ia-guidelines-taller (commit 65d2258). MIT, ver NOTICE.md.
"""

from __future__ import annotations

import re
import unicodedata

# Grupos: 1 tipo, 2 letra de apéndice opcional («A» en «Figura A1»), 3 número.
CAPTION = re.compile(
    r"^(Figura|Fig\.|Tabla|Imagen|Gr[aá]fico|Cuadro|Ilustraci[oó]n)\s*([A-Z]?)(\d+)\b",
    re.IGNORECASE,
)
TOC_LINE = re.compile(r"^(?P<t>.+?)\s*(?:(?:\s*[.\u2026]){2,}|\s{2,})\s*(?P<p>\d{1,3})\s*$")
INVISIBLE = re.compile("[\u2060\u200b\ufeff\u00a0]")  # espacios invisibles o no separables
NUMBERED = re.compile(r"^(\d+(\.\d+)*\.?|[a-z]\)|[IVX]+\.)\s+")
BULLET = re.compile(r"^\s*([\u2022\u25cf\u25aa\u25e6\u2023\-\u2013*]|\d{1,2}[.)]|[a-z][.)])\s")


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def squash(text: str) -> str:
    """Espacios simples: los títulos leídos de una tabla traen huecos de más."""
    return " ".join(text.split())


def normalize(text: str) -> str:
    """Minúsculas, sin tildes ni signos, espacios simples: para comparar títulos."""
    plain = re.sub(r"[^a-z0-9 ]+", " ", strip_accents(text).lower())
    return re.sub(r"\s+", " ", plain).strip()
