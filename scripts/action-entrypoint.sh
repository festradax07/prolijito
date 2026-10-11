#!/bin/sh
# Entrypoint de la GitHub Action (action.yml). Recorre los PDFs de `path`, publica anotaciones y el
# resumen del job, y guarda un reporte JSON por PDF en `report-dir`.
#
# Uso: prolijito-action <perfil> <rutas> [profiles-dir] [fail-on] [report-dir]
#   <rutas>: uno o más PDFs o carpetas, uno por línea (por ejemplo, la salida de `git diff --name-only`).
# Exit: 0 sin errores · 1 hay violaciones desde `fail-on` · 2 una ruta no existe o un chequeo falló.
set -u

profile="$1"
targets="$2"
profiles_dir="${3:-}"
fail_on="${4:-error}"
report_dir="${5:-prolijito-reportes}"

set -- --profile "$profile"
if [ -n "$profiles_dir" ]; then
  set -- "$@" --profiles-dir "$profiles_dir"
fi

entries="$(mktemp)"
list="$(mktemp)"
trap 'rm -f "$entries" "$list"' EXIT
printf '%s\n' "$targets" > "$entries"

status=0
while IFS= read -r entry; do
  entry="$(printf '%s' "$entry" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
  if [ -z "$entry" ]; then
    continue
  elif [ -d "$entry" ]; then
    find "$entry" -type f -name '*.pdf' >> "$list"
  elif [ -f "$entry" ]; then
    printf '%s\n' "$entry" >> "$list"
  else
    echo "::error title=prolijito::No existe '$entry' (input path)."
    status=2
  fi
done < "$entries"
sort -u -o "$list" "$list"

if [ ! -s "$list" ]; then
  if [ "$status" -eq 0 ]; then
    echo "::warning title=prolijito::No hay PDFs para chequear en el input path."
  fi
  exit "$status"
fi

mkdir -p "$report_dir"
while IFS= read -r pdf; do
  prolijito check "$pdf" "$@" --format github --fail-on "$fail_on"
  code=$?
  # Nombre del reporte: la ruta con "/" reemplazada, para que no choquen PDFs homónimos.
  report="$report_dir/$(printf '%s' "${pdf%.pdf}" | sed 's|^\./||; s|/|__|g').json"
  prolijito check "$pdf" "$@" --format json --fail-on never --output "$report" 2>/dev/null
  if [ "$code" -eq 2 ]; then
    echo "::error title=prolijito::No se pudo chequear '$pdf' (ver el log del paso)."
    status=2
  elif [ "$code" -eq 1 ] && [ "$status" -eq 0 ]; then
    status=1
  fi
done < "$list"
exit "$status"
