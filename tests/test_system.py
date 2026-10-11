"""Definición de terminado del MVP con PDFs propios (fuente: tests/fixtures/pdf/informe.typ)."""

import json
from pathlib import Path

import pytest

from prolijito.cli import ExitCode, main

PDFS = Path(__file__).parent / "fixtures" / "pdf"

pytestmark = pytest.mark.system


def test_compliant_pdf_passes(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["check", str(PDFS / "cumple.pdf"), "--profile", "unlp-tp2", "--format", "json"])

    report = json.loads(capsys.readouterr().out)
    assert code == ExitCode.OK
    assert report["resumen"]["error"] == 0
    assert report["resumen"]["revisar"] == 0


def test_single_spacing_fails_with_tip03(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        [
            "check",
            str(PDFS / "interlineado-simple.pdf"),
            "--profile",
            "unlp-tp2",
            "--format",
            "json",
        ]
    )

    errors = [
        v for v in json.loads(capsys.readouterr().out)["violaciones"] if v["severidad"] == "error"
    ]
    assert code == ExitCode.VIOLATIONS
    assert [v["id"] for v in errors] == ["TIP-03"]
