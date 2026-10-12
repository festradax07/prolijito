# Chequeo de formato — con-errores.pdf — perfil unlp-tp2@1.0.0

**Estado:** ❌ con 6 errores y 3 puntos a revisar

## Errores (❌)

### Estructura

**EST-04 · Índice de tablas**

- Falta el índice de tablas.
- Cómo arreglar:
  - **Google Docs:** No es nativo. Lista a mano con número, leyenda y página, o un complemento de índice con estilo propio para epígrafes.
  - **Word / LibreOffice:** Referencias → Insertar tabla de ilustraciones (requiere epígrafes con Insertar título).
  - **LaTeX:** `\listoffigures` / `\listoftables`
  - **Typst:** `#outline(target: figure.where(kind: image))` / `kind: table`

**EST-05 · Bibliografía**

- Falta la bibliografía.
- Cómo arreglar:
  - **En general:** Sección «Bibliografía» con autor o título, URL o editorial y fecha de consulta.
  - **Word / LibreOffice:** Referencias → Bibliografía.
  - **LaTeX:** `\printbibliography` (biblatex) o `\bibliography{…}`
  - **Typst:** `#bibliography("referencias.bib")`

### Títulos e índice

**TIT-01 · Entradas del índice con su título en el cuerpo**

- La entrada del índice «4. Trabajo futuro» no tiene un título en el cuerpo. (esperado: título en p. 4 · medido: no encontrado)
- Cómo arreglar:
  - **Google Docs:** Insertar → Índice; usar estilos Título 1/2 en los títulos. Para actualizar, clic en el índice → Actualizar.
  - **Word / LibreOffice:** Referencias → Tabla de contenido. Para actualizar, clic derecho → Actualizar campos.
  - **LaTeX:** `\tableofcontents` (compilar dos veces).
  - **Typst:** `#outline()`

**TIT-02 · Páginas del índice correctas**

- p. 4 — «3. Resultados» no está en la página que indica el índice. (esperado: p. 3 · medido: p. 4)
- Cómo arreglar:
  - **Google Docs:** Insertar → Índice; usar estilos Título 1/2 en los títulos. Para actualizar, clic en el índice → Actualizar.
  - **Word / LibreOffice:** Referencias → Tabla de contenido. Para actualizar, clic derecho → Actualizar campos.
  - **LaTeX:** `\tableofcontents` (compilar dos veces).
  - **Typst:** `#outline()`

### Figuras y tablas

**FIG-03 · Posición del epígrafe**

- p. 3 — El epígrafe de la Tabla 1 está arriba. (esperado: debajo · medido: arriba)
- Cómo arreglar:
  - **Google Docs:** Párrafo centrado debajo de la figura o tabla, con un estilo propio («Epígrafe») para poder listarlo.
  - **Word / LibreOffice:** Referencias → Insertar título → posición «Debajo de la selección».
  - **LaTeX:** `\caption` después del `tabular` o `\includegraphics`; `\usepackage[spanish,es-tabla]{babel}` para «Tabla».
  - **Typst:** `#show figure.where(kind: table): set figure.caption(position: bottom)`

**FIG-04 · Figuras y tablas referenciadas desde el texto**

- p. 3 — La Tabla 1 no se menciona en el texto.
- Cómo arreglar:
  - **En general:** Mencionar la figura o tabla por su número en el texto («como muestra la Figura 2»).
  - **Word / LibreOffice:** Referencias → Referencia cruzada.
  - **LaTeX:** `\ref` o `\autoref`
  - **Typst:** `@etiqueta`

## Para revisar (❓)

### Tipografía

**TIP-05 · Otras familias tipográficas permitidas**

- Se usan otras familias tipográficas: DejaVuSansMono. En código o tablas puede estar bien. (esperado: Arial, Times New Roman, Libertinus · medido: DejaVuSansMono)
- Cómo arreglar:
  - **En general:** Usar la fuente del cuerpo en todo el texto; una monoespaciada solo en bloques de código.

### Lenguaje

**LEN-01 · Persona gramatical y voseo** (2)

- p. 3 — Posible pronombre 1ª/2ª persona: nuestro. (esperado: impersonal o tercera persona)
  - p. 3 — «1. Introducción En este trabajo decidimos usar nuestro propio sensor de humedad para reducir el costo total. La es»
- p. 3 — Posible verbo 1ª persona plural (candidato): decidimos. (esperado: impersonal o tercera persona)
  - p. 3 — «1. Introducción En este trabajo decidimos usar nuestro propio sensor de humedad para reducir el costo»
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
| EST-03 | Índice de figuras | ✅ |
| EST-04 | Índice de tablas | ❌ |
| EST-05 | Bibliografía | ❌ |
| EST-06 | Anexo | ℹ️ |
| TIT-01 | Entradas del índice con su título en el cuerpo | ❌ |
| TIT-02 | Páginas del índice correctas | ❌ |
| TIT-03 | Títulos con entrada en el índice | ✅ |
| FIG-01 | Numeración de figuras correlativa | ✅ |
| FIG-02 | Numeración de tablas correlativa | ✅ |
| FIG-03 | Posición del epígrafe | ❌ |
| FIG-04 | Figuras y tablas referenciadas desde el texto | ❌ |
| FIG-05 | Figuras y tablas en su índice | ✅ |
| FIG-06 | Imágenes grandes con epígrafe | ✅ |
| FIG-07 | Tablas con epígrafe | ✅ |
| LEN-01 | Persona gramatical y voseo | ❓ |
