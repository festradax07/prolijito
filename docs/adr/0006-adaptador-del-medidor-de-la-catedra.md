# 0006. Adaptador del medidor de la cátedra y sus compensaciones

- Estado: Reemplazada por el ADR 0008
- Fecha: 2026-10-11

## Contexto
`third_party/formato-entregas/analizar_pdf.py` no se edita (UPSTREAM.md). Al correrlo con `--json`
sobre un informe real de TP2 aparecieron diferencias entre lo que mide y lo que necesitan las reglas:

- Mezcla medición y juicio: `fuente_ok`, `tamano_ok` y `familias_no_permitidas` usan constantes
  propias (`FUENTES_OK`, `TAM_OK`), no el perfil.
- `interlineado.paginas_fuera` se calcula siempre contra "1,5".
- Las secciones con número adelante ("6. Bibliografía") no se detectan: el patrón exige el título
  solo. El informe real tenía bibliografía y el script la daba por ausente.
- Los logos de la carátula cuentan en `imagenes_por_pagina`, y un documento sin figuras pero con
  logos exigiría índice de figuras.
- Detalles de formato: `"sí"` con tilde, claves numéricas como texto, el cotejo de epígrafes con el
  índice en una lista aparte.

## Opciones
- **A — Usar los campos tal cual**: simple / falsos positivos y la norma de TP2 filtrada en todos los perfiles.
- **B — Reescribir el medidor ya**: control total / semanas de trabajo antes de tener un MVP.
- **C — Adaptador que traduce y compensa, sin tocar el script**: aprovecha lo medido y corrige lo
  conocido / el adaptador conoce detalles del script.

## Decisión
Se elige C. `adapters/cathedra_measurer.py` traduce el JSON al contrato `Measurements` del dominio:

- Ignora los campos con juicio (`fuente_ok`, `tamano_ok`, `familias_no_permitidas`); las reglas
  comparan `fuentes.cuerpo` y `fuentes.otras` contra el perfil.
- Expone `paginas_fuera` junto con la clase contra la que se calculó (`deviant_from`); la regla solo
  las usa si el perfil pide esa misma clase.
- Completa bibliografía y anexo buscando en `titulos_detectados` con la numeración quitada.
- Si la página 1 parece carátula, no cuenta sus imágenes como figuras.

## Consecuencias
- Cada compensación tiene un test con el fixture `tests/fixtures/mediciones/tp2-informe-avance.json`.
- Cuando se actualice el script desde upstream, se corre de nuevo sobre un PDF real y se revisan estas
  compensaciones.
- Reemplazar el medidor es escribir otro adaptador que devuelva `Measurements`; las reglas no cambian.
