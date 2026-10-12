# Avisos de terceros

## Medidor de PDF y rúbrica de Taller de Proyecto II (UNLP)

prolijito incluye código y documentación derivados del repositorio de la cátedra
**Taller de Proyecto II** (Ingeniería en Computación, Universidad Nacional de La Plata):
[tpII/ia-guidelines-taller](https://github.com/tpII/ia-guidelines-taller), carpeta
`skills/formato-entregas/`, commit `65d22589d03b9b40e02ec1d8505abccd3a4f90f1`.

- `src/prolijito/adapters/pdf/` es un fork de `analizar_pdf.py`: el mismo método de medición sobre
  poppler, reorganizado en módulos, con tipos y tests, sin la norma de TP2 fija en el código y con
  mejoras propias (ver `docs/adr/0008-fork-del-medidor-de-la-catedra.md`).
- `profiles/normas/unlp-tp2-rubrica.md` es la rúbrica de la cátedra, sin modificaciones. Es la
  fuente del perfil `unlp-tp2`.

Gracias a la cátedra por publicar estas herramientas. Esas partes se distribuyen bajo su licencia
original:

```
MIT License

Copyright (c) 2026 Taller de Proyecto 2

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
