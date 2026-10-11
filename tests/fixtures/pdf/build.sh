#!/usr/bin/env sh
# Regenera los PDFs de prueba desde informe.typ con una versión fija de Typst (en Docker).
#   cumple.pdf               interlineado 1,5: no debería tener errores con unlp-tp2
#   interlineado-simple.pdf  interlineado simple: debería dar TIP-03
set -eu
cd "$(dirname "$0")"
TYPST="ghcr.io/typst/typst:v0.13.1@sha256:253fa1351e43316f5f8dd12d0dd7906b7eedc0c986bff9a374be749032da00c0"
compile() {
  docker run --rm -u "$(id -u):$(id -g)" -v "$PWD:/data" -w /data "$TYPST" \
    compile --input "leading=$1" --creation-timestamp 0 informe.typ "$2"
}
compile 0.95em cumple.pdf
compile 0.65em interlineado-simple.pdf
