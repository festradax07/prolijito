import re
from pathlib import Path

import pytest

from prolijito.adapters.yaml_profiles import (
    PROFILES_ENV_VAR,
    YamlProfileRepository,
    builtin_profiles_dir,
    deep_merge,
    profile_template,
)
from prolijito.application.errors import ProfileError
from prolijito.domain import CaptionPosition, LineSpacingClass, Requirement, Severity

BUILTIN = builtin_profiles_dir()

CHILD = """\
id: {id}
version: 1.0.0
extends: unlp-tp2@1
descripcion: Perfil de prueba
{extra}
"""


def write(directory: Path, profile_id: str, extra: str = "", body: str | None = None) -> Path:
    path = directory / f"{profile_id}.yaml"
    path.write_text(body if body is not None else CHILD.format(id=profile_id, extra=extra))
    return path


@pytest.fixture
def repo(tmp_path: Path) -> YamlProfileRepository:
    return YamlProfileRepository([tmp_path, BUILTIN])


# ---------- perfiles incluidos ----------


def test_builtin_unlp_tp2_matches_the_rubric() -> None:
    profile = YamlProfileRepository([BUILTIN]).load("unlp-tp2")

    assert profile.reference == "unlp-tp2@1.0.0"
    assert profile.layout.fonts == ("Arial", "Times New Roman", "Libertinus")
    assert profile.layout.body_size_pt == 12.0
    assert profile.layout.size_tolerance_pt == 0.6
    assert profile.layout.line_spacing is LineSpacingClass.ONE_AND_HALF
    assert profile.layout.justified
    assert profile.layout.figure_captions is CaptionPosition.BELOW
    assert profile.layout.table_captions is CaptionPosition.BELOW
    assert profile.structure.figure_index is Requirement.IF_CONTENT
    assert profile.structure.appendix is Requirement.OPTIONAL
    assert profile.norm_source == "profiles/normas/unlp-tp2-rubrica.md"


def test_builtin_base_profile_is_lenient() -> None:
    profile = YamlProfileRepository([BUILTIN]).load("informe-tecnico-es")

    assert not profile.layout.justified
    assert profile.layout.allows_font("Calibri")
    assert profile.structure.figure_index is Requirement.OPTIONAL


def test_lists_builtin_profiles() -> None:
    ids = [s.id for s in YamlProfileRepository([BUILTIN]).available()]

    assert ids == ["informe-tecnico-es", "unlp-tp2"]


# ---------- resolución ----------


def test_loads_by_path_and_inherits_from_builtin(
    tmp_path: Path, repo: YamlProfileRepository
) -> None:
    path = write(tmp_path, "mi-catedra", "layout:\n  interlineado: doble")

    profile = repo.load(str(path))

    assert profile.id == "mi-catedra"
    assert profile.layout.line_spacing is LineSpacingClass.DOUBLE
    assert profile.layout.fonts == ("Arial", "Times New Roman", "Libertinus")  # heredado


def test_profiles_dir_takes_priority_over_builtin(tmp_path: Path) -> None:
    write(
        tmp_path,
        "unlp-tp2",
        body=(BUILTIN / "unlp-tp2.yaml")
        .read_text()
        .replace(
            "descripcion: Entregas de Taller de Proyecto II (UNLP)", "descripcion: Versión local"
        ),
    )

    profile = YamlProfileRepository([tmp_path, BUILTIN]).load("unlp-tp2")

    assert profile.description == "Versión local"


def test_parent_is_found_next_to_the_child(tmp_path: Path) -> None:
    write(
        tmp_path,
        "empresa-base",
        body=(BUILTIN / "informe-tecnico-es.yaml")
        .read_text()
        .replace("id: informe-tecnico-es", "id: empresa-base"),
    )
    child = write(
        tmp_path,
        "postmortem",
        body=CHILD.format(id="postmortem", extra="").replace("unlp-tp2@1", "empresa-base@1"),
    )

    assert YamlProfileRepository([BUILTIN]).load(str(child)).id == "postmortem"


def test_lists_override_parent_lists(tmp_path: Path, repo: YamlProfileRepository) -> None:
    write(tmp_path, "solo-arial", "layout:\n  fuentes: [Arial]")

    assert repo.load("solo-arial").layout.fonts == ("Arial",)


def test_severity_overrides(tmp_path: Path, repo: YamlProfileRepository) -> None:
    write(tmp_path, "laxo", "severidades:\n  LEN-01: info\n  FIG-07: revisar")

    profile = repo.load("laxo")

    assert profile.severity_overrides == {"LEN-01": Severity.INFO, "FIG-07": Severity.REVIEW}


def test_deep_merge() -> None:
    merged = deep_merge({"a": {"x": 1, "y": [1, 2]}, "b": 1}, {"a": {"y": [3]}, "c": 2})

    assert merged == {"a": {"x": 1, "y": [3]}, "b": 1, "c": 2}


# ---------- errores ----------


@pytest.mark.parametrize(
    ("setup", "reference", "message"),
    [
        (lambda _: None, "no-existe", "no existe el perfil 'no-existe'. Disponibles: "),
        (lambda _: None, "nada.yaml", "no existe el archivo de perfil"),
        (
            lambda d: write(d, "nombre", body=CHILD.format(id="otro", extra="")),
            "nombre",
            "no coincide con el nombre del archivo",
        ),
        (lambda d: write(d, "roto", body="id: [sin cerrar"), "roto", "no se pudo leer"),
        (lambda d: write(d, "lista", body="- a\n- b\n"), "lista", "mapa de claves"),
        (
            lambda d: write(d, "vers", body=CHILD.format(id="vers", extra="").replace("@1", "@2")),
            "vers",
            "está en la versión 1.0.0",
        ),
        (
            lambda d: write(d, "malo", "layout:\n  interlineado: '1,15'"),
            "malo",
            "layout.interlineado: valor no permitido",
        ),
        (lambda d: write(d, "tipeo", "layaut: {}"), "tipeo", "tiene un campo desconocido"),
        (
            lambda d: write(d, "regla", "severidades:\n  TIP-99: info"),
            "regla",
            "reglas que no existen: TIP-99",
        ),
    ],
)
def test_invalid_profiles(
    tmp_path: Path, repo: YamlProfileRepository, setup: object, reference: str, message: str
) -> None:
    setup(tmp_path)  # type: ignore[operator]

    with pytest.raises(ProfileError, match=re.escape(message)):
        repo.load(reference)


def test_circular_inheritance(tmp_path: Path, repo: YamlProfileRepository) -> None:
    write(tmp_path, "a", body=CHILD.format(id="a", extra="").replace("unlp-tp2@1", "b@1"))
    write(tmp_path, "b", body=CHILD.format(id="b", extra="").replace("unlp-tp2@1", "a@1"))

    with pytest.raises(ProfileError, match="herencia circular: a → b → a"):
        repo.load("a")


# ---------- plantilla ----------


def test_template_creates_a_valid_profile(tmp_path: Path, repo: YamlProfileRepository) -> None:
    (tmp_path / "mi-catedra.yaml").write_text(profile_template("mi-catedra"))

    profile = repo.load("mi-catedra")

    assert profile.id == "mi-catedra"
    assert profile.layout.fonts == ("Arial", "Times New Roman")


def test_builtin_dir_can_be_overridden(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(PROFILES_ENV_VAR, str(tmp_path))

    assert builtin_profiles_dir() == tmp_path


def test_caption_position_by_kind_and_cover_page(
    tmp_path: Path, repo: YamlProfileRepository
) -> None:
    write(
        tmp_path,
        "seminario",
        "layout:\n  epigrafes: { tablas: arriba }\nestructura:\n  caratula_pagina: 2",
    )

    profile = repo.load("seminario")

    assert profile.layout.table_captions is CaptionPosition.ABOVE
    assert profile.layout.figure_captions is CaptionPosition.BELOW
    assert profile.structure.cover_max_page == 2
    assert profile.structure.toc is Requirement.REQUIRED  # el resto de la estructura se hereda


def test_invalid_caption_position_object(tmp_path: Path, repo: YamlProfileRepository) -> None:
    write(tmp_path, "malo2", "layout:\n  epigrafes: { cuadros: arriba }")

    with pytest.raises(ProfileError, match=r"layout\.epigrafes"):
        repo.load("malo2")
