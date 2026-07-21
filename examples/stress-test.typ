// Zátěžový test balíčku vlna — všechna pravidla, krajní případy, zákeřné
// vstupy i degenerované konfigurace. Kompilace nesmí spadnout, zacyklit se
// ani hlásit nekonvergující layout; rámečky (debug) ukazují, co se slepilo.
//
//   typst compile --root .. stress-test.typ stress-test.pdf

#import "../lib.typ": apply-vlna, default-units, vlna-on, vlna-off, vlna-debug-on, vlna-debug-off

#set text(lang: "cs", size: 9pt)
#set page(width: 185mm, height: auto, margin: 6mm)
#set par(justify: true)

#let sample = [Šel k lesu a v něm, 2 500 Kč, 21. 6. 2024, a. s., 1 : 2, 1948–1989, tzv. klikání, M. Novák.]

= 1 — Pravidla ÚJČ (debug)

#[
  #show: apply-vlna.with(debug: true)
  Členění čísel: 2 500, 1 000 000, 25,325 23. Číslo a značka: 50 %, § 23, \# 26, \* 1921, † 2000.
  Číslo a jednotka: 5 str., 8 hod., s. 53, č. 9, obr. 1, tab. 3, 100 m², 10 kg, 16 h, 19 °C, 1 000 000 Kč, 250 €, 200 µA, 12 MiB, 100.5 kJ.
  Telefon: +420 800 123 987, 723 456 789, 800 11 22 33.
  Datum: 21. 6. 2024 a 16. ledna 1972. Mapa v měřítku 1 : 50 000, poměr hlasů 5 : 3, dělení 10 : 2 = 5.
  Firma a. s. i s. r. o., mn. č., př. n. l., T. G. M., PS PČR, FF UK, ČSN 01 6910, ÚJČ AV ČR, ČSN EN ISO 9001.
  Válka 1948–1989 skončila, pomlčka s mezerami – ta zůstává na konci řádku.
  Psali Fr. Daneš a M. Těšitelová, tzv. klikání. Tituly: prof. Ing. arch. Novák, Jan Novák, Ph.D., Ing. B. Novák.
  Interakce: stálo to o 2 500 Kč víc, akce od 21. 6. 2024, výška u 19 °C, zápas o 5 : 3.
]

= 2 — Volby krátkých slov

#[
  #show: apply-vlna.with(bind-two-letter-words: false, debug: true)
  Jen jednopísmenná: k lesu a v něm jsem se u potoka na kopci o vše rozdělil.
]
#[
  #show: apply-vlna.with(short-words: "vksuozVKSUOZAI", debug: true)
  Přesná sada: k lesu a v něm se u potoka, a EU i AI zůstávají volné.
]
#[
  #show: apply-vlna.with(short-words: ("v", "k", "na", "Na"), debug: true)
  Pole slov: k lesu, v něm, na kopci, ale u potoka a o vše volně.
]

= 3 — Jazykové sady a vynucený jazyk

#[
  #show: apply-vlna.with(short-words: (cs: "AIiVvOoUuSsZzKk", sk: "AIiVvOoUuSsZzKk"), debug: true)
  Česky: šel k lesu a v něm se o vše rozdělil.
  #text(lang: "en")[English: a trip to a lake with i and v words stays untouched.]
  #text(lang: "sk")[Slovensky: išli sme k jazeru a v ňom.]
]
#[
  #show: apply-vlna.with(short-words: (cs: "AIiVvOoUuSsZzKk"), lang: "cs", debug: true)
  Vynuceně česká sada: #text(lang: "en")[A trip with v word binds too.]
]

= 4 — Zákeřné vstupy

#[
  #show: apply-vlna.with(debug: true)

  *Řetězení:* k k k k k k k k k k slovo. a a a a a a a a konec.

  *Laviny:* 1 2 3 4 5 6 7 8 9 10. a. b. c. d. e. f. konec. I. I. I. I. patro. AB CD EF 12 34.

  *Unicode:* k 😀 a שלום, v 中文 slovo, k módě, k Ǆungle.

  *Hranice stylů (neváže se — dokumentované omezení):* k *lesu* a _v_ něm.

  *Raw se nezpracovává:* `Šel k lesu, 2 500 Kč, a. s.` #raw(block: true, "k lesu 2 500 Kč\na. s. 1 : 2")

  *Matematika se nezpracovává:* $k = 2 500$ a $x : y = 1 : 2$, ale text k $a$ se váže.

  *Interpunkce:* (k lesu), „v něm", [s bratrem], {o vše}, „50 %"?!

  *Pomlčky:* a–b–c–d, x – y – z – w.

  == Nadpis k lesu a 2 500 Kč
  - položka k lesu
  - 21. 6. 2024 a. s.
  #table(columns: 2, [k lesu], [2 500 Kč], [a. s.], [1 : 50 000])
  Text#footnote[Poznámka k lesu, 2 500 Kč.] pokračuje.
]

= 5 — Adresy v úzkém sloupci (22 mm)

#box(width: 22mm, stroke: .3pt + gray, inset: 1mm)[
  #show: apply-vlna
  #link("https://a.example.com//b//c/d?x=1&y=2#frag~tilde_under%20pct")
  #link("mailto:a@b.cz")[a\@b.cz]
  #link("https://www.cr2030.cz/strategie")
  účet #link("https://x.com/SenatCZ")[\@SenatCZ] se za \@ nezalomí.
]

= 6 — Krajně úzká sazba (30 mm)

#box(width: 30mm, stroke: .3pt + gray, inset: 1mm)[
  #show: apply-vlna.with(debug: true)
  Text v nejneobhospodařovávatelnějšímu pokračuje k pseudopseudohypoparathyroidismus konci.
]

= 7 — Degenerované konfigurace (nesmí spadnout)

#[#show: apply-vlna.with(short-words: none, initials: false, titles: false, numbers: false, ratios: false, dates: false, abbreviations: false, dashes: false, links: false); Vše vypnuto: #sample]
#[#show: apply-vlna.with(units: ()); Prázdné units: #sample]
#[#show: apply-vlna.with(months: ()); Prázdné months: #sample]
#[#show: apply-vlna.with(compound-initials: ()); Prázdné compound-initials: #sample]
#[#show: apply-vlna.with(short-words: ""); Prázdný řetězec: #sample]
#[#show: apply-vlna.with(short-words: ()); Prázdné pole: #sample]
#[#show: apply-vlna.with(short-words: (:)); Prázdný slovník: #sample]
#[#show: apply-vlna.with(units: ("$", "(x)", "a|b", "m^2", "[u]")); Metaznaky v units: 5 \$ a 3 (x) a 1 a|b.]
#[#show: apply-vlna.with(units: default-units + default-units); Duplicitní units: #sample]
#[#show: apply-vlna.with(short-words: none, initials: false, titles: false, numbers: false, ratios: false, dates: false, abbreviations: false, dashes: false, number-word: true); Jen number-word: Přišlo 500 lidí na 5. pluk, viz strana 2, Karel IV.]

= 8 — Přepínání uprostřed dokumentu

// Poslední sekce: stavy jsou globální pro celý dokument, #vlna-debug-off()
// by jinak vypnul rámečky všem následujícím sekcím.
#[
  #show: apply-vlna.with(debug: true)
  Váže se: k lesu a 50 %. #vlna-off() Nic se neváže: k lesu, 2 500 Kč, 21. 6. #vlna-on() A zase: k lesu.
]
#[
  #show: apply-vlna
  Bez rámečků: k lesu. #vlna-debug-on() S rámečky: k lesu a v něm. #vlna-debug-off() Zase bez: k lesu.
]
