"""Datos de prueba: un documento y un perfil que cumplen todo, para cambiar de a una cosa."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from prolijito.domain import (
    FontUsage,
    Justification,
    JustificationState,
    Layout,
    LineSpacing,
    LineSpacingClass,
    Measurements,
    Profile,
    Requirement,
    Section,
    Structure,
    StructureRequirements,
    Typography,
)

PRESENT = Section(present=True, pages=(2,))
ABSENT = Section(present=False)


def a_layout(**changes: Any) -> Layout:
    layout = Layout(
        fonts=("Arial", "Times New Roman", "Libertinus"),
        equivalents=("Liberation Serif", "Liberation Sans"),
        body_size_pt=12.0,
        size_tolerance_pt=0.6,
        line_spacing=LineSpacingClass.ONE_AND_HALF,
        justified=True,
    )
    return replace(layout, **changes)


def a_profile(**changes: Any) -> Profile:
    profile = Profile(
        id="unlp-tp2",
        version="1.0.0",
        description="Entregas de prueba",
        layout=a_layout(),
        structure=StructureRequirements(
            cover=Requirement.REQUIRED,
            toc=Requirement.REQUIRED,
            figure_index=Requirement.IF_CONTENT,
            table_index=Requirement.IF_CONTENT,
            bibliography=Requirement.REQUIRED,
            appendix=Requirement.OPTIONAL,
        ),
    )
    return replace(profile, **changes)


def a_structure(**changes: Any) -> Structure:
    structure = Structure(
        cover_page=1,
        toc=PRESENT,
        figure_index=PRESENT,
        table_index=PRESENT,
        bibliography=PRESENT,
        appendix=PRESENT,
    )
    return replace(structure, **changes)


def a_document(**changes: Any) -> Measurements:
    measurements = Measurements(
        page_count=10,
        typography=Typography(body=FontUsage("Times New Roman", 12.0, 80.0)),
        line_spacing=LineSpacing(ratio=1.72, spacing_class=LineSpacingClass.ONE_AND_HALF),
        justification=Justification(state=JustificationState.YES, aligned_pct=90),
        structure=a_structure(),
    )
    return replace(measurements, **changes)
