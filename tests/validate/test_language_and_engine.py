import pytest

from prolijito.domain import LanguageFinding, Severity, Violation
from prolijito.validate import engine, evaluate
from prolijito.validate.rules import RETIRED, RULES
from tests.builders import a_document, a_profile

FINDINGS = (
    LanguageFinding(3, "voseo/tuteo", "podés", "…si podés…"),
    LanguageFinding(5, "verbo 1ª persona plural (candidato)", "tomamos", "…tomamos decisiones…"),
    LanguageFinding(7, "voseo/tuteo", "tenés", "…tenés que…"),
)


def test_len01_groups_findings_by_kind() -> None:
    violations = evaluate(a_document(language=FINDINGS), a_profile())

    by_message = {v.message: v for v in violations}
    voseo = by_message["Posible voseo/tuteo: podés, tenés."]
    assert voseo.severity is Severity.REVIEW
    assert [o.page for o in voseo.occurrences] == [3, 7]
    assert len(violations) == 2


def test_profile_severity_override_is_applied() -> None:
    profile = a_profile(severity_overrides={"LEN-01": Severity.INFO})

    violations = evaluate(a_document(language=FINDINGS[:1]), profile)

    assert [v.severity for v in violations] == [Severity.INFO]


def test_how_to_fix_is_attached_by_rule_id() -> None:
    fixes = {"LEN-01": {"docs": "Reescribir en impersonal"}}

    [violation] = evaluate(a_document(language=FINDINGS[:1]), a_profile(), fixes)

    assert violation.how_to_fix == {"docs": "Reescribir en impersonal"}


def test_unregistered_rule_is_a_bug(monkeypatch: pytest.MonkeyPatch) -> None:
    def rogue(*_: object) -> object:
        yield Violation("PRI-99", Severity.ERROR, "no registrada")

    monkeypatch.setattr(engine, "CHECKS", (rogue,))

    with pytest.raises(LookupError, match="PRI-99"):
        evaluate(a_document(), a_profile())


def test_registry_ids_are_well_formed_and_not_retired() -> None:
    for rule_id in RULES:
        Violation(rule_id, Severity.INFO, "ok")  # valida el formato
    assert not set(RULES) & RETIRED
