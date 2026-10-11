"""Caso de uso: validar un documento contra un perfil."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from prolijito.application.ports import FixCatalog, Measurer, ProfileRepository
from prolijito.domain import CheckResult
from prolijito.validate import evaluate


@dataclass(frozen=True, slots=True)
class CheckDocument:
    measurer: Measurer
    profiles: ProfileRepository
    fixes: FixCatalog

    def __call__(self, document: Path, profile_reference: str) -> CheckResult:
        # El perfil va primero: si es inválido, se falla sin gastar tiempo midiendo.
        profile = self.profiles.load(profile_reference)
        measurements = self.measurer.measure(document)
        violations = evaluate(measurements, profile, self.fixes.how_to_fix())
        return CheckResult(document=str(document), profile=profile, violations=violations)
