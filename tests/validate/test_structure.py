import pytest

from prolijito.domain import (
    Caption,
    CaptionKind,
    Captions,
    Requirement,
    Severity,
    StructureRequirements,
)
from prolijito.validate import evaluate
from tests.builders import ABSENT, a_document, a_profile, a_structure

FIGURE = Caption(CaptionKind.FIGURE, 1, 3, "Figura 1", below=True, text_references=1, in_index=True)
TABLE = Caption(CaptionKind.TABLE, 1, 4, "Tabla 1", below=True, text_references=1, in_index=True)


def test_est01_first_page_is_not_a_cover() -> None:
    [violation] = evaluate(
        a_document(structure=a_structure(cover_on_first_page=False)), a_profile()
    )

    assert (violation.rule_id, violation.page) == ("EST-01", 1)


@pytest.mark.parametrize(("rule_id", "field"), [("EST-02", "toc"), ("EST-05", "bibliography")])
def test_required_section_missing(rule_id: str, field: str) -> None:
    doc = a_document(structure=a_structure(**{field: ABSENT}))

    [violation] = evaluate(doc, a_profile())

    assert (violation.rule_id, violation.severity) == (rule_id, Severity.ERROR)


@pytest.mark.parametrize(
    ("rule_id", "field", "captions"),
    [
        ("EST-03", "figure_index", Captions(items=(FIGURE,))),
        ("EST-04", "table_index", Captions(items=(TABLE,))),
    ],
)
def test_index_required_when_document_has_content(
    rule_id: str, field: str, captions: Captions
) -> None:
    doc = a_document(structure=a_structure(**{field: ABSENT}), captions=captions)

    assert [v.rule_id for v in evaluate(doc, a_profile())] == [rule_id]


def test_indexes_not_required_without_figures_or_tables() -> None:
    doc = a_document(structure=a_structure(figure_index=ABSENT, table_index=ABSENT))

    assert evaluate(doc, a_profile()) == ()


def test_est06_missing_optional_appendix_is_info() -> None:
    [violation] = evaluate(a_document(structure=a_structure(appendix=ABSENT)), a_profile())

    assert (violation.rule_id, violation.severity) == ("EST-06", Severity.INFO)


def test_not_required_section_is_silent() -> None:
    profile = a_profile(structure=StructureRequirements(*[Requirement.NOT_REQUIRED] * 6))
    doc = a_document(structure=a_structure(cover_on_first_page=False, toc=ABSENT, appendix=ABSENT))

    assert evaluate(doc, profile) == ()
