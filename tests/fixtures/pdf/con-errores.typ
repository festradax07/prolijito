// Informe ficticio con errores de formato a propósito, para probar las reglas de punta a punta.
// Contenido propio, sin datos reales. Errores: índice manual desactualizado, una entrada del
// índice sin título, tabla con epígrafe arriba y sin mencionar, primera persona, código en
// monoespaciada, sin bibliografía y sin índice de tablas.
#set document(title: "Informe con errores")
#set page(paper: "a4", margin: 2.5cm, numbering: "1")
#set text(lang: "es", size: 12pt)
#set par(justify: true, leading: 0.95em, spacing: 1.55em)
#set heading(numbering: "1.")
#show figure.where(kind: table): set figure.caption(position: top)

// ---------- carátula ----------
#align(center)[
  #v(4cm)
  #text(size: 20pt, weight: "bold")[Informe con errores de prueba]
  #v(1cm)
  #text(size: 14pt)[Estación meteorológica de bajo costo]
  #v(3cm)
  Grupo de ejemplo
  #v(0.5cm)
  1 de enero de 2026
]
#pagebreak()

// ---------- índice escrito a mano (desactualizado) ----------
#let entrada(titulo, pagina) = grid(columns: (auto, 1fr, auto), column-gutter: 4pt, titulo, repeat[.], pagina)
#heading(numbering: none, outlined: false)[Índice]
#entrada([1. Introducción], [1])
#entrada([2. Desarrollo], [1])
#entrada([3. Resultados], [3])
#entrada([4. Trabajo futuro], [4])
#pagebreak()

#let parrafo = [
  La estación mide temperatura, humedad y presión cada cinco minutos y publica las lecturas en
  un servidor central que las almacena como series de tiempo. El diseño prioriza el bajo costo
  y el consumo reducido, de modo que el equipo funcione con una batería pequeña y un panel solar
  durante varias semanas sin mantenimiento. Las lecturas se validan contra una estación de
  referencia ubicada en el mismo predio, y las diferencias se registran para calibrar los
  sensores antes de cada campaña de medición en el campo.
]

= Introducción
En este trabajo decidimos usar nuestro propio sensor de humedad para reducir el costo total.
#parrafo
#parrafo

= Desarrollo
#parrafo
#figure(
  table(
    columns: (1fr, 1fr, 1fr),
    [Componente], [Cantidad], [Costo],
    [Sensor], [3], [USD 20],
    [Placa], [1], [USD 15],
    [Fuente], [1], [USD 10],
  ),
  caption: [Materiales del prototipo],
)
#parrafo
El firmware lee los sensores con el siguiente bucle:
```
while true:
    temperatura = sensor_temperatura.leer()
    humedad = sensor_humedad.leer()
    presion = sensor_presion.leer()
    publicar(servidor, temperatura, humedad, presion)
    esperar(minutos=5)
```
#parrafo

= Resultados
#parrafo
#parrafo
#parrafo
