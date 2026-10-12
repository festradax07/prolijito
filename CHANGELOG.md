# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones con
[SemVer](https://semver.org/lang/es/). Para la GitHub Action, usar el tag: `festradax07/prolijito@v0.2.0`.

## [0.2.0] — 2026-10-11

### Cambiado
- **Medidor de PDF propio**: el script de la cátedra de Taller de Proyecto II (UNLP) pasa a ser un
  fork dentro de `src/prolijito/adapters/pdf/`, con atribución en cada módulo y en `NOTICE.md`
  (ADR 0008). Se mide sin subproceso ni JSON intermedio; poppler sigue siendo la única dependencia.
- La rúbrica de TP2 se movió a `profiles/normas/unlp-tp2-rubrica.md`.
- `prolijito profiles --help` explica cómo crear un perfil propio con `--template`.

### Agregado
- Perfiles: `layout.epigrafes` por tipo (`{ figuras: debajo, tablas: arriba }`) y
  `estructura.caratula_pagina` (hasta qué página puede estar la carátula).
- Epígrafes con numeración de apéndice («Figura A1», «Tabla A1»).
- La carátula se busca antes del índice: una carta de presentación previa ya no la confunde, y esas
  páginas no se analizan como cuerpo.
- Interlineado medido por página y comparado contra la clase del perfil (antes, solo contra 1,5).
- README: guía para crear perfiles, con ejemplo y referencia de campos.

### Corregido
- Tablas: el texto justificado con huecos grandes ya no se toma como tabla; las celdas de varias
  líneas y las tablas que cruzan de página no generan «tabla sin epígrafe»; el epígrafe se asigna a
  la tabla más cercana (antes podía reportarse «arriba» un epígrafe que estaba debajo); un epígrafe
  justo arriba de la tabla cuenta (estilo APA).
- «No hay el índice de figuras» → «No hay índice de figuras (es opcional)».
- Espacios de más en los títulos leídos de un índice armado como tabla.
- Fragmentos de una misma línea en orden de izquierda a derecha.

## [0.1.0] — 2026-10-11

Primera versión (MVP).

- `prolijito check` sobre PDF con 22 reglas (`TIP`, `EST`, `TIT`, `FIG`, `LEN`) y exit codes.
- Reportes en Markdown, JSON y anotaciones de GitHub, con «cómo arreglar» en Docs, Word, LaTeX y Typst.
- Perfiles `informe-tecnico-es` y `unlp-tp2` con herencia (`extends`), esquema y plantilla.
- Imagen Docker, instalador (`prolijito` / `plj`) y GitHub Action (varios PDFs en `path`).
