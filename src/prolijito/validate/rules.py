"""Registro central de reglas. Los IDs son estables para siempre: uno retirado no se reutiliza."""

from __future__ import annotations

from collections.abc import Mapping

RULES: Mapping[str, str] = {
    "TIP-01": "Fuente del cuerpo permitida",
    "TIP-02": "Tamaño del cuerpo",
    "TIP-03": "Interlineado",
    "TIP-04": "Texto justificado",
    "TIP-05": "Otras familias tipográficas permitidas",
    "EST-01": "Carátula en la página 1",
    "EST-02": "Índice general",
    "EST-03": "Índice de figuras",
    "EST-04": "Índice de tablas",
    "EST-05": "Bibliografía",
    "EST-06": "Anexo",
    "TIT-01": "Entradas del índice con su título en el cuerpo",
    "TIT-02": "Páginas del índice correctas",
    "TIT-03": "Títulos con entrada en el índice",
    "FIG-01": "Numeración de figuras correlativa",
    "FIG-02": "Numeración de tablas correlativa",
    "FIG-03": "Posición del epígrafe",
    "FIG-04": "Figuras y tablas referenciadas desde el texto",
    "FIG-05": "Figuras y tablas en su índice",
    "FIG-06": "Imágenes grandes con epígrafe",
    "FIG-07": "Tablas con epígrafe",
    "LEN-01": "Persona gramatical y voseo",
}

RETIRED: frozenset[str] = frozenset()
