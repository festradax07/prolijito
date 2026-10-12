#!/usr/bin/env sh
# Regenera los PDFs de prueba con una versión fija de Typst (en Docker) y guarda la salida de
# poppler de cada uno en poppler/, para que los tests midan sin poppler instalado.
#   cumple.pdf               interlineado 1,5: no debería tener errores con unlp-tp2
#   interlineado-simple.pdf  interlineado simple: debería dar TIP-03
#   con-errores.pdf          varios errores a propósito (ver con-errores.typ)
# Requiere Docker y poppler-utils (pdftohtml, pdftotext).
set -eu
cd "$(dirname "$0")"
TYPST="ghcr.io/typst/typst:v0.13.1@sha256:253fa1351e43316f5f8dd12d0dd7906b7eedc0c986bff9a374be749032da00c0"
compile() {
  docker run --rm -u "$(id -u):$(id -g)" -v "$PWD:/data" -w /data "$TYPST" \
    compile --creation-timestamp 0 "$@"
}
compile --input leading=0.95em informe.typ cumple.pdf
compile --input leading=0.65em informe.typ interlineado-simple.pdf
compile con-errores.typ con-errores.pdf

mkdir -p poppler
for pdf in cumple interlineado-simple con-errores; do
  pdftohtml -xml -i -zoom 3 -q "$pdf.pdf" "poppler/$pdf"
  pdftotext -layout "$pdf.pdf" "poppler/$pdf.txt"
done
