// README hero image: the same paragraph without and with vlna.
//   typst compile --root .. --ppi 200 hero.typ hero.png
#import "../lib.typ": apply-vlna

#set page(width: 170mm, height: auto, margin: 6mm, fill: white)
#set text(lang: "cs", size: 10pt, font: "Libertinus Serif")
#set par(justify: true)

#let sample = [
  Schůzka se koná 21. 6. 2024 v 9 h v Praze a vstupné je 1 500 Kč. Přednáší
  prof. Ing. Jan Novák, Ph.D., o vlivu teploty 19 °C na úrodu a v diskusi
  vystoupí i M. J. Hegel s kolegy z ČSN 01 6910. Podle § 234 odst. 4 písm. a)
  jde o věc sp. zn. 12 Nt 345/2026.
]
#let column(title, body) = block(width: 100%)[
  #text(size: 8pt, weight: "bold", fill: luma(110), tracking: 0.08em, upper(title))
  #v(-2pt)
  #line(length: 100%, stroke: 0.5pt + luma(200))
  #body
]

#grid(
  columns: (1fr, 1fr),
  column-gutter: 8mm,
  column("Plain Typst", block(width: 56mm, sample)),
  column("With vlna (debug frames on)", block(width: 56mm)[
    #show: apply-vlna.with(legal: true, debug: true)
    #sample
  ]),
)
