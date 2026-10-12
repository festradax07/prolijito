# 0009. Publicación de la imagen en GHCR por tag

- Estado: Aceptada
- Fecha: 2026-10-11

## Contexto
Hasta la 0.2.0 la imagen no estaba publicada (ADR 0007): el instalador necesitaba `--build` y la
GitHub Action construía la imagen en cada ejecución.

## Opciones
- **A — Publicar a mano** con un token personal: depende de una persona y de su arquitectura.
- **B — Workflow al crear un tag**, con el `GITHUB_TOKEN` de la ejecución: automático, sin credenciales
  guardadas, multiarquitectura.

## Decisión
Se elige B (`.github/workflows/release.yml`):

- Se dispara con tags `v*` y publica `ghcr.io/festradax07/prolijito` con las etiquetas `X.Y.Z`,
  `X.Y` y `latest`, para `linux/amd64` y `linux/arm64`.
- Antes de publicar verifica que el tag coincida con `__version__` y prueba la imagen con los PDFs
  de prueba (uno que cumple, exit 0; uno con interlineado simple, exit 1). Si algo falla, no publica.
- Permisos mínimos: `contents: read`, `packages: write`.
- `scripts/install.sh` descarga por defecto la imagen de la misma versión que el repo clonado.

## Consecuencias
- El package se crea privado: hay que hacerlo público una vez desde la configuración del package
  (y un package público no puede volver a ser privado; el código ya es público, AGPL).
- El tag se crea después de que la CI de `main` esté en verde.
- Desde 0.3.1, `action.yml` usa `docker://ghcr.io/festradax07/prolijito:<versión>`. La CI de `main`
  lo reemplaza por `Dockerfile` (la imagen de esa versión todavía no existe) y el workflow de
  publicación verifica la Action con la imagen ya publicada. Al subir la versión hay que actualizar
  `__version__` y `action.yml` juntos: la publicación falla si no coinciden.
