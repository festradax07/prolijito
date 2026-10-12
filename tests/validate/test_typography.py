import pytest

from prolijito.domain import (
    FontUsage,
    Justification,
    JustificationState,
    LineSpacing,
    LineSpacingClass,
    Severity,
    Typography,
    Unmeasured,
    Violation,
)
from prolijito.validate import evaluate
from tests.builders import a_document, a_layout, a_profile


def ids(violations: tuple[Violation, ...]) -> list[str]:
    return [v.rule_id for v in violations]


def test_compliant_document_has_no_typography_violations() -> None:
    assert not [i for i in ids(evaluate(a_document(), a_profile())) if i.startswith("TIP")]


@pytest.mark.parametrize("family", ["Calibri", "Comic Sans"])
def test_tip01_body_font_not_allowed(family: str) -> None:
    doc = a_document(typography=Typography(body=FontUsage(family, 12.0, 80.0)))

    [violation] = evaluate(doc, a_profile())

    assert violation.rule_id == "TIP-01"
    assert violation.measured == family


def test_tip01_accepts_equivalent_font() -> None:
    doc = a_document(typography=Typography(body=FontUsage("Liberation Serif", 12.0, 80.0)))

    assert evaluate(doc, a_profile()) == ()


def test_tip02_body_size_out_of_tolerance() -> None:
    doc = a_document(typography=Typography(body=FontUsage("Arial", 11.0, 80.0)))

    [violation] = evaluate(doc, a_profile())

    assert violation.rule_id == "TIP-02"
    assert violation.measured == "11 pt"


def test_tip03_single_spacing_is_an_error() -> None:
    doc = a_document(line_spacing=LineSpacing(1.33, LineSpacingClass.SINGLE))

    [violation] = evaluate(doc, a_profile())

    assert violation.rule_id == "TIP-03"
    assert violation.severity is Severity.ERROR
    assert violation.measured == "1,33 (simple)"


def test_tip03_reports_pages_with_another_spacing() -> None:
    one_half, single = LineSpacingClass.ONE_AND_HALF, LineSpacingClass.SINGLE
    spacing = LineSpacing(1.7, one_half, page_classes={3: one_half, 4: single, 7: single})

    [violation] = evaluate(a_document(line_spacing=spacing), a_profile())

    assert violation.page == 4
    assert [o.page for o in violation.occurrences] == [4, 7]


def test_tip03_compares_pages_against_the_profile_class() -> None:
    double = LineSpacingClass.DOUBLE
    spacing = LineSpacing(2.3, double, page_classes={3: double, 4: double})
    profile = a_profile(layout=a_layout(line_spacing=double))

    assert evaluate(a_document(line_spacing=spacing), profile) == ()


def test_tip03_unmeasured_needs_review() -> None:
    doc = a_document(line_spacing=Unmeasured("pocos párrafos"))

    [violation] = evaluate(doc, a_profile())

    assert violation.severity is Severity.REVIEW


@pytest.mark.parametrize(
    ("state", "severity"),
    [(JustificationState.NO, Severity.ERROR), (JustificationState.PARTIAL, Severity.REVIEW)],
)
def test_tip04_justification(state: JustificationState, severity: Severity) -> None:
    doc = a_document(justification=Justification(state, aligned_pct=40, doubtful_pages=(3,)))

    [violation] = evaluate(doc, a_profile())

    assert (violation.rule_id, violation.severity) == ("TIP-04", severity)


def test_tip04_unmeasured_needs_review() -> None:
    [violation] = evaluate(a_document(justification=Unmeasured("pocas líneas")), a_profile())

    assert (violation.rule_id, violation.severity) == ("TIP-04", Severity.REVIEW)


def test_tip04_skipped_when_profile_does_not_require_justification() -> None:
    doc = a_document(justification=Justification(JustificationState.NO, aligned_pct=10))
    profile = a_profile(layout=a_layout(justified=False))

    assert evaluate(doc, profile) == ()


def test_tip05_other_families_need_review() -> None:
    others = (FontUsage("CourierNew", 10.5, 2.0), FontUsage("Arial", 11.0, 9.0))
    doc = a_document(typography=Typography(FontUsage("Times New Roman", 12.0, 80.0), others))

    [violation] = evaluate(doc, a_profile())

    assert (violation.rule_id, violation.severity) == ("TIP-05", Severity.REVIEW)
    assert violation.measured == "CourierNew"
