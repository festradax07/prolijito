"""Resultado de validar un documento contra un perfil."""

from __future__ import annotations

from dataclasses import dataclass

from prolijito.domain.profile import Profile
from prolijito.domain.violation import Severity, Violation


@dataclass(frozen=True, slots=True)
class CheckResult:
    document: str
    """Ruta del documento tal como se indicó (las anotaciones de GitHub la necesitan)."""
    profile: Profile
    violations: tuple[Violation, ...]

    def with_severity(self, severity: Severity) -> tuple[Violation, ...]:
        return tuple(v for v in self.violations if v.severity is severity)

    def count(self, severity: Severity) -> int:
        return len(self.with_severity(severity))

    @property
    def has_errors(self) -> bool:
        return self.count(Severity.ERROR) > 0

    def fails(self, threshold: Severity | None) -> bool:
        """¿Hay violaciones de severidad `threshold` o más grave? `None`: nunca falla."""
        if threshold is None:
            return False
        blocking = list(Severity)[: list(Severity).index(threshold) + 1]
        return any(self.count(severity) for severity in blocking)
