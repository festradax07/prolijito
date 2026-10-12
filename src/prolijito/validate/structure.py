"""Reglas EST: secciones obligatorias del documento."""

from __future__ import annotations

from collections.abc import Iterator

from prolijito.domain import Measurements, Profile, Requirement, Section, Severity, Violation


def check_structure(m: Measurements, p: Profile) -> Iterator[Violation]:
    s, req = m.structure, p.structure
    yield from _cover(s.cover_page, req.cover, req.cover_max_page)
    yield from _section("EST-02", ("el", "índice general"), req.toc, s.toc)
    yield from _section(
        "EST-03",
        ("el", "índice de figuras"),
        req.figure_index,
        s.figure_index,
        has_content=m.captions.has_figures,
    )
    yield from _section(
        "EST-04",
        ("el", "índice de tablas"),
        req.table_index,
        s.table_index,
        has_content=m.captions.has_tables,
    )
    yield from _section("EST-05", ("la", "bibliografía"), req.bibliography, s.bibliography)
    yield from _section("EST-06", ("el", "anexo"), req.appendix, s.appendix)


def _cover(cover_page: int | None, requirement: Requirement, max_page: int) -> Iterator[Violation]:
    if not requirement.is_required():
        return
    expected = (
        "carátula sola en la página 1" if max_page == 1 else f"carátula hasta la página {max_page}"
    )
    if cover_page is None:
        yield Violation(
            "EST-01",
            Severity.ERROR,
            "No se encontró una carátula: ninguna página antes del índice tiene poco texto.",
            page=1,
            expected=expected,
        )
    elif cover_page > max_page:
        yield Violation(
            "EST-01",
            Severity.ERROR,
            f"La carátula está en la página {cover_page}.",
            page=cover_page,
            expected=expected,
            measured=f"página {cover_page}",
        )


def _section(
    rule_id: str,
    what: tuple[str, str],
    requirement: Requirement,
    section: Section,
    *,
    has_content: bool = True,
) -> Iterator[Violation]:
    """`what`: artículo y nombre, para «Falta la bibliografía» y «No hay anexo (es opcional)»."""
    if section.present:
        return
    article, name = what
    if requirement.is_required(has_content=has_content):
        yield Violation(rule_id, Severity.ERROR, f"Falta {article} {name}.")
    elif requirement is Requirement.OPTIONAL:
        yield Violation(rule_id, Severity.INFO, f"No hay {name} (es opcional).")
