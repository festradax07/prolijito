"""Reporte JSON para otras herramientas. Los campos siguen el contrato de violación."""

from __future__ import annotations

import json
from typing import Any

from prolijito import __version__
from prolijito.domain import CheckResult, Severity, Violation


def render_json(result: CheckResult) -> str:
    payload = {
        "prolijito": __version__,
        "documento": result.document,
        "perfil": result.profile.reference,
        "estado": "con_errores" if result.has_errors else "sin_errores",
        "resumen": {severity.value: result.count(severity) for severity in Severity},
        "violaciones": [_violation(v) for v in result.violations],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _violation(v: Violation) -> dict[str, Any]:
    return {
        "id": v.rule_id,
        "severidad": v.severity.value,
        "categoria": v.category.value,
        "pagina": v.page,
        "esperado": v.expected,
        "medido": v.measured,
        "mensaje": v.message,
        "como_arreglar": dict(v.how_to_fix),
        "autofixable": v.autofixable,
        "ocurrencias": [{"pagina": o.page, "texto": o.text} for o in v.occurrences],
    }
