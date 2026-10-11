# 0003. Perfiles declarativos en YAML con herencia (`extends`)

- Estado: Aceptada
- Fecha: 2026-10-11

## Contexto
La herramienta apunta a entregas de facultad, informes de trabajo y papers. El script de la cátedra
tiene la norma de TP2 hardcodeada (fuentes, tamaño, umbrales). Cada nuevo tipo de documento no puede
requerir cambiar código.

## Opciones
- **A — Constantes en código por perfil**: simple / cada norma nueva es un PR de código.
- **B — Perfiles YAML planos**: datos / duplicación entre perfiles parecidos.
- **C — Perfiles YAML con `extends` (merge profundo, versionados por semver)**: datos sin duplicación / más complejo de resolver.

## Decisión
Se elige C desde el día uno, aunque el MVP tenga un solo perfil real: migrar de B a C después es más
caro que empezar con C.

## Consecuencias
- Hace falta esquema y tests de resolución de herencia.
- Los hijos referencian al padre por major (`@1`), así un cambio incompatible del padre no los rompe.
- Perfiles privados de organizaciones viven fuera del repo y se montan con `--profiles-dir`.
