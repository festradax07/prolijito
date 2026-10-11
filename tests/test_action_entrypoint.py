"""Entrypoint de la GitHub Action, con un `prolijito` falso en el PATH (sin Docker ni poppler).

El falso devuelve 1 si el nombre del PDF contiene "mal", 2 si contiene "roto" y 0 si no.
"""

import os
import subprocess
from pathlib import Path

import pytest

ENTRYPOINT = Path(__file__).parents[1] / "scripts" / "action-entrypoint.sh"

FAKE_PROLIJITO = """#!/bin/sh
pdf="$2"
echo "check $*" >> "$CALLS"
for arg in "$@"; do
  if [ "$prev" = "--output" ]; then echo '{}' > "$arg"; fi
  prev="$arg"
done
case "$pdf" in *roto*) exit 2 ;; *mal*) exit 1 ;; esac
exit 0
"""


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "prolijito"
    fake.write_text(FAKE_PROLIJITO)
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("CALLS", str(tmp_path / "calls.txt"))
    monkeypatch.chdir(tmp_path)
    for name in ("docs/entregas/ia1.pdf", "docs/entregas/ia2-mal.pdf", "docs/entregas/sub/b.pdf"):
        Path(name).parent.mkdir(parents=True, exist_ok=True)
        Path(name).touch()
    return tmp_path


def run(paths: str, fail_on: str = "error") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/sh", str(ENTRYPOINT), "unlp-tp2", paths, "", fail_on, "reportes"],
        capture_output=True,
        text=True,
        check=False,
    )


def checked(workspace: Path) -> list[str]:
    calls = (workspace / "calls.txt").read_text().splitlines()
    return [c.split()[2] for c in calls if "--format github" in c]


def test_folder_is_searched_recursively(workspace: Path) -> None:
    result = run("docs/entregas")

    assert result.returncode == 1  # ia2-mal.pdf tiene errores
    assert checked(workspace) == [
        "docs/entregas/ia1.pdf",
        "docs/entregas/ia2-mal.pdf",
        "docs/entregas/sub/b.pdf",
    ]


def test_several_paths_one_per_line(workspace: Path) -> None:
    result = run("docs/entregas/ia1.pdf\n  docs/entregas/sub/b.pdf  \n\n")

    assert result.returncode == 0
    assert checked(workspace) == ["docs/entregas/ia1.pdf", "docs/entregas/sub/b.pdf"]


def test_duplicates_are_checked_once(workspace: Path) -> None:
    run("docs/entregas/ia1.pdf\ndocs/entregas\n")

    assert checked(workspace).count("docs/entregas/ia1.pdf") == 1


def test_one_json_report_per_pdf(workspace: Path) -> None:
    run("docs/entregas")

    assert sorted(p.name for p in (workspace / "reportes").iterdir()) == [
        "docs__entregas__ia1.json",
        "docs__entregas__ia2-mal.json",
        "docs__entregas__sub__b.json",
    ]


def test_fail_on_is_passed_to_each_check(workspace: Path) -> None:
    run("docs/entregas/ia1.pdf", fail_on="revisar")

    calls = (workspace / "calls.txt").read_text().splitlines()
    assert "--fail-on revisar" in calls[0]  # anotaciones: el umbral del input
    assert "--fail-on never" in calls[1]  # reporte JSON: nunca falla


def test_missing_path_is_reported_but_others_are_checked(workspace: Path) -> None:
    result = run("docs/entregas/ia1.pdf\ndocs/no-existe.pdf")

    assert result.returncode == 2
    assert "::error title=prolijito::No existe 'docs/no-existe.pdf'" in result.stdout
    assert checked(workspace) == ["docs/entregas/ia1.pdf"]


def test_failed_check_is_an_execution_error(workspace: Path) -> None:
    Path("docs/entregas/roto.pdf").touch()

    result = run("docs/entregas/roto.pdf")

    assert result.returncode == 2
    assert "No se pudo chequear 'docs/entregas/roto.pdf'" in result.stdout


@pytest.mark.parametrize("paths", ["", "\n  \n", "docs/vacia"])
def test_nothing_to_check_is_a_warning(workspace: Path, paths: str) -> None:
    Path("docs/vacia").mkdir()

    result = run(paths)

    assert result.returncode == 0
    assert "::warning title=prolijito::No hay PDFs" in result.stdout
