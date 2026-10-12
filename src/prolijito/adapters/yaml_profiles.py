"""Perfiles en YAML: búsqueda por ID o ruta, herencia (`extends`), esquema y traducción al dominio.

Ver ADR 0003. El ID de un perfil es el nombre de su archivo: `unlp-tp2` vive en `unlp-tp2.yaml`.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from importlib import resources
from pathlib import Path
from string import Template
from typing import Any

import yaml
from jsonschema import Draft202012Validator, ValidationError

from prolijito.application.errors import ProfileError
from prolijito.application.ports import ProfileSummary
from prolijito.domain import (
    CaptionPosition,
    Layout,
    LineSpacingClass,
    Profile,
    Requirement,
    Severity,
    StructureRequirements,
)
from prolijito.validate.rules import RULES

Raw = dict[str, Any]

PROFILES_ENV_VAR = "PROLIJITO_PROFILES_DIR"
SUFFIXES = (".yaml", ".yml")

_REQUIREMENTS: Mapping[object, Requirement] = {
    True: Requirement.REQUIRED,
    False: Requirement.NOT_REQUIRED,
    "opcional": Requirement.OPTIONAL,
    "si_hay_figuras": Requirement.IF_CONTENT,
    "si_hay_tablas": Requirement.IF_CONTENT,
}


def builtin_profiles_dir() -> Path:
    """`$PROLIJITO_PROFILES_DIR` o, en una copia del repo, `profiles/` en la raíz."""
    if env := os.environ.get(PROFILES_ENV_VAR):
        return Path(env)
    return Path(__file__).resolve().parents[3] / "profiles"


def profile_template(profile_id: str) -> str:
    """Plantilla comentada para crear un perfil propio."""
    text = (
        resources.files("prolijito.adapters").joinpath("profile_template.yaml").read_text("utf-8")
    )
    return Template(text).substitute(id=profile_id)


class YamlProfileRepository:
    def __init__(self, search_dirs: Sequence[Path]) -> None:
        """`search_dirs` por prioridad: un ID se resuelve en la primera carpeta que lo tenga."""
        self._dirs = tuple(search_dirs)
        self._validator = Draft202012Validator(_schema())

    def load(self, reference: str) -> Profile:
        path = Path(reference)
        if path.suffix in SUFFIXES:
            if not path.is_file():
                raise ProfileError(f"no existe el archivo de perfil '{path}'.")
            raw = self._resolve_file(path, chain=())
        else:
            raw = self._resolve_id(reference, chain=(), extra_dirs=())
        self._validate(raw, reference)
        return _to_profile(raw)

    def available(self) -> tuple[ProfileSummary, ...]:
        found: dict[str, ProfileSummary] = {}
        for directory in self._dirs:
            for path in sorted(directory.glob("*.y*ml")) if directory.is_dir() else ():
                if path.stem not in found and path.suffix in SUFFIXES:
                    raw = _read(path)
                    found[path.stem] = ProfileSummary(
                        id=path.stem,
                        version=str(raw.get("version", "?")),
                        description=str(raw.get("descripcion", "")),
                        path=path,
                    )
        return tuple(found.values())

    # ---------- resolución y herencia ----------

    def _resolve_id(
        self, profile_id: str, chain: tuple[str, ...], extra_dirs: Sequence[Path]
    ) -> Raw:
        for directory in (*extra_dirs, *self._dirs):
            for suffix in SUFFIXES:
                path = directory / f"{profile_id}{suffix}"
                if path.is_file():
                    return self._resolve_file(path, chain)
        known = ", ".join(s.id for s in self.available()) or "ninguno"
        raise ProfileError(f"no existe el perfil '{profile_id}'. Disponibles: {known}.")

    def _resolve_file(self, path: Path, chain: tuple[str, ...]) -> Raw:
        raw = _read(path)
        profile_id = raw.get("id")
        if profile_id != path.stem:
            raise ProfileError(
                f"el id del perfil ({profile_id!r}) no coincide con el nombre del archivo "
                f"'{path.name}'. Usar `id: {path.stem}` o renombrar el archivo."
            )
        if path.stem in chain:
            raise ProfileError(f"herencia circular: {' → '.join((*chain, path.stem))}.")
        parent_ref = raw.pop("extends", None)
        if parent_ref is None:
            return raw
        parent_id, _, major = str(parent_ref).partition("@")
        parent = self._resolve_id(parent_id, (*chain, path.stem), extra_dirs=(path.parent,))
        if str(parent.get("version", "")).split(".")[0] != major:
            raise ProfileError(
                f"'{path.name}' extiende {parent_ref}, pero '{parent_id}' está en la versión "
                f"{parent.get('version')}."
            )
        return deep_merge(parent, raw)

    # ---------- validación ----------

    def _validate(self, raw: Raw, reference: str) -> None:
        errors = sorted(self._validator.iter_errors(raw), key=lambda e: list(e.absolute_path))
        if errors:
            detail = "; ".join(_describe(e) for e in errors[:5])
            raise ProfileError(f"el perfil '{reference}' no es válido: {detail}.")
        unknown = sorted(set(raw.get("severidades", {})) - set(RULES))
        if unknown:
            raise ProfileError(
                f"el perfil '{reference}' cambia la severidad de reglas que no existen: "
                f"{', '.join(unknown)}."
            )


def deep_merge(base: Raw, override: Raw) -> Raw:
    """Mezcla recursiva: los diccionarios se combinan; listas y valores del hijo reemplazan."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _read(path: Path) -> Raw:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ProfileError(f"no se pudo leer el perfil '{path}': {error}") from error
    if not isinstance(data, dict):
        raise ProfileError(f"el perfil '{path}' tiene que ser un mapa de claves YAML.")
    return data


def _schema() -> Raw:
    text = resources.files("prolijito.adapters").joinpath("profile.schema.json").read_text("utf-8")
    schema: Raw = json.loads(text)
    return schema


def _describe(error: ValidationError) -> str:
    location = ".".join(str(p) for p in error.absolute_path) or "(raíz)"
    messages = {
        "required": "falta un campo obligatorio",
        "additionalProperties": "tiene un campo desconocido",
        "enum": f"valor no permitido (opciones: {error.validator_value})",
        "type": f"tipo incorrecto (se esperaba {error.validator_value})",
        "pattern": "formato incorrecto",
    }
    message = messages.get(str(error.validator), error.message)
    return f"{location}: {message} ({error.message})"


# ---------- traducción al dominio ----------


def _to_profile(raw: Raw) -> Profile:
    layout, structure = raw["layout"], raw["estructura"]
    return Profile(
        id=raw["id"],
        version=raw["version"],
        description=raw["descripcion"],
        layout=Layout(
            fonts=tuple(layout["fuentes"]),
            equivalents=tuple(layout.get("equivalentes", ())),
            body_size_pt=float(layout["tamano_cuerpo_pt"]),
            size_tolerance_pt=float(layout["tolerancia_tamano_pt"]),
            line_spacing=LineSpacingClass(layout["interlineado"]),
            justified=bool(layout["justificado"]),
            figure_captions=_caption_position(layout, "figuras"),
            table_captions=_caption_position(layout, "tablas"),
        ),
        structure=StructureRequirements(
            cover=_REQUIREMENTS[structure["caratula"]],
            toc=_REQUIREMENTS[structure["indice"]],
            figure_index=_REQUIREMENTS[structure["indice_figuras"]],
            table_index=_REQUIREMENTS[structure["indice_tablas"]],
            bibliography=_REQUIREMENTS[structure["bibliografia"]],
            appendix=_REQUIREMENTS[structure["anexo"]],
            cover_max_page=int(structure.get("caratula_pagina", 1)),
        ),
        severity_overrides={k: Severity(v) for k, v in raw.get("severidades", {}).items()},
        norm_source=raw.get("fuente_norma"),
    )


def _caption_position(layout: Raw, kind: str) -> CaptionPosition:
    """`epigrafes: debajo` vale para todo; `epigrafes: {tablas: arriba}` distingue por tipo."""
    value = layout.get("epigrafes", "debajo")
    if isinstance(value, dict):
        value = value.get(kind, "debajo")
    return CaptionPosition(value)
