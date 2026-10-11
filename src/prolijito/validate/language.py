"""Regla LEN-01: candidatos de primera o segunda persona y voseo. Siempre a revisar."""

from __future__ import annotations

from collections.abc import Iterator
from itertools import groupby

from prolijito.domain import LanguageFinding, Measurements, Occurrence, Profile, Severity, Violation


def check_language(m: Measurements, _: Profile) -> Iterator[Violation]:
    def kind(finding: LanguageFinding) -> str:
        return finding.kind

    for finding_kind, group in groupby(sorted(m.language, key=kind), key=kind):
        findings = tuple(group)
        words = ", ".join(sorted({f.word for f in findings}))
        yield Violation(
            "LEN-01",
            Severity.REVIEW,
            f"Posible {finding_kind}: {words}.",
            page=findings[0].page,
            expected="impersonal o tercera persona",
            occurrences=tuple(Occurrence(f.page, f.context) for f in findings),
        )
