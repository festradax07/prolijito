"""Anotaciones de GitHub Actions (`::error`, `::warning`, `::notice`).

El Markdown completo para el resumen del job lo escribe la CLI en `$GITHUB_STEP_SUMMARY`.
Formato: https://docs.github.com/actions/reference/workflow-commands-for-github-actions
"""

from __future__ import annotations

from prolijito.domain import CheckResult, Severity, Violation
from prolijito.report.labels import status
from prolijito.validate.rules import RULES

COMMANDS = {Severity.ERROR: "error", Severity.REVIEW: "warning", Severity.INFO: "notice"}


def render_github(result: CheckResult) -> str:
    lines = [_annotation(v, result.document) for v in result.violations]
    lines.append(
        f"prolijito: {result.document} — perfil {result.profile.reference} — {status(result)}"
    )
    return "\n".join(lines) + "\n"


def _annotation(v: Violation, document: str) -> str:
    title = f"{v.rule_id} {RULES[v.rule_id]}"
    page = f" (p. {v.page})" if v.page is not None else ""
    properties = f"file={_escape_property(document)},title={_escape_property(title)}"
    return f"::{COMMANDS[v.severity]} {properties}::{_escape_data(v.message + page)}"


def _escape_data(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _escape_property(text: str) -> str:
    return _escape_data(text).replace(":", "%3A").replace(",", "%2C")
