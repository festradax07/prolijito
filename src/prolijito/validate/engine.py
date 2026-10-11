"""Evalúa todas las reglas y aplica lo que define el perfil (severidades) y el catálogo de fixes."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import replace

from prolijito.domain import Measurements, Profile, Violation
from prolijito.validate.figures import check_figures
from prolijito.validate.headings import check_headings
from prolijito.validate.language import check_language
from prolijito.validate.rules import RULES
from prolijito.validate.structure import check_structure
from prolijito.validate.typography import check_typography

Check = Callable[[Measurements, Profile], Iterator[Violation]]

CHECKS: tuple[Check, ...] = (
    check_typography,
    check_structure,
    check_headings,
    check_figures,
    check_language,
)


def evaluate(
    measurements: Measurements,
    profile: Profile,
    how_to_fix: Mapping[str, Mapping[str, str]] | None = None,
) -> tuple[Violation, ...]:
    fixes = how_to_fix or {}
    violations = (v for check in CHECKS for v in check(measurements, profile))
    return tuple(_finish(v, profile, fixes) for v in violations)


def _finish(
    violation: Violation, profile: Profile, fixes: Mapping[str, Mapping[str, str]]
) -> Violation:
    if violation.rule_id not in RULES:
        raise LookupError(f"Regla sin registrar en rules.py: {violation.rule_id}")
    return replace(
        violation,
        severity=profile.severity_for(violation.rule_id, violation.severity),
        how_to_fix=fixes.get(violation.rule_id, {}),
    )
