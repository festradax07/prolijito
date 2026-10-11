from prolijito.domain import Caption, CaptionKind, Captions


def caption(kind: CaptionKind, number: int = 1) -> Caption:
    return Caption(
        kind, number, page=3, text=f"{kind} {number}", below=True, text_references=1, in_index=True
    )


def test_empty_document_has_no_figures_or_tables() -> None:
    captions = Captions()

    assert not captions.has_figures
    assert not captions.has_tables


def test_figures_detected_by_caption_or_by_image() -> None:
    assert Captions(items=(caption(CaptionKind.FIGURE),)).has_figures
    assert Captions(images_per_page={4: 1}).has_figures


def test_tables_detected_by_caption_or_by_geometry() -> None:
    assert Captions(items=(caption(CaptionKind.TABLE),)).has_tables
    assert Captions(detected_tables=2).has_tables


def test_of_kind_filters_captions() -> None:
    figure, table = caption(CaptionKind.FIGURE), caption(CaptionKind.TABLE)
    captions = Captions(items=(figure, table))

    assert captions.of_kind(CaptionKind.TABLE) == (table,)
