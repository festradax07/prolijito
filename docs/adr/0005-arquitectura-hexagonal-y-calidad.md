# 0005. Arquitectura hexagonal en Python y calidad forzada por CI

- Estado: Aceptada
- Fecha: 2026-10-11

## Contexto
El proyecto va a crecer por etapas (check, fix, review, API, MCP) y cambiar piezas concretas: el
medidor de la cátedra por uno propio, nuevos formatos de entrada y de reporte. Se evaluó Go por su
tipado y su binario único, pero la imagen Docker ya resuelve la distribución (ADR 0001) y las fases
siguientes dependen de bibliotecas de Python (Presidio, spaCy, pdfplumber/pymupdf).

## Opciones
- **A — Go**: tipado nativo, binario único / sin ecosistema de NLP ni de layout de PDF equivalente.
- **B — Python sin estructura impuesta**: rápido al principio / el acoplamiento crece sin control.
- **C — Python con arquitectura hexagonal y herramientas que la verifican**: núcleo testeable y
  piezas reemplazables / más archivos y configuración desde el día uno.

## Decisión
Se elige C.

Capas (cada una solo importa de las de abajo):

```
cli                    entrypoint: arma dependencias y llama a los casos de uso
adapters | report      implementaciones de los puertos (medidor, perfiles YAML, reportes)
application            casos de uso (check) y puertos (Protocol)
validate               reglas puras: Measurements + Profile → [Violation]
domain                 entidades y valores, sin I/O ni dependencias externas
```

Herramientas, todas de desarrollo y sin efecto en la imagen:

- `ruff`: formato y lint con un set amplio de reglas (incluye complejidad ciclomática).
- `mypy --strict`: tipado completo.
- `import-linter`: verifica el orden de capas y que `domain` y `validate` no importen YAML ni jsonschema.
- `pytest` + `pytest-cov` con cobertura mínima.
- `pre-commit`: corre lo anterior antes de cada commit.

## Consecuencias
- La CI falla si se rompe una capa, baja la cobertura o falta un tipo.
- Las reglas se prueban con datos en memoria, sin poppler.
- Reemplazar el script de la cátedra es agregar un adaptador `Measurer`.
- La estructura de `src/` difiere de la versión inicial de `CLAUDE.md`, que se actualiza.
