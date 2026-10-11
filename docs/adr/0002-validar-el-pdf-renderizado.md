# 0002. Validar el PDF renderizado, corregir el fuente

- Estado: Aceptada
- Fecha: 2026-10-11

## Contexto
Quien corrige ve el PDF. Lo que dice el menú de un editor no coincide con el resultado: el "1,15" de
Google Docs y el `\linespread{1.15}` de LaTeX miden 1,33–1,39× el tamaño de fuente, es decir, simple.
El script de la cátedra ya mide sobre el PDF con poppler.

## Opciones
- **A — Validar el fuente** (Typst/LaTeX/docx): fácil de mapear a correcciones / no ve el resultado real.
- **B — Validar el PDF y corregir el fuente**: mide lo que importa / requiere recompilar en cada vuelta.

## Decisión
Se elige B. El validador consume el PDF; el fixer edita el fuente y recompila. Con entrada solo PDF,
el resultado es reporte + sugerencias, sin autofix.

## Consecuencias
- El loop necesita un render reproducible (motivo adicional para la imagen Docker, ADR 0001).
- Typst es el primer formato con loop completo por su compilación rápida.
