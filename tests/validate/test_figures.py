import pytest

from prolijito.domain import (
    Caption,
    CaptionKind,
    CaptionPosition,
    Captions,
    PageLocation,
    Severity,
)
from prolijito.validate import evaluate
from tests.builders import ABSENT, a_document, a_layout, a_profile, a_structure


def caption(**changes: object) -> Caption:
    base = {
        "kind": CaptionKind.FIGURE,
        "number": 1,
        "page": 3,
        "text": "Figura 1",
        "below": True,
        "text_references": 1,
        "in_index": True,
    }
    return Caption(**{**base, **changes})  # type: ignore[arg-type]


def found(captions: Captions, **profile_changes: object) -> list[tuple[str, Severity]]:
    doc = a_document(captions=captions)
    return [(v.rule_id, v.severity) for v in evaluate(doc, a_profile(**profile_changes))]


def test_well_formed_captions_are_silent() -> None:
    assert found(Captions(items=(caption(), caption(kind=CaptionKind.TABLE)))) == []


@pytest.mark.parametrize(
    ("captions", "rule_id"),
    [
        (Captions(figures_consecutive=False), "FIG-01"),
        (Captions(tables_consecutive=False), "FIG-02"),
    ],
)
def test_numbering_not_consecutive(captions: Captions, rule_id: str) -> None:
    assert found(captions) == [(rule_id, Severity.ERROR)]


def test_fig03_caption_above_when_below_is_expected() -> None:
    assert found(Captions(items=(caption(below=False),))) == [("FIG-03", Severity.ERROR)]


def test_fig03_caption_below_when_above_is_expected() -> None:
    profile_layout = a_layout(figure_captions=CaptionPosition.ABOVE)

    assert found(Captions(items=(caption(),)), layout=profile_layout) == [
        ("FIG-03", Severity.ERROR)
    ]


def test_fig03_position_by_kind() -> None:
    """Estilo APA: tablas con el epígrafe arriba, figuras debajo."""
    apa = a_layout(table_captions=CaptionPosition.ABOVE)
    table_above = caption(kind=CaptionKind.TABLE, below=False)

    assert found(Captions(items=(caption(), table_above)), layout=apa) == []


def test_appendix_label_in_messages() -> None:
    doc = a_document(captions=Captions(items=(caption(prefix="A", text_references=0),)))

    [violation] = evaluate(doc, a_profile())

    assert violation.message == "La Figura A1 no se menciona en el texto."


def test_fig03_unknown_position_needs_review() -> None:
    assert found(Captions(items=(caption(below=None),))) == [("FIG-03", Severity.REVIEW)]


def test_fig04_not_referenced_from_text() -> None:
    assert found(Captions(items=(caption(text_references=0),))) == [("FIG-04", Severity.ERROR)]


def test_fig05_missing_from_existing_index() -> None:
    assert found(Captions(items=(caption(in_index=False),))) == [("FIG-05", Severity.ERROR)]


def test_fig05_not_repeated_when_the_index_is_missing() -> None:
    doc = a_document(
        captions=Captions(items=(caption(in_index=False),)),
        structure=a_structure(figure_index=ABSENT),
    )

    assert [v.rule_id for v in evaluate(doc, a_profile())] == ["EST-03"]


def test_fig06_large_image_without_caption_needs_review() -> None:
    images = Captions(uncaptioned_images=(PageLocation(4, 100.0),))

    assert found(images) == [("FIG-06", Severity.REVIEW)]


def test_fig07_table_without_caption() -> None:
    tables = Captions(uncaptioned_tables=(PageLocation(4, 100.0),))

    assert found(tables) == [("FIG-07", Severity.ERROR)]
