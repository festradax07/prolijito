# Chequeo de formato — entrega.pdf — perfil unlp-tp2@1.0.0

**Estado:** ❌ con 25 errores y 2 puntos a revisar

## Errores (❌)

### Estructura

**EST-03 · Índice de figuras**

- Falta el índice de figuras.
- Cómo arreglar:
  - **Google Docs:** No es nativo. Lista a mano con número, leyenda y página, o un complemento de índice con estilo propio para epígrafes.
  - **Word / LibreOffice:** Referencias → Insertar tabla de ilustraciones (requiere epígrafes con Insertar título).
  - **LaTeX:** `\listoffigures` / `\listoftables`
  - **Typst:** `#outline(target: figure.where(kind: image))` / `kind: table`

**EST-04 · Índice de tablas**

- Falta el índice de tablas.
- Cómo arreglar:
  - **Google Docs:** No es nativo. Lista a mano con número, leyenda y página, o un complemento de índice con estilo propio para epígrafes.
  - **Word / LibreOffice:** Referencias → Insertar tabla de ilustraciones (requiere epígrafes con Insertar título).
  - **LaTeX:** `\listoffigures` / `\listoftables`
  - **Typst:** `#outline(target: figure.where(kind: image))` / `kind: table`

### Títulos e índice

**TIT-02 · Páginas del índice correctas** (12)

- p. 7 — «4. Grado de Avance» no está en la página que indica el índice. (esperado: p. 6 · medido: p. 7)
- p. 7 — «4.1 Grado de Avance por Parte» no está en la página que indica el índice. (esperado: p. 6 · medido: p. 7)
- p. 8 — «4.2 Cumplimiento del Avance de Octubre» no está en la página que indica el índice. (esperado: p. 7 · medido: p. 8)
- p. 10 — «4.4.1 Código que controla el hardware» no está en la página que indica el índice. (esperado: p. 9 · medido: p. 10)
- p. 11 — «4.4.2 Código que controla las comunicaciones» no está en la página que indica el índice. (esperado: p. 10 · medido: p. 11)
- p. 12 — «4.4.3 Código del Sistema y la interfaz web» no está en la página que indica el índice. (esperado: p. 11 · medido: p. 12)
- p. 13 — «4.5 Modelo de clasificación y optimización para la Raspberry Pi» no está en la página que indica el índice. (esperado: p. 12 · medido: p. 13)
- p. 14 — «4.6 Pruebas realizadas» no está en la página que indica el índice. (esperado: p. 13 · medido: p. 14)
- p. 15 — «4.7 Problemas encontrados y soluciones» no está en la página que indica el índice. (esperado: p. 14 · medido: p. 15)
- p. 17 — «5.2 Capturas de la interfaz web» no está en la página que indica el índice. (esperado: p. 16 · medido: p. 17)
- p. 18 — «5.4 Bitácora y repositorio» no está en la página que indica el índice. (esperado: p. 17 · medido: p. 18)
- p. 18 — «6. Bibliografía» no está en la página que indica el índice. (esperado: p. 17 · medido: p. 18)
- Cómo arreglar:
  - **Google Docs:** Insertar → Índice; usar estilos Título 1/2 en los títulos. Para actualizar, clic en el índice → Actualizar.
  - **Word / LibreOffice:** Referencias → Tabla de contenido. Para actualizar, clic derecho → Actualizar campos.
  - **LaTeX:** `\tableofcontents` (compilar dos veces).
  - **Typst:** `#outline()`

### Figuras y tablas

**FIG-03 · Posición del epígrafe** (2)

- p. 8 — El epígrafe de la Tabla 2 está arriba. (esperado: debajo · medido: arriba)
- p. 12 — El epígrafe de la Tabla 5 está arriba. (esperado: debajo · medido: arriba)
- Cómo arreglar:
  - **Google Docs:** Párrafo centrado debajo de la figura o tabla, con un estilo propio («Epígrafe») para poder listarlo.
  - **Word / LibreOffice:** Referencias → Insertar título → posición «Debajo de la selección».
  - **LaTeX:** `\caption` después del `tabular` o `\includegraphics`; `\usepackage[spanish,es-tabla]{babel}` para «Tabla».
  - **Typst:** `#show figure.where(kind: table): set figure.caption(position: bottom)`

**FIG-07 · Tablas con epígrafe** (9)

- p. 4 — Hay una tabla sin epígrafe (o un bloque que parece tabla).
- p. 4 — Hay una tabla sin epígrafe (o un bloque que parece tabla).
- p. 7 — Hay una tabla sin epígrafe (o un bloque que parece tabla).
- p. 7 — Hay una tabla sin epígrafe (o un bloque que parece tabla).
- p. 7 — Hay una tabla sin epígrafe (o un bloque que parece tabla).
- p. 8 — Hay una tabla sin epígrafe (o un bloque que parece tabla).
- p. 8 — Hay una tabla sin epígrafe (o un bloque que parece tabla).
- p. 12 — Hay una tabla sin epígrafe (o un bloque que parece tabla).
- p. 15 — Hay una tabla sin epígrafe (o un bloque que parece tabla).
- Cómo arreglar:
  - **Google Docs:** Párrafo centrado debajo de la figura o tabla, con un estilo propio («Epígrafe») para poder listarlo.
  - **Word / LibreOffice:** Referencias → Insertar título → posición «Debajo de la selección».
  - **LaTeX:** `\caption` después del `tabular` o `\includegraphics`; `\usepackage[spanish,es-tabla]{babel}` para «Tabla».
  - **Typst:** `#show figure.where(kind: table): set figure.caption(position: bottom)`

## Para revisar (❓)

### Tipografía

**TIP-05 · Otras familias tipográficas permitidas**

- Se usan otras familias tipográficas: CourierNew. En código o tablas puede estar bien. (esperado: Arial, Times New Roman, Libertinus · medido: CourierNew)
- Cómo arreglar:
  - **En general:** Usar la fuente del cuerpo en todo el texto; una monoespaciada solo en bloques de código.

### Lenguaje

**LEN-01 · Persona gramatical y voseo**

- p. 3 — Posible verbo 1ª persona plural (candidato): tomamos. (esperado: impersonal o tercera persona)
  - p. 3 — «contexto anonimizado tomamos contexto anonimizado»
- Cómo arreglar:
  - **En general:** Reescribir en impersonal («se propone», «se implementó») o en tercera persona («el grupo definió»). Leer la oración completa: puede ser un falso positivo.

## Informativo (ℹ️)

### Estructura

**EST-06 · Anexo**

- No hay anexo (es opcional).
- Cómo arreglar:
  - **En general:** Opcional. Para código extenso, datasheets o esquemáticos grandes.

## Detalle por criterio

| ID | Criterio | Estado |
|---|---|---|
| TIP-01 | Fuente del cuerpo permitida | ✅ |
| TIP-02 | Tamaño del cuerpo | ✅ |
| TIP-03 | Interlineado | ✅ |
| TIP-04 | Texto justificado | ✅ |
| TIP-05 | Otras familias tipográficas permitidas | ❓ |
| EST-01 | Carátula en la página 1 | ✅ |
| EST-02 | Índice general | ✅ |
| EST-03 | Índice de figuras | ❌ |
| EST-04 | Índice de tablas | ❌ |
| EST-05 | Bibliografía | ✅ |
| EST-06 | Anexo | ℹ️ |
| TIT-01 | Entradas del índice con su título en el cuerpo | ✅ |
| TIT-02 | Páginas del índice correctas | ❌ |
| TIT-03 | Títulos con entrada en el índice | ✅ |
| FIG-01 | Numeración de figuras correlativa | ✅ |
| FIG-02 | Numeración de tablas correlativa | ✅ |
| FIG-03 | Posición del epígrafe | ❌ |
| FIG-04 | Figuras y tablas referenciadas desde el texto | ✅ |
| FIG-05 | Figuras y tablas en su índice | ✅ |
| FIG-06 | Imágenes grandes con epígrafe | ✅ |
| FIG-07 | Tablas con epígrafe | ❌ |
| LEN-01 | Persona gramatical y voseo | ❓ |
