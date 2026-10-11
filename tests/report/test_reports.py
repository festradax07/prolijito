"""Snapshots de los reportes sobre las mediciones reales (anonimizadas) de un informe de TP2.

Para regenerarlos después de un cambio intencional: UPDATE_SNAPSHOTS=1 pytest tests/report
"""

import json
import os
from pathlib import Path

import pytest

from prolijito.adapters.cathedra_measurer import parse_measurements
from prolijito.adapters.fix_catalog import YamlFixCatalog
from prolijito.adapters.yaml_profiles import YamlProfileRepository, builtin_profiles_dir
from prolijito.domain import CheckResult, Severity, Violation
from prolijito.report import RENDERERS, render_github, render_json, render_markdown
from prolijito.report.labels import status
from prolijito.validate import evaluate
from tests.builders import a_profile

FIXTURE = Path(__file__).parents[1] / "fixtures" / "mediciones" / "tp2-informe-avance.json"
SNAPSHOTS = Path(__file__).parent / "snapshots"
SUFFIXES = {"md": "md", "json": "json", "github": "txt"}


@pytest.fixture(scope="module")
def tp2_result() -> CheckResult:
    measurements = parse_measurements(json.loads(FIXTURE.read_text(encoding="utf-8")))
    profile = YamlProfileRepository([builtin_profiles_dir()]).load("unlp-tp2")
    violations = evaluate(measurements, profile, YamlFixCatalog().how_to_fix())
    return CheckResult("entregas/entrega.pdf", profile, violations)


@pytest.mark.parametrize("fmt", list(RENDERERS))
def test_report_snapshot(tp2_result: CheckResult, fmt: str) -> None:
    rendered = RENDERERS[fmt](tp2_result)
    snapshot = SNAPSHOTS / f"tp2-informe-avance.{SUFFIXES[fmt]}"
    if os.environ.get("UPDATE_SNAPSHOTS") or not snapshot.exists():
        snapshot.write_text(rendered, encoding="utf-8")

    assert rendered == snapshot.read_text(encoding="utf-8")


def clean_result(*violations: Violation) -> CheckResult:
    return CheckResult("informe.pdf", a_profile(), violations)


@pytest.mark.parametrize(
    ("violations", "expected"),
    [
        ((), "✅ listo para entregar"),
        ((Violation("LEN-01", Severity.REVIEW, "x"),), "✅ sin errores · 1 punto a revisar"),
        (
            (Violation("TIP-03", Severity.ERROR, "x"), Violation("TIP-01", Severity.ERROR, "y")),
            "❌ con 2 errores y 0 puntos a revisar",
        ),
    ],
)
def test_status(violations: tuple[Violation, ...], expected: str) -> None:
    assert status(clean_result(*violations)) == expected


def test_markdown_of_a_clean_document_shows_all_criteria_ok() -> None:
    md = render_markdown(clean_result())

    assert "## Errores" not in md
    assert md.count("| ✅ |") == 22


def test_json_follows_the_violation_contract() -> None:
    violation = Violation(
        "TIP-03",
        Severity.ERROR,
        "Interlineado simple.",
        page=4,
        expected="1,5",
        measured="1,33 (simple)",
        how_to_fix={"typst": "x"},
        autofixable=True,
    )

    data = json.loads(render_json(clean_result(violation)))

    assert data["estado"] == "con_errores"
    assert data["resumen"] == {"error": 1, "revisar": 0, "info": 0}
    assert data["violaciones"][0] == {
        "id": "TIP-03",
        "severidad": "error",
        "categoria": "tipografia",
        "pagina": 4,
        "esperado": "1,5",
        "medido": "1,33 (simple)",
        "mensaje": "Interlineado simple.",
        "como_arreglar": {"typst": "x"},
        "autofixable": True,
        "ocurrencias": [],
    }


def test_github_annotations_by_severity() -> None:
    result = CheckResult(
        "docs/informe.pdf",
        a_profile(),
        (
            Violation("TIP-03", Severity.ERROR, "Interlineado simple.", page=4),
            Violation("LEN-01", Severity.REVIEW, "Posible voseo."),
            Violation("EST-06", Severity.INFO, "No hay anexo."),
        ),
    )

    lines = render_github(result).splitlines()

    assert (
        lines[0]
        == "::error file=docs/informe.pdf,title=TIP-03 Interlineado::Interlineado simple. (p. 4)"
    )
    assert lines[1].startswith("::warning file=docs/informe.pdf,title=LEN-01 ")
    assert lines[2].startswith("::notice ")
    assert lines[3].startswith("prolijito: docs/informe.pdf — perfil unlp-tp2@1.0.0 — ❌")


def test_github_escapes_workflow_command_characters() -> None:
    violation = Violation("TIT-03", Severity.REVIEW, "100% listo\nsegunda línea")
    result = CheckResult("a:b,c.pdf", a_profile(), (violation,))

    first = render_github(result).splitlines()[0]

    assert first == (
        "::warning file=a%3Ab%2Cc.pdf,title=TIT-03 Títulos con entrada en el índice"
        "::100%25 listo%0Asegunda línea"
    )
