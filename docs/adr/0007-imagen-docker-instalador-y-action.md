# 0007. Imagen Docker, instalador y GitHub Action

- Estado: Aceptada
- Fecha: 2026-10-11

## Contexto
El ADR 0001 fija una sola imagen para la CLI y la GitHub Action. Al implementarla aparecieron
restricciones concretas:

- GitHub ejecuta las *container actions* como root y no permite `USER` en el Dockerfile: con otro
  usuario la acción no puede escribir en el workspace ni en `$GITHUB_STEP_SUMMARY`.
- En la CLI local, un contenedor root deja archivos de root en la carpeta del usuario (`--output`).
- Debian 13 (base de `python:3.12-slim`) no trae `fonts-libertinus`.
- La definición de terminado del MVP pide un PDF que cumpla la rúbrica y otro con interlineado
  simple. No se pueden usar documentos reales en el repo.
- Publicar la imagen en GHCR está fuera del alcance del MVP.

## Decisión
- **Imagen**: `python:3.12-slim` fijada por digest, *multi-stage* (el venv se arma en una etapa y se
  copia; sin compiladores en la final), `poppler-utils`, `fonts-liberation`,
  `fonts-linuxlibertine`, `fontconfig`. El script de la cátedra y los perfiles van en
  `/opt/prolijito` y se ubican por `PROLIJITO_CATHEDRA_SCRIPT` y `PROLIJITO_PROFILES_DIR`.
- **Usuario**: la imagen no declara `USER` (requisito de Actions). El wrapper de la CLI
  (`scripts/install.sh`) corre siempre con `-u $(id -u):$(id -g)`, así los archivos quedan del
  usuario del host. Se aparta del "usuario no root" de `MVP.md` por la restricción de GitHub.
- **Instalador**: `install.sh` usa la imagen publicada por defecto y `--build` para construirla
  desde el repo. Hasta que exista la publicación en GHCR, el camino documentado es `--build`.
- **Action**: `runs.using: docker` con `image: Dockerfile` (se construye en cada ejecución, ~1-2 min)
  y un entrypoint propio que recorre carpetas, anota, escribe el resumen y deja un JSON por PDF.
- **PDFs de prueba**: se generan desde `tests/fixtures/pdf/informe.typ` (contenido propio) con
  Typst en Docker, versión y digest fijos, y se commitean. Typst se usa solo para los fixtures; no
  entra en la imagen del producto.

## Consecuencias
- Local y Docker dan el mismo reporte sobre el mismo PDF (verificado con un informe real).
- Los archivos fuera de la carpeta actual no son visibles para el wrapper: hay que ejecutar desde
  una carpeta que contenga el PDF y los perfiles.
- Cuando se publique la imagen en GHCR, `action.yml` puede pasar a `image: docker://…:<tag>` y
  dejar de construir en cada ejecución.
- La CI construye la imagen, verifica la definición de terminado y ejecuta la propia Action.
