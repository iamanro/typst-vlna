#!/usr/bin/env python3
"""Generate a deterministic Czech benchmark document where every vlna rule fires."""
import random
import sys

PARA_COUNT = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

SENTENCES = [
    "Šel k lesu a v něm se u potoka na kopci o vše rozdělil se svým bratrem.",
    "Členění čísel je 2 500, 1 000 000 a 25,325 23, což se nikdy nezalomí.",
    "Číslo a značka: 50 %, § 23, \\* 1921, † 2000 zůstávají pohromadě.",
    "Číslo a jednotka: 5 str., 8 hod., s. 53, č. 9, obr. 1, tab. 3, 100 m², 10 kg.",
    "Teplota 19 °C, cena 1 000 000 Kč, částka 250 €, proud 200 µA, disk 12 MiB.",
    "Telefon +420 800 123 987, dále 723 456 789 a 800 11 22 33 v jednom bloku.",
    "Datum 21. 6. 2024 a 16. ledna 1972 drží den s měsícem pohromadě.",
    "Mapa v měřítku 1 : 50 000, poměr hlasů 5 : 3 a dělení 10 : 2 = 5.",
    "Firma a. s. i s. r. o., mn. č., př. n. l., T. G. M., PS PČR, FF UK, ČSN 01 6910.",
    "Válka 1948–1989 skončila, pomlčka s mezerami – ta zůstává na konci řádku.",
    "Psali Fr. Daneš a M. Těšitelová o tzv. klikání v odborném textu.",
    "Tituly: prof. Ing. arch. Novák, Jan Novák, Ph.D., a dále Ing. B. Novák.",
    "Interakce: stálo to o 2 500 Kč víc, akce od 21. 6. 2024, výška u 19 °C.",
    "Uvedl to plk. gšt. doc. Mgr. et Mgr. Ing. Libor Kutěj na semináři v Brně.",
    "Viz tabulka 3 na straně 12, kde je uvedeno 500 lidí a 5. pluk armády.",
    "Pan Ing. Karel Malý, CSc., pracoval u nás od 1. 9. 2019 do 30. 6. 2024.",
    "Zpráva ÚJČ AV ČR uvádí, že norma ČSN EN ISO 9001 platí i pro s. r. o.",
    "Podle odst. 2 a např. kap. 4 je nutné dodržet postup dle obr. 7 a tab. 9.",
    "Rychlost 130 km/h při 50 Hz a výkon 2 kW se měřily po 15 min v laboratoři.",
    "Ceny vzrostly o 12,5 % na 1 250 Kč za kus, tj. o 150 Kč více než v r. 2023.",
]

WORDS = [
    "text", "dokument", "sazba", "řádek", "odstavec", "kniha", "stránka",
    "písmo", "zlom", "mezera", "slovo", "věta", "kapitola", "tabulka",
    "obrázek", "norma", "pravidlo", "jazyk", "překlad", "korektura",
]
SHORT = ["k", "s", "v", "z", "o", "u", "a", "i", "na", "do", "po", "se", "je"]

rng = random.Random(20260901)
out = []
for i in range(PARA_COUNT):
    if i % 25 == 0:
        out.append(f"= Kapitola {i // 25 + 1} — sazba k lesu a 2 500 Kč\n")
    n = rng.randint(4, 7)
    parts = [rng.choice(SENTENCES) for _ in range(n)]
    tail = " ".join(
        f"{rng.choice(SHORT)} {rng.choice(WORDS)}" for _ in range(rng.randint(3, 8))
    )
    parts.append(f"Dále {tail} a konec odstavce.")
    out.append(" ".join(parts) + "\n")

body = "\n".join(out)
print(body, end="")
