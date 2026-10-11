# 0004. Open source con licencia AGPL-3.0-or-later

- Estado: Aceptada
- Fecha: 2026-10-11

## Contexto
prolijito nace como herramienta de uso propio (trabajo, entregas de facultad) y proyecto de portfolio.
Un SaaS desde el inicio exige cobros, soporte y custodia de documentos, y choca con el ADR 0001
(todo corre local, sin servidor). La v2 ya prevé una API con workers self-hosteable, así que la
puerta a un servicio hosteado queda abierta.

## Opciones
- **A — SaaS cerrado**: posible ingreso / costo y operación desde el día uno, custodia de documentos.
- **B — Open source MIT o Apache-2.0**: máxima adopción / un tercero puede ofrecerlo como SaaS cerrado.
- **C — Open source AGPL-3.0-or-later**: abierto y quien lo ofrezca como servicio en red publica sus
  cambios / algunas empresas evitan dependencias AGPL.

## Decisión
Se elige C. Mantiene el proyecto abierto y deja viable un modelo open core (motor abierto, versión
hosteada opcional) sin que otro pueda cerrar una copia.

## Consecuencias
- `LICENSE` en la raíz y `license = "AGPL-3.0-or-later"` en `pyproject.toml`.
- `third_party/formato-entregas/` sigue bajo MIT; es compatible y se conserva su aviso.
- Contribuciones externas quedan bajo la misma licencia. Si se quisiera relicenciar en el futuro
  (por ejemplo, para una versión comercial) haría falta un CLA, a decidir cuando haya contribuciones.
- Los perfiles privados de organizaciones viven fuera del repo y no quedan alcanzados por la licencia del código.
