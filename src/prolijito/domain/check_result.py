"""Resultado de validar un documento contra un perfil."""

from __future__ import annotations

from dataclasses import dataclass

from prolijito.domain.profile import Profile
from prolijito.domain.violation import Severity, Violation


@dataclass(frozen=True, slots=True)
class CheckResult:
    document: str
    profile: Profile
    violations: tuple[Violation, ...]

    def with_severity(self, severity: Severity) -> tuple[Violation, ...]:
        return tuple(v for v in self.violations if v.severity is severity)

    def count(self, severity: Severity) -> int:
        return len(self.with_severity(severity))

    @property
    def has_errors(self) -> bool:
        return self.count(Severity.ERROR) > 0
