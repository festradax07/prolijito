import pytest

from prolijito.domain import CheckResult, Severity, Violation
from tests.builders import a_profile


@pytest.mark.parametrize(
    ("severities", "threshold", "fails"),
    [
        ((), Severity.ERROR, False),
        ((Severity.REVIEW,), Severity.ERROR, False),
        ((Severity.REVIEW,), Severity.REVIEW, True),
        ((Severity.INFO,), Severity.REVIEW, False),
        ((Severity.INFO,), Severity.INFO, True),
        ((Severity.ERROR,), None, False),
    ],
)
def test_check_result_fails_from_threshold(
    severities: tuple[Severity, ...], threshold: Severity | None, fails: bool
) -> None:
    result = CheckResult(
        "informe.pdf", a_profile(), tuple(Violation("LEN-01", s, "x") for s in severities)
    )

    assert result.fails(threshold) is fails
