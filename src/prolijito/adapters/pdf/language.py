"""Lenguaje: candidatos de primera o segunda persona, voseo y tuteo. Siempre para revisar.

Basado en `analizar_pdf.py` de la cátedra Taller de Proyecto II (UNLP),
https://github.com/tpII/ia-guidelines-taller (commit 65d2258). MIT, ver NOTICE.md.
"""

from __future__ import annotations

import re
from collections.abc import Collection, Iterator, Sequence

from prolijito.adapters.pdf.text import normalize
from prolijito.domain import LanguageFinding

CONTEXT_CHARS = 60
MIN_PLURAL_CHARS = 5
MIN_VOSEO_CHARS = 4

PRONOUNS = re.compile(
    r"\b(yo|nosotros|nosotras|nuestro|nuestra|nuestros|nuestras|conmigo|vos|ustedes|tú|tuyo|tuya"
    r"|tuyos|tuyas)\b",
    re.IGNORECASE,
)
VOSEO = re.compile(
    r"\b(tenés|podés|querés|sabés|hacés|decís|sos|mirá|fijate|acordate|andá|vení|hacé|tené|usá"
    r"|pensá|imaginá|vas a ver|te das cuenta|tenes|podes|queres|sabes|haces|puedes|tienes|quieres"
    r"|debes|ves)\b",
    re.IGNORECASE,
)
FIRST_SINGULAR = re.compile(
    r"\b(creo|pienso|considero|propongo|quiero|voy a|opino|espero|me parece|mi proyecto"
    r"|mi trabajo|mi propuesta)\b",
    re.IGNORECASE,
)
FIRST_PLURAL = re.compile(
    r"\b([a-záéíóúñ]{2,}?(?:ábamos|íamos|aremos|eremos|iremos|amos|emos|imos))\b", re.IGNORECASE
)
VOSEO_ENDING = re.compile(r"\b[a-záéíóúñ]{3,}(ás|és|ís)\b")

_PATTERNS = (
    ("pronombre 1ª/2ª persona", PRONOUNS),
    ("voseo/tuteo", VOSEO),
    ("1ª persona singular", FIRST_SINGULAR),
)
# Palabras terminadas en -amos/-emos/-imos que no son verbos en primera persona del plural.
NOT_PLURAL_VERBS = frozenset(
    (
        "gramos",
        "kilogramos",
        "miligramos",
        "tramos",
        "ramos",
        "reclamos",
        "minimos",
        "maximos",
        "optimos",
        "ultimos",
        "proximos",
        "mismos",
        "decimos",
        "intimos",
        "legitimos",
        "infimos",
        "pesimos",
        "primos",
        "remos",
        "programos",
        "cosmos",
        "dinamos",
        "diagramos",
        "ambos",
        "lemos",
        "monimos",
        "anonimos",
        "sinonimos",
        "antonimos",
        "homonimos",
        "autonomos",
        "economos",
        "tomos",
        "atomos",
        "aromas",
        "ramas",
        "textos",
        "extremos",
        "supremos",
        "internos",
        "externos",
        "modernos",
        "eternos",
        "cuadernos",
        "gobiernos",
        "cremos",
        "temos",
        "domos",
        "trimos",
    )
)
# Palabras agudas terminadas en -ás/-és/-ís que no son voseo.
NOT_VOSEO = frozenset(
    (
        "ademas",
        "despues",
        "traves",
        "ingles",
        "frances",
        "interes",
        "pais",
        "quizas",
        "jamas",
        "atras",
        "detras",
        "compas",
        "anis",
        "cortes",
        "portugues",
        "japones",
        "holandes",
        "escoces",
        "danes",
        "marques",
        "revés",
        "reves",
        "estres",
        "envés",
        "enves",
        "demas",
        "paris",
        "paises",
        "reles",
        "cafes",
        "bebes",
        "chales",
        "carnes",
        "cipres",
        "burgues",
        "vienes",
        "montes",
    )
)


def find_language_issues(
    texts: Sequence[str], excluded_pages: Collection[int]
) -> tuple[LanguageFinding, ...]:
    return tuple(
        finding
        for number, text in enumerate(texts, 1)
        if number not in excluded_pages
        for finding in _page_findings(number, re.sub(r"\s+", " ", text))
    )


def _page_findings(page: int, text: str) -> Iterator[LanguageFinding]:
    for kind, pattern in _PATTERNS:
        for m in pattern.finditer(text):
            yield _finding(page, kind, m.group(0), text, m)
    for m in FIRST_PLURAL.finditer(text):
        if _is_plural_verb(m.group(1)):
            yield _finding(page, "verbo 1ª persona plural (candidato)", m.group(1), text, m)
    for m in VOSEO_ENDING.finditer(text):
        word = normalize(m.group(0))
        if word not in NOT_VOSEO and len(word) >= MIN_VOSEO_CHARS:
            yield _finding(page, "posible voseo (terminación -ás/-és/-ís)", m.group(0), text, m)


def _is_plural_verb(word: str) -> bool:
    plain = normalize(word)
    if plain in NOT_PLURAL_VERBS or len(plain) < MIN_PLURAL_CHARS:
        return False
    # Una tilde antes de la terminación indica sustantivo o adjetivo, salvo -ábamos/-íamos.
    accented_stem = re.search(r"[áéíóú]", word[:-4]) is not None
    return not accented_stem or word.lower().endswith(("ábamos", "íamos"))


def _finding(page: int, kind: str, word: str, text: str, m: re.Match[str]) -> LanguageFinding:
    context = text[max(0, m.start() - CONTEXT_CHARS) : m.end() + CONTEXT_CHARS].strip()
    return LanguageFinding(page=page, kind=kind, word=word, context=context)
