"""Formato de valores para mensajes: coma decimal, como se escribe en español."""

from __future__ import annotations

from collections.abc import Iterable


def number(value: float) -> str:
    return f"{value:g}".replace(".", ",")


def pages(values: Iterable[int]) -> str:
    return ", ".join(str(v) for v in values)
