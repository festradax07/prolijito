#!/usr/bin/env sh
# Prueba de humo de una imagen de prolijito con los PDFs de prueba del repo.
#
#   scripts/smoke-test.sh                                   imagen publicada de la versión del repo
#   scripts/smoke-test.sh ghcr.io/festradax07/prolijito:0.3.1
#   scripts/smoke-test.sh prolijito:dev                     una imagen construida localmente
#
# La usan la CI y el workflow de publicación; también sirve para probar una imagen a mano.
set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
VERSION="$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$REPO/src/prolijito/__init__.py")"
IMAGE="${1:-ghcr.io/festradax07/prolijito:$VERSION}"
PDFS="$REPO/tests/fixtures/pdf"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT
failures=0

run() {
  docker run --rm -u "$(id -u):$(id -g)" -v "$PDFS:/work:ro" -v "$OUT:/out" -w /work "$IMAGE" "$@"
}

check() {
  name="$1"
  shift
  if "$@" > "$OUT/log" 2>&1; then
    echo "ok    $name"
  else
    echo "FALLA $name"
    sed 's/^/      /' "$OUT/log"
    failures=$((failures + 1))
  fi
}

expect_exit() {
  expected="$1"
  shift
  set +e
  "$@" > /dev/null 2>&1
  code=$?
  set -e
  [ "$code" -eq "$expected" ] || { echo "exit $code, se esperaba $expected"; return 1; }
}

echo "Probando $IMAGE"
check "descarga o imagen local disponible" sh -c "docker image inspect '$IMAGE' >/dev/null 2>&1 || docker pull -q '$IMAGE'"
check "--version informa la versión" sh -c "docker run --rm '$IMAGE' --version | grep -q 'prolijito '"
check "profiles lista los perfiles incluidos" sh -c "docker run --rm '$IMAGE' profiles | grep -q unlp-tp2"
check "--template genera un perfil" sh -c "docker run --rm '$IMAGE' profiles --template prueba | grep -q 'id: prueba'"
check "un PDF que cumple → exit 0" expect_exit 0 run check cumple.pdf --profile unlp-tp2
check "interlineado simple → exit 1" expect_exit 1 run check interlineado-simple.pdf --profile unlp-tp2
check "interlineado simple → TIP-03 en el JSON" sh -c "
  docker run --rm -u '$(id -u):$(id -g)' -v '$PDFS:/work:ro' -w /work '$IMAGE' \
    check interlineado-simple.pdf --profile unlp-tp2 --format json --fail-on never \
    | grep -q '\"id\": \"TIP-03\"'"
check "PDF con errores → 10 hallazgos" sh -c "
  docker run --rm -u '$(id -u):$(id -g)' -v '$PDFS:/work:ro' -w /work '$IMAGE' \
    check con-errores.pdf --profile unlp-tp2 --format json --fail-on never \
    | grep -c '\"id\": ' | grep -qx 10"
check "--output escribe el reporte" sh -c "
  docker run --rm -u '$(id -u):$(id -g)' -v '$PDFS:/work:ro' -v '$OUT:/out' -w /work '$IMAGE' \
    check cumple.pdf --profile unlp-tp2 --output /out/reporte.md 2>/dev/null; test -s '$OUT/reporte.md'"
check "--format github anota errores" sh -c "
  docker run --rm -u '$(id -u):$(id -g)' -v '$PDFS:/work:ro' -w /work '$IMAGE' \
    check interlineado-simple.pdf --profile unlp-tp2 --format github --fail-on never \
    | grep -q '^::error '"
check "entrypoint de la Action recorre una carpeta" expect_exit 1 \
  docker run --rm -u "$(id -u):$(id -g)" -v "$PDFS:/work:ro" -w /work \
    --entrypoint /usr/local/bin/prolijito-action "$IMAGE" unlp-tp2 . "" error /tmp/reportes
check "archivo inexistente → exit 2" expect_exit 2 run check no-existe.pdf --profile unlp-tp2

if [ "$failures" -gt 0 ]; then
  echo "$failures prueba(s) fallaron."
  exit 1
fi
echo "Todas las pruebas pasaron."
