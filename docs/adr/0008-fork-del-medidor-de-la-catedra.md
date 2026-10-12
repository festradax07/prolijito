# 0008. Medidor de PDF propio: fork del script de la cátedra

- Estado: Aceptada (reemplaza al ADR 0006)
- Fecha: 2026-10-11

## Contexto
Hasta acá, `third_party/formato-entregas/analizar_pdf.py` se ejecutaba como caja negra y un adaptador
compensaba sus límites (ADR 0006). Al probarlo con un informe APA y al revisar a mano las páginas
del Informe de Avance de TP2 aparecieron falsos positivos que no se podían corregir desde afuera:

- La carátula solo podía estar en la página 1 (un informe con carta de presentación fallaba, y el
  título de su carátula se tomaba como un título del cuerpo).
- «Figura A1» y «Tabla A1» no se reconocían como epígrafes.
- La posición del epígrafe de tabla se decidía contando cualquier línea con fragmentos separados en
  las 12 líneas cercanas: un párrafo con código en línea o la tabla siguiente invertían el resultado.
  En el informe de TP2, los epígrafes de las Tablas 2 y 5 estaban debajo y se reportaban arriba.
- Las tablas con celdas de varias líneas o partidas entre páginas se contaban como varias tablas sin
  epígrafe (9 FIG-07 en el informe de TP2, todos falsos según las páginas renderizadas).
- Las páginas fuera de norma solo se calculaban contra interlineado 1,5.

La cátedra autorizó modificar el script. Su licencia (MIT) lo permite conservando el aviso.

## Decisión
El script se incorpora como medidor propio en `src/prolijito/adapters/pdf/` (poppler, tipografía,
estructura, epígrafes, lenguaje), en dos pasos:

1. **Port sin cambios de comportamiento**, verificado: las mediciones del script y del port son
   idénticas en los cuatro PDFs disponibles (dos de prueba y dos informes reales).
2. **Mejoras**, cada una con test y con su efecto revisado sobre los informes reales:
   - Carátula: la primera página con aspecto de carátula antes del índice. Las páginas previas al
     índice (carta, carátula) no se analizan como cuerpo. El perfil fija hasta qué página puede
     estar (`estructura.caratula_pagina`, por defecto 1).
   - Numeración de apéndice («A1»), como serie propia para la numeración correlativa.
   - Tablas: bloques de filas con columnas alineadas, tolerando celdas de varias líneas y cortados
     por un epígrafe; continuaciones al borde de la página unidas a su tabla; el epígrafe pertenece
     a la tabla más cercana; un epígrafe justo arriba también cuenta (estilo APA).
   - Interlineado: la clase de cada página; la regla compara contra la clase del perfil.
   - Posición del epígrafe por tipo en el perfil: `epigrafes: { figuras: debajo, tablas: arriba }`.
   - Espacios normalizados en títulos, fragmentos de una línea en orden de izquierda a derecha,
     bibliografía numerada excluida del análisis de lenguaje.

La atribución queda en el encabezado de cada módulo derivado y en `NOTICE.md` (texto MIT original),
incluido en el paquete. La rúbrica pasa a `profiles/normas/unlp-tp2-rubrica.md`.

## Consecuencias
- Desaparecen `third_party/`, el subproceso con `python -I` y el JSON intermedio: se mide y se
  devuelve el dominio directamente. Poppler sigue siendo la única dependencia de sistema.
- Informe de Avance de TP2: de 25 errores a 14, todos reales (índice desactualizado, faltan índices
  de figuras y de tablas). Informe APA con un perfil propio del seminario: de 8 hallazgos (5 falsos)
  a 3 reales.
- Los tests miden los PDFs de prueba a partir de la salida de poppler guardada en
  `tests/fixtures/pdf/poppler/`; un test de sistema verifica que coincida con poppler real.
- Las mejoras no vuelven automáticamente a la cátedra. Si alguna le sirve, se puede proponer como PR
  a su repositorio.
- Queda pendiente medir márgenes y detectar referencias justificadas con huecos grandes.
