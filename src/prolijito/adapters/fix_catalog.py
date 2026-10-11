"""Catálogo de «cómo arreglar» por regla, cargado de `fixes.yaml`."""

from __future__ import annotations

from collections.abc import Mapping
from functools import cached_property
from importlib import resources

import yaml

from prolijito.application.errors import ProlijitoError

Fixes = Mapping[str, Mapping[str, str]]


class YamlFixCatalog:
    def __init__(self, text: str | None = None) -> None:
        self._text = text

    def how_to_fix(self) -> Fixes:
        return self._fixes

    @cached_property
    def _fixes(self) -> Fixes:
        text = self._text or resources.files("prolijito.adapters").joinpath("fixes.yaml").read_text(
            "utf-8"
        )
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ProlijitoError("fixes.yaml tiene que ser un mapa de reglas.")
        # Las claves que empiezan con "_" son anclas YAML para reutilizar textos.
        return {
            rule_id: {tool: str(hint).strip() for tool, hint in hints.items()}
            for rule_id, hints in data.items()
            if not rule_id.startswith("_")
        }
