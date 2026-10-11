from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from prolijito.application.check import CheckDocument
from prolijito.application.errors import ProfileError
from prolijito.application.ports import ProfileSummary
from prolijito.domain import LineSpacing, LineSpacingClass, Measurements, Profile, Severity
from tests.builders import a_document, a_profile


@dataclass
class FakeMeasurer:
    result: Measurements
    calls: list[Path] = field(default_factory=list)

    def measure(self, document: Path) -> Measurements:
        self.calls.append(document)
        return self.result


@dataclass
class FakeProfiles:
    profile: Profile | None

    def load(self, reference: str) -> Profile:
        if self.profile is None:
            raise ProfileError(f"no existe el perfil '{reference}'")
        return self.profile

    def available(self) -> tuple[ProfileSummary, ...]:
        return ()


class FakeFixes:
    def how_to_fix(self) -> Mapping[str, Mapping[str, str]]:
        return {"TIP-03": {"typst": "#set par(leading: 1.5em)"}}


def test_compliant_document_has_no_errors() -> None:
    check = CheckDocument(FakeMeasurer(a_document()), FakeProfiles(a_profile()), FakeFixes())

    result = check(Path("informe.pdf"), "unlp-tp2")

    assert result.document == "informe.pdf"
    assert result.profile.reference == "unlp-tp2@1.0.0"
    assert not result.has_errors


def test_violations_carry_how_to_fix() -> None:
    single = a_document(line_spacing=LineSpacing(1.33, LineSpacingClass.SINGLE))
    check = CheckDocument(FakeMeasurer(single), FakeProfiles(a_profile()), FakeFixes())

    result = check(Path("informe.pdf"), "unlp-tp2")

    assert result.has_errors
    assert result.count(Severity.ERROR) == 1
    assert result.violations[0].how_to_fix == {"typst": "#set par(leading: 1.5em)"}


def test_invalid_profile_fails_before_measuring() -> None:
    measurer = FakeMeasurer(a_document())
    check = CheckDocument(measurer, FakeProfiles(None), FakeFixes())

    with pytest.raises(ProfileError):
        check(Path("informe.pdf"), "no-existe")
    assert measurer.calls == []
