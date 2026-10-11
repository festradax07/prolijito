# prolijito

> Dejalo prolijito.

`prolijito` valida el formato de informes contra una norma (fuente, tamaño, interlineado,
justificado, índices, epígrafes, persona gramatical), **sin tocar el contenido**. Sirve para
entregas de facultad, papers e informes de trabajo.

Funciona como *policy-as-code* para documentos: el motor es siempre el mismo y la norma es un
**perfil** en YAML que se elige por parámetro. Se valida el **PDF renderizado**, que es lo que ve
quien lee o corrige: el "1,15" de Google Docs, por ejemplo, mide como interlineado simple.

## Estado

En desarrollo, camino al MVP: `prolijito check` sobre PDF, en la terminal y como GitHub Action.

| Parte | Estado |
|---|---|
| Medición de PDF (con el script de la cátedra de TP2) | ✅ |
| 22 reglas de formato (`TIP`, `EST`, `TIT`, `FIG`, `LEN`) | ✅ |
| Perfiles YAML con herencia, plantilla para perfiles propios | ✅ |
| `prolijito profiles` | ✅ |
| Reportes Markdown, JSON y anotaciones de GitHub, con «cómo arreglar» por herramienta | ✅ |
| `prolijito check` de punta a punta | ✅ |
| Imagen Docker, instalador y GitHub Action | ⏳ |
| `fix`, `review`, `new` | ⏳ fases siguientes |

## Instalación (desde el código fuente)

Requisitos: Python 3.11 o superior y, para medir PDFs, `poppler-utils` (`pdftohtml`, `pdftotext`,
`pdfinfo`).

```bash
sudo apt install poppler-utils        # Debian/Ubuntu; en macOS: brew install poppler
git clone https://github.com/festradax07/prolijito.git
cd prolijito
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
prolijito --version
```

Más adelante la forma recomendada va a ser la imagen Docker, que trae poppler y las fuentes.

## Uso

```bash
prolijito --help                                        # comandos disponibles
prolijito profiles                                      # perfiles disponibles
prolijito check informe.pdf --profile unlp-tp2          # reporte en Markdown en la terminal
prolijito check informe.pdf --profile unlp-tp2 --format json --output reporte.json
```

Opciones de `check`:

| Opción | Para qué |
|---|---|
| `--profile` | ID de un perfil (`prolijito profiles`) o ruta a un `.yaml`. Obligatoria. |
| `--profiles-dir DIR` | Suma una carpeta con perfiles propios; tiene prioridad sobre los incluidos. |
| `--format md\|json\|github` | `md` (por defecto) para leer; `json` para otras herramientas; `github` para Actions: anotaciones y el Markdown en el resumen del job. |
| `--output ARCHIVO` | Guarda el reporte en un archivo en vez de imprimirlo. |
| `--fail-on error\|revisar\|never` | Desde qué severidad termina con exit code 1 (por defecto: `error`). |

Ejemplo de reporte (recortado):

```markdown
# Chequeo de formato — informe.pdf — perfil unlp-tp2@1.0.0

**Estado:** ❌ con 25 errores y 2 puntos a revisar

## Errores (❌)

### Títulos e índice

**TIT-02 · Páginas del índice correctas** (12)

- p. 7 — «4. Grado de Avance» no está en la página que indica el índice. (esperado: p. 6 · medido: p. 7)
- Cómo arreglar:
  - **Google Docs:** Insertar → Índice; usar estilos Título 1/2 en los títulos. Para actualizar, clic en el índice → Actualizar.
  - **Word / LibreOffice:** Referencias → Tabla de contenido. Para actualizar, clic derecho → Actualizar campos.
  - **LaTeX:** `\tableofcontents` (compilar dos veces).
  - **Typst:** `#outline()`
```

El reporte completo de ejemplo está en
[`tests/report/snapshots/tp2-informe-avance.md`](tests/report/snapshots/tp2-informe-avance.md).

Exit codes: `0` sin errores · `1` hay violaciones de severidad `error` (o la que indique
`--fail-on`) · `2` error de ejecución (archivo inexistente, perfil inválido, dependencia faltante).

## Perfiles

| Perfil | Para qué |
|---|---|
| `informe-tecnico-es` | Base genérica y permisiva para informes técnicos en español. Pensada para extenderse. |
| `unlp-tp2` | Entregas de Taller de Proyecto II (UNLP). Extiende la base con la [rúbrica de la cátedra](third_party/formato-entregas/rubrica.md): Arial, Times New Roman o Libertinus 12 pt, interlineado 1,5, justificado, epígrafes debajo e índices de figuras y tablas si las hay. |

### Crear un perfil propio

```bash
prolijito profiles --template mi-catedra > mi-catedra.yaml
# editar mi-catedra.yaml
prolijito check informe.pdf --profile mi-catedra.yaml
prolijito check informe.pdf --profile mi-catedra --profiles-dir ./perfiles
```

La plantilla viene comentada. Lo importante:

- **El `id` es el nombre del archivo**: `mi-catedra` vive en `mi-catedra.yaml`.
- **Herencia con `extends: <perfil>@<versión mayor>`**: solo se escribe lo que cambia; las listas
  del hijo reemplazan a las del padre.
- **Severidades**: cualquier regla se puede bajar o subir de severidad, por ejemplo
  `severidades: { LEN-01: info }`.
- Los perfiles con normas internas (de una empresa, de un cliente) se guardan fuera de este repo y se
  usan con `--profiles-dir`.

## Reglas

Cada violación tiene un ID estable y una severidad: ❌ `error` (corregir), ❓ `revisar` (criterio
humano) o ℹ️ `info`. La tabla muestra la severidad por defecto; el perfil la puede cambiar.

| ID | Qué verifica | Severidad |
|---|---|---|
| TIP-01 | Fuente del cuerpo permitida | ❌ |
| TIP-02 | Tamaño del cuerpo | ❌ |
| TIP-03 | Interlineado | ❌ (❓ si no se pudo medir) |
| TIP-04 | Texto justificado | ❌ si no está justificado, ❓ si lo está en parte |
| TIP-05 | Otras familias tipográficas (código, tablas) | ❓ |
| EST-01 | Carátula sola en la página 1 | ❌ |
| EST-02 | Índice general | ❌ |
| EST-03 | Índice de figuras | ❌ |
| EST-04 | Índice de tablas | ❌ |
| EST-05 | Bibliografía | ❌ |
| EST-06 | Anexo | ℹ️ |
| TIT-01 | Entrada del índice sin título en el cuerpo | ❌ |
| TIT-02 | Página del índice que no coincide | ❌ |
| TIT-03 | Título sin entrada en el índice | ❓ |
| FIG-01 | Numeración de figuras correlativa | ❌ |
| FIG-02 | Numeración de tablas correlativa | ❌ |
| FIG-03 | Posición del epígrafe | ❌ (❓ si no se pudo determinar) |
| FIG-04 | Figura o tabla mencionada en el texto | ❌ |
| FIG-05 | Figura o tabla en su índice | ❌ |
| FIG-06 | Imagen grande sin epígrafe | ❓ |
| FIG-07 | Tabla sin epígrafe | ❌ |
| LEN-01 | Primera o segunda persona y voseo | ❓ |

Las secciones que el perfil marca como opcionales o "si hay figuras/tablas" solo se exigen cuando
corresponde.

## Desarrollo

```bash
make install        # pip install -e '.[dev]' y hook de pre-commit
make check          # ruff + mypy --strict + import-linter + pytest
make format         # formatea y aplica fixes automáticos
```

- Arquitectura hexagonal (`domain` → `validate` → `application` → `adapters`/`report` → `cli`). La
  CI falla si una capa importa de una superior. Ver [ADR 0005](docs/adr/0005-arquitectura-hexagonal-y-calidad.md).
- Los tests corren sin poppler usando mediciones guardadas en `tests/fixtures/`. Los que necesitan
  dependencias de sistema llevan `@pytest.mark.system`: `pytest -m system` mide los PDFs que haya
  en `docs/doc_test/` (carpeta ignorada por git, para documentos reales que no se suben).
- Las decisiones de diseño están en [`docs/adr/`](docs/adr/).

## Créditos

La medición de PDF usa el script y la rúbrica de la cátedra **Taller de Proyecto II** (Ingeniería en
Computación, UNLP), incluidos sin modificaciones en [`third_party/formato-entregas/`](third_party/formato-entregas/).

## Licencia

[AGPL-3.0-or-later](./LICENSE). Si se ofrece prolijito como servicio en red, hay que publicar el
código fuente de esa versión, modificaciones incluidas.

`third_party/formato-entregas/` conserva su propia licencia MIT (ver
[`third_party/formato-entregas/LICENSE`](./third_party/formato-entregas/LICENSE)).
