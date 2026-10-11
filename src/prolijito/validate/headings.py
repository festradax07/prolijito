"""Reglas TIT: concordancia entre el índice y los títulos del cuerpo."""

from __future__ import annotations

from collections.abc import Iterator

from prolijito.domain import Measurements, Profile, Severity, Violation
from prolijito.validate._format import pages


def check_headings(m: Measurements, _: Profile) -> Iterator[Violation]:
    toc = m.structure.toc_check
    for entry in toc.entries_without_heading:
        yield Violation(
            "TIT-01",
            Severity.ERROR,
            f"La entrada del índice «{entry.title}» no tiene un título en el cuerpo.",
            expected=f"título en p. {entry.declared_page}",
            measured="no encontrado",
            autofixable=True,
        )
    for mismatch in toc.page_mismatches:
        yield Violation(
            "TIT-02",
            Severity.ERROR,
            f"El índice dice que «{mismatch.title}» está en la p. {mismatch.declared_page}.",
            page=mismatch.actual_pages[0] if mismatch.actual_pages else None,
            expected=f"p. {mismatch.declared_page}",
            measured=f"p. {pages(mismatch.actual_pages)}",
            autofixable=True,
        )
    for heading in toc.headings_without_entry:
        yield Violation(
            "TIT-03",
            Severity.REVIEW,
            f"El título «{heading.text}» no aparece en el índice.",
            page=heading.page,
        )
