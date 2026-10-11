"""Reglas EST: secciones obligatorias del documento."""

from __future__ import annotations

from collections.abc import Iterator

from prolijito.domain import Measurements, Profile, Requirement, Section, Severity, Violation


def check_structure(m: Measurements, p: Profile) -> Iterator[Violation]:
    s, req = m.structure, p.structure
    if req.cover.is_required() and not s.cover_on_first_page:
        yield Violation(
            "EST-01",
            Severity.ERROR,
            "La página 1 no parece una carátula (tiene demasiado texto).",
            page=1,
            expected="carátula sola en la página 1",
        )
    yield from _section("EST-02", "el índice general", req.toc, s.toc)
    yield from _section(
        "EST-03",
        "el índice de figuras",
        req.figure_index,
        s.figure_index,
        has_content=m.captions.has_figures,
    )
    yield from _section(
        "EST-04",
        "el índice de tablas",
        req.table_index,
        s.table_index,
        has_content=m.captions.has_tables,
    )
    yield from _section("EST-05", "la bibliografía", req.bibliography, s.bibliography)
    yield from _section("EST-06", "anexo", req.appendix, s.appendix)


def _section(
    rule_id: str,
    name: str,
    requirement: Requirement,
    section: Section,
    *,
    has_content: bool = True,
) -> Iterator[Violation]:
    if section.present:
        return
    if requirement.is_required(has_content=has_content):
        yield Violation(rule_id, Severity.ERROR, f"Falta {name}.", expected="presente")
    elif requirement is Requirement.OPTIONAL:
        yield Violation(rule_id, Severity.INFO, f"No hay {name} (es opcional).")
