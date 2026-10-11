"""Reglas TIP: fuente, tamaño, interlineado y justificado del cuerpo."""

from __future__ import annotations

from collections.abc import Iterator

from prolijito.domain import (
    JustificationState,
    Measurements,
    Occurrence,
    Profile,
    Severity,
    Unmeasured,
    Violation,
)
from prolijito.validate._format import number, pages


def check_typography(m: Measurements, p: Profile) -> Iterator[Violation]:
    yield from _body_font(m, p)
    yield from _body_size(m, p)
    yield from _line_spacing(m, p)
    yield from _justification(m, p)
    yield from _other_families(m, p)


def _body_font(m: Measurements, p: Profile) -> Iterator[Violation]:
    family = m.typography.body.family
    if not p.layout.allows_font(family):
        yield Violation(
            "TIP-01",
            Severity.ERROR,
            f"La fuente del cuerpo ({family}) no está permitida.",
            expected=", ".join(p.layout.fonts),
            measured=family,
            autofixable=True,
        )


def _body_size(m: Measurements, p: Profile) -> Iterator[Violation]:
    size = m.typography.body.size_pt
    if not p.layout.size_within_tolerance(size):
        yield Violation(
            "TIP-02",
            Severity.ERROR,
            f"El tamaño del cuerpo es {number(size)} pt.",
            expected=f"{number(p.layout.body_size_pt)} pt",
            measured=f"{number(size)} pt",
            autofixable=True,
        )


def _line_spacing(m: Measurements, p: Profile) -> Iterator[Violation]:
    spacing, expected = m.line_spacing, p.layout.line_spacing
    if isinstance(spacing, Unmeasured):
        yield Violation(
            "TIP-03", Severity.REVIEW, f"No se pudo medir el interlineado: {spacing.reason}."
        )
        return
    measured = f"{number(spacing.ratio)} ({spacing.spacing_class})"
    if spacing.spacing_class is not expected:
        yield Violation(
            "TIP-03",
            Severity.ERROR,
            f"El interlineado del cuerpo es {spacing.spacing_class}.",
            expected=expected.value,
            measured=measured,
            autofixable=True,
        )
    elif spacing.deviant_pages and spacing.deviant_from is expected:
        yield Violation(
            "TIP-03",
            Severity.ERROR,
            f"Hay páginas con otro interlineado: {pages(spacing.deviant_pages)}.",
            page=spacing.deviant_pages[0],
            expected=expected.value,
            measured=measured,
            autofixable=True,
            occurrences=tuple(Occurrence(n, "") for n in spacing.deviant_pages),
        )


def _justification(m: Measurements, p: Profile) -> Iterator[Violation]:
    justification = m.justification
    if not p.layout.justified:
        return
    if isinstance(justification, Unmeasured):
        yield Violation(
            "TIP-04", Severity.REVIEW, f"No se pudo medir el justificado: {justification.reason}."
        )
        return
    measured = f"{justification.aligned_pct} % de líneas alineadas al margen derecho"
    if justification.state is JustificationState.NO:
        yield Violation(
            "TIP-04",
            Severity.ERROR,
            "El cuerpo no está justificado.",
            expected="justificado",
            measured=measured,
            autofixable=True,
        )
    elif justification.state is JustificationState.PARTIAL:
        doubtful = justification.doubtful_pages
        yield Violation(
            "TIP-04",
            Severity.REVIEW,
            "El cuerpo parece justificado solo en parte.",
            page=doubtful[0] if doubtful else None,
            expected="justificado",
            measured=measured,
            occurrences=tuple(Occurrence(n, "") for n in doubtful),
        )


def _other_families(m: Measurements, p: Profile) -> Iterator[Violation]:
    families = sorted({f.family for f in m.typography.others if not p.layout.allows_font(f.family)})
    if families:
        yield Violation(
            "TIP-05",
            Severity.REVIEW,
            f"Se usan otras familias tipográficas: {', '.join(families)}. "
            "En código o tablas puede estar bien.",
            expected=", ".join(p.layout.fonts),
            measured=", ".join(families),
        )
