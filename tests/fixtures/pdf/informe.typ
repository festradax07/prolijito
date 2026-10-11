// Informe ficticio para probar prolijito de punta a punta. Contenido propio, sin datos reales.
// El interlineado se elige al compilar: --input leading=0.95em (1,5 medido) o 0.65em (simple).
#let leading = eval(sys.inputs.at("leading", default: "0.95em"))

#set document(title: "Informe de prueba")
#set page(paper: "a4", margin: 2.5cm, numbering: "1")
#set text(lang: "es", size: 12pt)
#set par(justify: true, leading: leading, spacing: leading + 0.6em)
#set heading(numbering: "1.")

// ---------- carátula ----------
#align(center)[
  #v(4cm)
  #text(size: 20pt, weight: "bold")[Informe técnico de prueba]
  #v(1cm)
  #text(size: 14pt)[Sistema de monitoreo de consumo eléctrico]
  #v(3cm)
  Grupo de ejemplo
  #v(0.5cm)
  Integrante A · Integrante B
  #v(0.5cm)
  1 de enero de 2026
]
#pagebreak()

// ---------- índice ----------
#outline(title: [Índice])
#pagebreak()

#let parrafo = [
  El sistema registra el consumo eléctrico de cada circuito de un edificio y presenta los datos en
  un panel web que se actualiza cada minuto. La medición se realiza con sensores de corriente no
  invasivos conectados a un microcontrolador, que envía las lecturas a un servidor central por
  medio de una red inalámbrica. El servidor almacena las series de tiempo, calcula promedios por
  hora y por día, y genera alertas cuando un circuito supera el umbral configurado para su uso
  habitual. Este documento describe el alcance del proyecto, la arquitectura propuesta, el plan de
  pruebas y los resultados obtenidos durante la etapa de validación en el laboratorio.
]

= Introducción
#parrafo
#parrafo
#parrafo

= Arquitectura
#parrafo
#parrafo

== Hardware
#parrafo
#parrafo

== Software
#parrafo
#parrafo

= Pruebas y resultados
#parrafo
#parrafo
#parrafo

= Conclusiones
#parrafo
#parrafo

#heading(numbering: none)[Bibliografía]

Autor de ejemplo. _Medición de corriente con sensores no invasivos._ Editorial de ejemplo, 2024.

Organización de ejemplo. _Guía de redes inalámbricas para sensores._ Consultado el 1 de enero de 2026.
