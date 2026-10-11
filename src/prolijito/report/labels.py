"""Textos compartidos por los reportes."""

from __future__ import annotations

from collections.abc import Mapping

from prolijito.domain import Category, CheckResult, Severity

ICONS: Mapping[Severity, str] = {
    Severity.ERROR: "❌",
    Severity.REVIEW: "❓",
    Severity.INFO: "ℹ️",  # noqa: RUF001 - es el ícono que se muestra
}

CATEGORY_TITLES: Mapping[Category, str] = {
    Category.TYPOGRAPHY: "Tipografía",
    Category.STRUCTURE: "Estructura",
    Category.HEADINGS: "Títulos e índice",
    Category.FIGURES: "Figuras y tablas",
    Category.LANGUAGE: "Lenguaje",
    Category.REFERENCES: "Referencias",
    Category.PRIVACY: "Privacidad",
}

TOOL_NAMES: Mapping[str, str] = {
    "general": "En general",
    "docs": "Google Docs",
    "word": "Word / LibreOffice",
    "latex": "LaTeX",
    "typst": "Typst",
}


def plural(n: int, singular: str, plural_form: str) -> str:
    return f"{n} {singular if n == 1 else plural_form}"


def status(result: CheckResult) -> str:
    errors = result.count(Severity.ERROR)
    review = plural(result.count(Severity.REVIEW), "punto a revisar", "puntos a revisar")
    if errors:
        return f"❌ con {plural(errors, 'error', 'errores')} y {review}"
    if result.count(Severity.REVIEW):
        return f"✅ sin errores · {review}"
    return "✅ listo para entregar"
