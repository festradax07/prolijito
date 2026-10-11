import pytest

from prolijito.domain import (
    Layout,
    LineSpacingClass,
    Profile,
    Requirement,
    Severity,
    StructureRequirements,
)


def make_layout() -> Layout:
    return Layout(
        fonts=("Arial", "Times New Roman"),
        equivalents=("Liberation Serif",),
        body_size_pt=12.0,
        size_tolerance_pt=0.6,
        line_spacing=LineSpacingClass.ONE_AND_HALF,
        justified=True,
    )


def make_profile(profile_id: str = "unlp-tp2", **overrides: Severity) -> Profile:
    required = Requirement.REQUIRED
    return Profile(
        id=profile_id,
        version="1.0.0",
        description="Entregas de TP2",
        layout=make_layout(),
        structure=StructureRequirements(
            required,
            required,
            Requirement.IF_CONTENT,
            Requirement.IF_CONTENT,
            required,
            Requirement.OPTIONAL,
        ),
        severity_overrides=overrides,
    )


@pytest.mark.parametrize("family", ["Arial", "times new roman", "Liberation Serif"])
def test_allows_listed_fonts_and_equivalents(family: str) -> None:
    assert make_layout().allows_font(family)


def test_rejects_unlisted_font() -> None:
    assert not make_layout().allows_font("Calibri")


@pytest.mark.parametrize(("size", "ok"), [(12.0, True), (11.4, True), (12.6, True), (11.0, False)])
def test_size_tolerance(size: float, ok: bool) -> None:
    assert make_layout().size_within_tolerance(size) is ok


@pytest.mark.parametrize(
    ("requirement", "has_content", "required"),
    [
        (Requirement.REQUIRED, False, True),
        (Requirement.NOT_REQUIRED, True, False),
        (Requirement.OPTIONAL, True, False),
        (Requirement.IF_CONTENT, True, True),
        (Requirement.IF_CONTENT, False, False),
    ],
)
def test_requirement(requirement: Requirement, has_content: bool, required: bool) -> None:
    assert requirement.is_required(has_content=has_content) is required


def test_severity_override_wins_over_default() -> None:
    profile = make_profile(**{"LEN-01": Severity.INFO})

    assert profile.severity_for("LEN-01", Severity.REVIEW) is Severity.INFO
    assert profile.severity_for("TIP-03", Severity.ERROR) is Severity.ERROR


def test_reference_includes_version() -> None:
    assert make_profile().reference == "unlp-tp2@1.0.0"


@pytest.mark.parametrize("profile_id", ["UNLP-TP2", "unlp_tp2", "-unlp", "unlp--tp2"])
def test_rejects_non_kebab_case_ids(profile_id: str) -> None:
    with pytest.raises(ValueError, match="kebab-case"):
        make_profile(profile_id)
