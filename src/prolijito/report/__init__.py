"""Renderizado de reportes: markdown, json y anotaciones de GitHub."""

from collections.abc import Callable, Mapping

from prolijito.domain import CheckResult
from prolijito.report.github import render_github
from prolijito.report.json_report import render_json
from prolijito.report.markdown import render_markdown

Renderer = Callable[[CheckResult], str]

RENDERERS: Mapping[str, Renderer] = {
    "md": render_markdown,
    "json": render_json,
    "github": render_github,
}

__all__ = ["RENDERERS", "Renderer", "render_github", "render_json", "render_markdown"]
