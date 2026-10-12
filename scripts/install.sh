#!/usr/bin/env sh
# Instala `prolijito` y el alias `plj` como wrappers de `docker run`.
#
#   scripts/install.sh                 descarga la imagen publicada en GHCR, de la misma versión que
#                                      esta copia del repo (o la de $PROLIJITO_IMAGE / --image)
#   scripts/install.sh --build         construye la imagen desde esta copia del repo (prolijito:local)
#   scripts/install.sh --bin-dir DIR   instala en DIR (por defecto: ~/.local/bin)
#
# El wrapper monta la carpeta actual en /work y corre como el usuario actual: los archivos que se
# le pasan tienen que estar dentro de la carpeta desde la que se ejecuta.
set -eu

REGISTRY_IMAGE="ghcr.io/festradax07/prolijito"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
# Versión de esta copia del repo: la instalación es reproducible (no depende de :latest).
VERSION="$(sed -n 's/^__version__ = "\(.*\)"$/\1/p' "$REPO/src/prolijito/__init__.py" 2>/dev/null || true)"
IMAGE="${PROLIJITO_IMAGE:-$REGISTRY_IMAGE:${VERSION:-latest}}"
BIN_DIR="${PROLIJITO_BIN_DIR:-$HOME/.local/bin}"
BUILD=0

fail() {
  echo "install.sh: error: $1" >&2
  exit 1
}

usage() {
  sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
}

while [ $# -gt 0 ]; do
  case "$1" in
    --build) BUILD=1 ;;
    --image) [ $# -ge 2 ] || fail "--image necesita un valor."; IMAGE="$2"; shift ;;
    --bin-dir) [ $# -ge 2 ] || fail "--bin-dir necesita un valor."; BIN_DIR="$2"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) fail "opción desconocida: $1 (ver --help)." ;;
  esac
  shift
done

command -v docker >/dev/null 2>&1 \
  || fail "no se encontró Docker. Instalarlo desde https://docs.docker.com/get-docker/ y volver a correr este script."
docker info >/dev/null 2>&1 \
  || fail "Docker está instalado pero no responde. Verificar que el servicio esté iniciado y que el usuario tenga permisos (grupo docker)."

if [ "$BUILD" -eq 1 ]; then
  [ -f "$REPO/Dockerfile" ] || fail "--build se usa desde una copia del repo (no se encontró $REPO/Dockerfile)."
  IMAGE="prolijito:local"
  echo "Construyendo $IMAGE desde $REPO..."
  docker build -t "$IMAGE" "$REPO"
else
  echo "Descargando $IMAGE..."
  docker pull "$IMAGE" \
    || fail "no se pudo descargar $IMAGE. Verificar la conexión, o construir la imagen localmente con --build."
fi

mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/prolijito" <<WRAPPER
#!/usr/bin/env sh
# Generado por prolijito/scripts/install.sh: ejecuta prolijito en Docker sobre la carpeta actual.
exec docker run --rm -v "\$PWD:/work" -w /work -u "\$(id -u):\$(id -g)" "$IMAGE" "\$@"
WRAPPER
chmod +x "$BIN_DIR/prolijito"
ln -sf prolijito "$BIN_DIR/plj"

echo "Instalado: $BIN_DIR/prolijito (alias: plj) → $IMAGE"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) echo "Agregar $BIN_DIR al PATH, por ejemplo: echo 'export PATH=\"$BIN_DIR:\$PATH\"' >> ~/.bashrc" ;;
esac
echo "Probar con: prolijito --version"
