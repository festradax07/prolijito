"""Medidor basado en el script de la cátedra (third_party/formato-entregas). Ver ADR 0006.

El script se ejecuta como caja negra (`python -I ... --json`) y su salida se traduce al contrato
`Measurements`, compensando las diferencias conocidas.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from prolijito.application.errors import MeasurementError, MissingDependencyError
from prolijito.domain import (
    Caption,
    CaptionKind,
    Captions,
    FontUsage,
    Heading,
    Justification,
    JustificationState,
    LanguageFinding,
    LineSpacing,
    LineSpacingClass,
    Measurements,
    PageLocation,
    PageMismatch,
    Section,
    Structure,
    TocCheck,
    TocEntry,
    Typography,
    Unmeasured,
)

Json = dict[str, Any]

SCRIPT_ENV_VAR = "PROLIJITO_CATHEDRA_SCRIPT"
REQUIRED_TOOLS = ("pdftohtml", "pdftotext", "pdfinfo")

_EQUIVALENT_SUFFIX = re.compile(r"\s*\(equivalente a [^)]*\)$")
_NUMBERING = re.compile(r"^(\d+(\.\d+)*\.?|[a-z]\.|[ivx]+\.)\s+")
_BIBLIOGRAPHY = re.compile(r"^(bibliografia|referencias)( bibliograficas)?$")
_APPENDIX = re.compile(r"^(anexos?|apendices?)( [a-z0-9]+)?( |$)")
_JUSTIFICATION = {
    "sí": JustificationState.YES,
    "si": JustificationState.YES,
    "parcial": JustificationState.PARTIAL,
    "no": JustificationState.NO,
}
_CAPTION_KIND = {"Figura": CaptionKind.FIGURE, "Tabla": CaptionKind.TABLE}


def default_script_path() -> Path:
    """`$PROLIJITO_CATHEDRA_SCRIPT` o, en una copia del repo, `third_party/` en la raíz."""
    if env := os.environ.get(SCRIPT_ENV_VAR):
        return Path(env)
    repo_root = Path(__file__).resolve().parents[3]
    return repo_root / "third_party" / "formato-entregas" / "analizar_pdf.py"


class CathedraMeasurer:
    def __init__(
        self, script: Path | None = None, required_tools: Sequence[str] = REQUIRED_TOOLS
    ) -> None:
        self._script = script or default_script_path()
        self._required_tools = tuple(required_tools)

    def measure(self, document: Path) -> Measurements:
        self._check_dependencies()
        return parse_measurements(self._run(document))

    def _check_dependencies(self) -> None:
        missing = [tool for tool in self._required_tools if shutil.which(tool) is None]
        if missing:
            raise MissingDependencyError(
                f"faltan herramientas de sistema: {', '.join(missing)} (paquete poppler-utils). "
                "La imagen Docker de prolijito ya las incluye."
            )
        if not self._script.is_file():
            raise MissingDependencyError(f"no se encontró el medidor en '{self._script}'.")

    def _run(self, document: Path) -> Json:
        command = [sys.executable, "-I", str(self._script), str(document), "--json"]
        # Argumentos en lista, sin shell: el nombre del archivo no se interpreta.
        result = subprocess.run(command, capture_output=True, text=True, check=False)  # noqa: S603
        if result.returncode != 0:
            detail = result.stderr.strip().splitlines()[-1:] or ["sin detalle"]
            raise MeasurementError(f"el medidor falló con '{document}': {detail[0]}")
        try:
            data: Json = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise MeasurementError(f"el medidor devolvió una salida no válida: {error}") from error
        return data


# ---------- traducción JSON → Measurements ----------


def parse_measurements(data: Json) -> Measurements:
    try:
        structure = _structure(data["estructura"])
        return Measurements(
            page_count=int(data["paginas"]),
            typography=_typography(data["fuentes"]),
            line_spacing=_line_spacing(data["interlineado"]),
            justification=_justification(data["justificado"]),
            structure=structure,
            captions=_captions(data["epigrafes"], skip_cover=structure.cover_on_first_page),
            language=tuple(_language(item) for item in data["lenguaje"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise MeasurementError(f"salida inesperada del medidor: falta o sobra {error}") from error


def _font(raw: Json) -> FontUsage:
    family = _EQUIVALENT_SUFFIX.sub("", raw["familia"])
    return FontUsage(family=family, size_pt=float(raw["size"]), share_pct=float(raw["pct"]))


def _typography(raw: Json) -> Typography:
    # Se ignoran fuente_ok, tamano_ok y familias_no_permitidas: usan la norma fija del script.
    return Typography(body=_font(raw["cuerpo"]), others=tuple(_font(f) for f in raw["otras"]))


def _line_spacing(raw: Json) -> LineSpacing | Unmeasured:
    if "error" in raw:
        return Unmeasured(raw["error"])
    return LineSpacing(
        ratio=float(raw["ratio"]),
        spacing_class=LineSpacingClass(raw["clase"]),
        deviant_pages=tuple(raw["paginas_fuera"]),
        deviant_from=LineSpacingClass.ONE_AND_HALF,
    )


def _justification(raw: Json) -> Justification | Unmeasured:
    if "error" in raw:
        return Unmeasured(raw["error"])
    return Justification(
        state=_JUSTIFICATION[raw["justificado"]],
        aligned_pct=int(raw["pct_borde_derecho_alineado"]),
        doubtful_pages=tuple(raw["paginas_dudosas"]),
    )


def _section(raw: Json) -> Section:
    return Section(present=bool(raw["presente"]), pages=tuple(raw["paginas"]))


def _with_numbered_heading(
    section: Section, headings: list[Json], pattern: re.Pattern[str]
) -> Section:
    """El script no reconoce secciones numeradas ("6. Bibliografía"); se buscan en los títulos."""
    if section.present:
        return section
    found = tuple(h["pag"] for h in headings if pattern.search(_heading_key(h["txt"])))
    return Section(present=True, pages=found) if found else section


def _heading_key(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text.lower())
    plain = "".join(c for c in plain if not unicodedata.combining(c))
    plain = _NUMBERING.sub("", plain.strip())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", plain)).strip()


def _structure(raw: Json) -> Structure:
    headings: list[Json] = raw["titulos_detectados"]
    return Structure(
        cover_on_first_page=bool(raw["caratula"]["pag1_parece_caratula"]),
        toc=_section(raw["indice"]),
        figure_index=_section(raw["indice_figuras"]),
        table_index=_section(raw["indice_tablas"]),
        bibliography=_with_numbered_heading(_section(raw["bibliografia"]), headings, _BIBLIOGRAPHY),
        appendix=_with_numbered_heading(_section(raw["anexo"]), headings, _APPENDIX),
        toc_check=_toc_check(raw["cotejo_indice"]),
    )


def _toc_check(raw: Json) -> TocCheck:
    return TocCheck(
        entries_without_heading=tuple(
            TocEntry(e["titulo"], int(e["pag_declarada"]))
            for e in raw["entradas_sin_titulo_en_doc"]
        ),
        page_mismatches=tuple(
            PageMismatch(e["titulo"], int(e["pag_declarada"]), tuple(e["pag_real"]))
            for e in raw["pagina_distinta"]
        ),
        headings_without_entry=tuple(
            Heading(int(h["pag"]), h["txt"]) for h in raw["titulos_sin_entrada_en_indice"]
        ),
        page_offset=int(raw["desfasaje_paginas"]),
    )


def _captions(raw: Json, *, skip_cover: bool) -> Captions:
    in_index = {(c["tipo"], c["num"], c["pag"]): bool(c["en_indice"]) for c in raw["cotejo_indice"]}
    images = {int(page): int(n) for page, n in raw["imagenes_por_pagina"].items()}
    if skip_cover:
        images.pop(1, None)  # logos de la carátula: no son figuras
    return Captions(
        items=tuple(_caption(c, in_index) for c in raw["epigrafes"]),
        figures_consecutive=bool(raw["numeracion_figuras_correlativa"]),
        tables_consecutive=bool(raw["numeracion_tablas_correlativa"]),
        uncaptioned_images=tuple(_location(i) for i in raw["imagenes_grandes_sin_epigrafe"]),
        uncaptioned_tables=tuple(_location(t) for t in raw["tablas_sin_epigrafe"]),
        detected_tables=int(raw["tablas_detectadas"]),
        images_per_page=images,
    )


def _caption(raw: Json, in_index: dict[tuple[str, int, int], bool]) -> Caption:
    kind = _CAPTION_KIND[raw["tipo"]]
    below = raw.get("debajo_de_figura" if kind is CaptionKind.FIGURE else "debajo_de_tabla")
    return Caption(
        kind=kind,
        number=int(raw["num"]),
        page=int(raw["pag"]),
        text=raw["txt"],
        below=below,
        text_references=int(raw["referencias_en_texto"]),
        in_index=in_index.get((raw["tipo"], raw["num"], raw["pag"]), False),
    )


def _location(raw: Json) -> PageLocation:
    return PageLocation(page=int(raw["pag"]), top_pt=float(raw["top"]))


def _language(raw: Json) -> LanguageFinding:
    return LanguageFinding(
        page=int(raw["pag"]), kind=raw["tipo"], word=raw["palabra"], context=raw["contexto"]
    )
