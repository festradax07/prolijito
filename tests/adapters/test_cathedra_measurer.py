import copy
import json
from pathlib import Path
from typing import Any

import pytest

from prolijito.adapters.cathedra_measurer import (
    SCRIPT_ENV_VAR,
    CathedraMeasurer,
    default_script_path,
    parse_measurements,
)
from prolijito.application.errors import MeasurementError, MissingDependencyError
from prolijito.domain import (
    CaptionKind,
    JustificationState,
    LineSpacing,
    LineSpacingClass,
    Unmeasured,
)

FIXTURE = Path(__file__).parents[1] / "fixtures" / "mediciones" / "tp2-informe-avance.json"
# PDFs reales para pruebas locales: se ponen en docs/doc_test/ (ignorada por git).
LOCAL_PDFS = sorted((Path(__file__).parents[2] / "docs" / "doc_test").glob("*.pdf"))


@pytest.fixture
def raw() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return data


def test_parses_typography_and_strips_equivalent_suffix(raw: dict[str, Any]) -> None:
    raw["fuentes"]["cuerpo"]["familia"] = "Liberation Serif (equivalente a Times)"

    m = parse_measurements(raw)

    assert m.typography.body.family == "Liberation Serif"
    assert m.typography.body.size_pt == 12.0
    assert {f.family for f in m.typography.others} >= {"CourierNew", "Arial"}


def test_parses_line_spacing_and_justification(raw: dict[str, Any]) -> None:
    m = parse_measurements(raw)

    assert isinstance(m.line_spacing, LineSpacing)
    assert m.line_spacing.spacing_class is LineSpacingClass.ONE_AND_HALF
    assert m.line_spacing.deviant_from is LineSpacingClass.ONE_AND_HALF
    assert m.justification.state is JustificationState.YES  # type: ignore[union-attr]


def test_measurer_errors_become_unmeasured(raw: dict[str, Any]) -> None:
    raw["interlineado"] = {"error": "no se encontraron párrafos de cuerpo suficientes"}
    raw["justificado"] = {"error": "pocas líneas largas para evaluar"}

    m = parse_measurements(raw)

    assert m.line_spacing == Unmeasured("no se encontraron párrafos de cuerpo suficientes")
    assert isinstance(m.justification, Unmeasured)


def test_detects_numbered_bibliography_missed_by_the_script(raw: dict[str, Any]) -> None:
    assert raw["estructura"]["bibliografia"]["presente"] is False  # falso negativo del script

    m = parse_measurements(raw)

    assert m.structure.bibliography.present
    assert m.structure.bibliography.pages == (18,)


def test_numbered_heading_fallback_does_not_invent_sections(raw: dict[str, Any]) -> None:
    raw["estructura"]["titulos_detectados"] = [{"pag": 3, "txt": "1. Introducción", "size": 20}]

    assert not parse_measurements(raw).structure.bibliography.present


def test_cover_logos_are_not_figures(raw: dict[str, Any]) -> None:
    m = parse_measurements(raw)

    assert 1 not in m.captions.images_per_page
    assert m.captions.images_per_page[17] == 2


def test_cover_images_kept_when_page_one_is_not_a_cover(raw: dict[str, Any]) -> None:
    raw["estructura"]["caratula"]["pag1_parece_caratula"] = False

    assert parse_measurements(raw).captions.images_per_page[1] == 2


def test_captions_are_joined_with_index_check(raw: dict[str, Any]) -> None:
    m = parse_measurements(raw)

    tables = m.captions.of_kind(CaptionKind.TABLE)
    assert len(tables) == 8
    assert len(m.captions.of_kind(CaptionKind.FIGURE)) == 6
    assert tables[1].below is False  # Tabla 2: epígrafe arriba
    assert not any(c.in_index for c in m.captions.items)


def test_toc_check_and_language(raw: dict[str, Any]) -> None:
    m = parse_measurements(raw)

    assert len(m.structure.toc_check.page_mismatches) == 12
    assert m.structure.toc_check.page_mismatches[0].actual_pages == (7,)
    assert [f.word for f in m.language] == ["tomamos"]


@pytest.mark.parametrize("missing", ["fuentes", "estructura", "epigrafes"])
def test_unexpected_output_is_a_measurement_error(raw: dict[str, Any], missing: str) -> None:
    broken = copy.deepcopy(raw)
    del broken[missing]

    with pytest.raises(MeasurementError, match="salida inesperada"):
        parse_measurements(broken)


# ---------- ejecución del script ----------


def fake_script(tmp_path: Path, body: str) -> Path:
    script = tmp_path / "medidor.py"
    script.write_text(body, encoding="utf-8")
    return script


def test_runs_the_script_and_parses_its_json(tmp_path: Path) -> None:
    script = fake_script(
        tmp_path, f"import sys; sys.stdout.write(open({str(FIXTURE)!r}, encoding='utf-8').read())"
    )

    m = CathedraMeasurer(script, required_tools=()).measure(tmp_path / "doc.pdf")

    assert m.page_count == 19


def test_script_failure_is_a_measurement_error(tmp_path: Path) -> None:
    script = fake_script(tmp_path, "import sys; sys.exit('pdftohtml: archivo dañado')")

    with pytest.raises(MeasurementError, match="archivo dañado"):
        CathedraMeasurer(script, required_tools=()).measure(tmp_path / "doc.pdf")


def test_invalid_json_is_a_measurement_error(tmp_path: Path) -> None:
    script = fake_script(tmp_path, "print('no es json')")

    with pytest.raises(MeasurementError, match="no válida"):
        CathedraMeasurer(script, required_tools=()).measure(tmp_path / "doc.pdf")


def test_missing_system_tool_is_reported(tmp_path: Path) -> None:
    measurer = CathedraMeasurer(fake_script(tmp_path, ""), required_tools=("no-existe-xyz",))

    with pytest.raises(MissingDependencyError, match="no-existe-xyz"):
        measurer.measure(tmp_path / "doc.pdf")


def test_missing_script_is_reported(tmp_path: Path) -> None:
    with pytest.raises(MissingDependencyError, match="no se encontró el medidor"):
        CathedraMeasurer(tmp_path / "nada.py", required_tools=()).measure(tmp_path / "doc.pdf")


def test_default_script_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(SCRIPT_ENV_VAR, raising=False)
    assert default_script_path().is_file()

    monkeypatch.setenv(SCRIPT_ENV_VAR, str(tmp_path / "otro.py"))
    assert default_script_path() == tmp_path / "otro.py"


@pytest.mark.system
@pytest.mark.skipif(not LOCAL_PDFS, reason="sin PDFs locales en docs/doc_test/")
@pytest.mark.parametrize("pdf", LOCAL_PDFS, ids=lambda p: p.name)
def test_measures_local_pdfs(pdf: Path) -> None:
    m = CathedraMeasurer().measure(pdf)

    assert m.page_count > 0
    assert m.typography.body.size_pt > 0
