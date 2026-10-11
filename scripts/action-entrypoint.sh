#!/bin/sh
# Entrypoint de la GitHub Action (action.yml). Recorre los PDFs de `path`, publica anotaciones y el
# resumen del job, y guarda un reporte JSON por PDF en `report-dir`.
#
# Uso: prolijito-action <perfil> <archivo-o-carpeta> [profiles-dir] [fail-on] [report-dir]
set -u

profile="$1"
target="$2"
profiles_dir="${3:-}"
fail_on="${4:-error}"
report_dir="${5:-prolijito-reportes}"

set -- --profile "$profile"
if [ -n "$profiles_dir" ]; then
  set -- "$@" --profiles-dir "$profiles_dir"
fi

list="$(mktemp)"
if [ -d "$target" ]; then
  find "$target" -type f -name '*.pdf' | sort > "$list"
elif [ -f "$target" ]; then
  printf '%s\n' "$target" > "$list"
else
  echo "::error title=prolijito::No existe '$target' (input path)."
  exit 2
fi

if [ ! -s "$list" ]; then
  echo "::warning title=prolijito::No hay PDFs en '$target'."
  exit 0
fi

mkdir -p "$report_dir"
status=0
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
rm -f "$list"
exit "$status"
