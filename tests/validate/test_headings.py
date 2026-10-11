from prolijito.domain import Heading, PageMismatch, Severity, TocCheck, TocEntry
from prolijito.validate import evaluate
from tests.builders import a_document, a_profile, a_structure


def with_toc_check(check: TocCheck) -> list[tuple[str, Severity, int | None]]:
    doc = a_document(structure=a_structure(toc_check=check))
    return [(v.rule_id, v.severity, v.page) for v in evaluate(doc, a_profile())]


def test_consistent_toc_is_silent() -> None:
    assert with_toc_check(TocCheck()) == []


def test_tit01_entry_without_heading() -> None:
    check = TocCheck(entries_without_heading=(TocEntry("3. Resultados", 8),))

    assert with_toc_check(check) == [("TIT-01", Severity.ERROR, None)]


def test_tit02_page_mismatch_points_to_actual_page() -> None:
    check = TocCheck(page_mismatches=(PageMismatch("4. Grado de avance", 6, (7,)),))

    assert with_toc_check(check) == [("TIT-02", Severity.ERROR, 7)]


def test_tit03_heading_without_entry_needs_review() -> None:
    check = TocCheck(headings_without_entry=(Heading(5, "Anexo técnico"),))

    assert with_toc_check(check) == [("TIT-03", Severity.REVIEW, 5)]
