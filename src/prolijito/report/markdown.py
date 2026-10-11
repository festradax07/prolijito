"""Reporte en Markdown: para leer en la terminal, en un PR o en el resumen del job de GitHub."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from itertools import groupby
from pathlib import PurePath

from prolijito.domain import CheckResult, Severity, Violation
from prolijito.report.labels import CATEGORY_TITLES, ICONS, TOOL_NAMES, status
from prolijito.validate.rules import RULES

SECTION_TITLES = {
    Severity.ERROR: "Errores",
    Severity.REVIEW: "Para revisar",
    Severity.INFO: "Informativo",
}
_RULE_ORDER = {rule_id: i for i, rule_id in enumerate(RULES)}


def render_markdown(result: CheckResult) -> str:
    name = PurePath(result.document).name
    lines = [
        f"# Chequeo de formato — {name} — perfil {result.profile.reference}",
        "",
        f"**Estado:** {status(result)}",
        "",
    ]
    for severity in Severity:
        lines += _section(severity, result.with_severity(severity))
    lines += _criteria(result)
    return "\n".join(lines).rstrip() + "\n"


def _section(severity: Severity, violations: Sequence[Violation]) -> list[str]:
    if not violations:
        return []
    lines = [f"## {SECTION_TITLES[severity]} ({ICONS[severity]})", ""]
    ordered = sorted(violations, key=lambda v: _RULE_ORDER[v.rule_id])
    for category, in_category in groupby(ordered, key=lambda v: v.category):
        lines += [f"### {CATEGORY_TITLES[category]}", ""]
        for rule_id, group in groupby(in_category, key=lambda v: v.rule_id):
            lines += _rule(rule_id, tuple(group))
    return lines


def _rule(rule_id: str, violations: Sequence[Violation]) -> list[str]:
    count = f" ({len(violations)})" if len(violations) > 1 else ""
    lines = [f"**{rule_id} · {RULES[rule_id]}**{count}", ""]
    for v in violations:
        lines.append(f"- {_where(v.page)}{v.message}{_values(v)}")
        lines += [f"  - {_where(o.page)}«{o.text}»" for o in v.occurrences if o.text]
    lines += _how_to_fix(violations[0].how_to_fix.items())
    return [*lines, ""]


def _where(page: int | None) -> str:
    return f"p. {page} — " if page is not None else ""


def _values(v: Violation) -> str:
    parts = [f"esperado: {v.expected}"] if v.expected else []
    parts += [f"medido: {v.measured}"] if v.measured else []
    return f" ({' · '.join(parts)})" if parts else ""


def _how_to_fix(hints: Iterable[tuple[str, str]]) -> list[str]:
    lines = [f"  - **{TOOL_NAMES.get(tool, tool)}:** {text}" for tool, text in hints]
    return ["- Cómo arreglar:", *lines] if lines else []


def _criteria(result: CheckResult) -> list[str]:
    worst: dict[str, Severity] = {}
    for v in result.violations:
        current = worst.get(v.rule_id)
        if current is None or list(Severity).index(v.severity) < list(Severity).index(current):
            worst[v.rule_id] = v.severity
    rows = [
        f"| {rule_id} | {criterion} | {ICONS[worst[rule_id]] if rule_id in worst else '✅'} |"
        for rule_id, criterion in RULES.items()
    ]
    return ["## Detalle por criterio", "", "| ID | Criterio | Estado |", "|---|---|---|", *rows]
