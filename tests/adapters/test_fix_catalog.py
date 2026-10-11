import pytest

from prolijito.adapters.fix_catalog import YamlFixCatalog
from prolijito.application.errors import ProlijitoError
from prolijito.validate.rules import RULES


def test_every_rule_has_a_hint_and_nothing_else() -> None:
    fixes = YamlFixCatalog().how_to_fix()

    assert set(fixes) == set(RULES)
    assert all(hints for hints in fixes.values())


def test_only_known_tools_are_used() -> None:
    tools = {tool for hints in YamlFixCatalog().how_to_fix().values() for tool in hints}

    assert tools <= {"general", "docs", "word", "latex", "typst"}


def test_anchors_are_resolved_and_hidden() -> None:
    catalog = YamlFixCatalog("_base: &b\n  docs: hacer X\nTIP-01: *b\n")

    assert catalog.how_to_fix() == {"TIP-01": {"docs": "hacer X"}}


def test_invalid_catalog_is_rejected() -> None:
    with pytest.raises(ProlijitoError, match="mapa de reglas"):
        YamlFixCatalog("- solo\n- una lista\n").how_to_fix()
