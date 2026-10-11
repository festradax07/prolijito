import pytest

from prolijito.domain import Category, Severity, Violation


@pytest.mark.parametrize(
    ("rule_id", "category"),
    [
        ("TIP-03", Category.TYPOGRAPHY),
        ("EST-01", Category.STRUCTURE),
        ("TIT-02", Category.HEADINGS),
        ("FIG-07", Category.FIGURES),
        ("LEN-01", Category.LANGUAGE),
        ("REF-01", Category.REFERENCES),
        ("PRI-01", Category.PRIVACY),
    ],
)
def test_category_comes_from_id_prefix(rule_id: str, category: Category) -> None:
    violation = Violation(rule_id, Severity.ERROR, "mensaje")

    assert violation.category is category


@pytest.mark.parametrize("rule_id", ["TIP-3", "tip-03", "XYZ-01", "TIP-003", ""])
def test_rejects_malformed_ids(rule_id: str) -> None:
    with pytest.raises(ValueError, match="ID de regla inválido"):
        Violation(rule_id, Severity.ERROR, "mensaje")


def test_with_severity_returns_a_new_violation() -> None:
    original = Violation("LEN-01", Severity.REVIEW, "mensaje", page=4)

    changed = original.with_severity(Severity.INFO)

    assert changed.severity is Severity.INFO
    assert original.severity is Severity.REVIEW
    assert changed.page == 4


def test_severity_values_match_the_contract() -> None:
    assert [s.value for s in Severity] == ["error", "revisar", "info"]
