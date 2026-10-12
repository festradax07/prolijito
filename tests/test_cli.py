import json
import subprocess
import sys
from pathlib import Path

import pytest

from prolijito import __version__, cli
from prolijito.cli import ExitCode, main, run
from prolijito.domain import Measurements
from tests.stored_pdfs import stored_measurements


def test_version_prints_package_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_help_lists_commands(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    assert exit_info.value.code == 0
    out = capsys.readouterr().out
    for command in ("check", "fix", "review", "new", "profiles"):
        assert command in out


def test_missing_command_is_execution_error() -> None:
    with pytest.raises(SystemExit) as exit_info:
        main([])

    assert exit_info.value.code == ExitCode.EXECUTION_ERROR


def test_check_requires_profile(tmp_path: Path) -> None:
    document = tmp_path / "informe.pdf"
    document.touch()

    with pytest.raises(SystemExit) as exit_info:
        main(["check", str(document)])

    assert exit_info.value.code == ExitCode.EXECUTION_ERROR


def test_check_rejects_unknown_format(tmp_path: Path) -> None:
    document = tmp_path / "informe.pdf"
    document.touch()

    with pytest.raises(SystemExit) as exit_info:
        main(["check", str(document), "--profile", "unlp-tp2", "--format", "html"])

    assert exit_info.value.code == ExitCode.EXECUTION_ERROR


def test_check_missing_file_is_execution_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "no-existe.pdf"

    code = main(["check", str(missing), "--profile", "unlp-tp2"])

    assert code == ExitCode.EXECUTION_ERROR
    assert "no existe el archivo" in capsys.readouterr().err


@pytest.mark.parametrize(
    "argv",
    [
        ["fix", "informe.typ", "--profile", "unlp-tp2"],
        ["review", "informe.pdf", "--profile", "unlp-tp2"],
        ["new", "unlp-tp2", "informe.typ"],
    ],
)
def test_future_commands_answer_not_implemented(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(argv)

    assert code == ExitCode.EXECUTION_ERROR
    assert f"'{argv[0]}' todavía no está implementado" in capsys.readouterr().err


def test_run_exits_with_main_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["prolijito", "fix", "a.typ", "--profile", "unlp-tp2"])

    with pytest.raises(SystemExit) as exit_info:
        run()

    assert exit_info.value.code == ExitCode.EXECUTION_ERROR


def test_module_is_executable() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "prolijito", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert __version__ in result.stdout


def test_profiles_lists_builtin_and_shows_how_to_create_one(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["profiles"]) == ExitCode.OK

    out = capsys.readouterr().out
    assert "unlp-tp2" in out
    assert "informe-tecnico-es" in out
    assert "--template" in out


def test_profiles_marks_custom_profiles_with_their_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["profiles", "--template", "mi-catedra"])
    (tmp_path / "mi-catedra.yaml").write_text(capsys.readouterr().out)

    assert main(["profiles", "--profiles-dir", str(tmp_path)]) == ExitCode.OK
    assert f"[{tmp_path / 'mi-catedra.yaml'}]" in capsys.readouterr().out


def test_template_defaults_to_mi_perfil(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["profiles", "--template"]) == ExitCode.OK
    assert "id: mi-perfil" in capsys.readouterr().out


def test_template_rejects_invalid_id(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["profiles", "--template", "Mi Catedra"]) == ExitCode.EXECUTION_ERROR
    assert "kebab-case" in capsys.readouterr().err


def test_missing_profiles_dir_is_execution_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["profiles", "--profiles-dir", str(tmp_path / "no-existe")])

    assert code == ExitCode.EXECUTION_ERROR
    assert "no existe la carpeta de perfiles" in capsys.readouterr().err


# ---------- check de punta a punta (medidor falso: sin poppler) ----------


class FixtureMeasurer:
    def measure(self, document: Path) -> Measurements:
        return stored_measurements("con-errores")


@pytest.fixture
def pdf(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(cli, "_measurer", FixtureMeasurer)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    document = tmp_path / "entrega.pdf"
    document.touch()
    return document


def test_check_prints_markdown_and_fails_on_errors(
    pdf: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["check", str(pdf), "--profile", "unlp-tp2"])

    out = capsys.readouterr().out
    assert code == ExitCode.VIOLATIONS
    assert out.startswith("# Chequeo de formato — entrega.pdf — perfil unlp-tp2@1.0.0")
    assert "TIT-02" in out


def test_check_json_to_output_file(pdf: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = pdf.parent / "reporte.json"

    main(["check", str(pdf), "--profile", "unlp-tp2", "--format", "json", "--output", str(output)])

    assert json.loads(output.read_text())["perfil"] == "unlp-tp2@1.0.0"
    assert "reporte guardado" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("fail_on", "code"), [("never", ExitCode.OK), ("error", ExitCode.VIOLATIONS)]
)
def test_check_fail_on(pdf: Path, fail_on: str, code: ExitCode) -> None:
    assert main(["check", str(pdf), "--profile", "unlp-tp2", "--fail-on", fail_on]) == code


def test_lenient_profile_only_reports_what_it_requires(
    pdf: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["check", str(pdf), "--profile", "informe-tecnico-es", "--format", "json"])

    severities = {
        v["id"]: v["severidad"] for v in json.loads(capsys.readouterr().out)["violaciones"]
    }
    assert severities["EST-03"] == "info"  # en la base, el índice de figuras es opcional
    assert "TIP-04" not in severities  # y el justificado no se verifica


def test_check_github_writes_annotations_and_job_summary(
    pdf: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    summary = pdf.parent / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))

    main(["check", str(pdf), "--profile", "unlp-tp2", "--format", "github"])

    lines = capsys.readouterr().out.splitlines()
    assert any(line.startswith("::error file=") for line in lines)
    assert lines[-1].startswith("prolijito: ")
    assert summary.read_text().startswith("# Chequeo de formato")


def test_check_with_unknown_profile_is_execution_error(
    pdf: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["check", str(pdf), "--profile", "no-existe"]) == ExitCode.EXECUTION_ERROR
    assert "no existe el perfil 'no-existe'" in capsys.readouterr().err
