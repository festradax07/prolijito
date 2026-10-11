# 0001. MVP sin servidor: CLI y GitHub Action sobre una única imagen Docker

- Estado: Aceptada
- Fecha: 2026-10-11

## Contexto
El MVP tiene que usarse desde la terminal (Linux, macOS, Windows) y desde GitHub Actions. Las
dependencias reales (poppler, typst, pandoc, vale y las fuentes) son difíciles de instalar igual en
todos lados, y una fuente faltante cambia el render y hace fallar la validación por un motivo ajeno
al documento. Además, para uso laboral los documentos no deberían pasar por un servidor de terceros.

## Opciones
- **A — Scripts nativos + instrucciones de instalación**: liviano / resultados distintos por máquina.
- **B — Servicio web hosteado**: cero instalación / custodia de documentos, costo y operación desde el día uno.
- **C — Imagen Docker + wrappers finos (`.sh`, `.ps1`) + container action**: mismo binario en todos lados / requiere Docker.

## Decisión
Se elige C. Cumple el principio "mismo binario en todos lados", no custodia datos (cada usuario trae su
API key o ninguna) y cuesta 0 en hosting (GHCR + Actions).

## Consecuencias
- Requiere Docker en la máquina del usuario.
- La imagen del MVP se reutiliza como worker del servicio de la v2.
- La imagen se publica por tag y las fuentes se fijan dentro de ella.
