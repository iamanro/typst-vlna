#!/usr/bin/env python3
"""Render each configuration with old (0.3.0) and new lib; compare rendered pages."""
import os
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops

# Both libraries to compare, and a scratch directory for the renderings.
OLD = Path(os.environ.get("VLNA_OLD_LIB", "/tmp/vlna-bench/versions/0.3.0/lib.typ"))
NEW = Path(os.environ.get("VLNA_NEW_LIB", Path(__file__).resolve().parents[2] / "lib.typ"))
WORK = Path(os.environ.get("VLNA_BENCH_DIR", "/tmp/vlna-bench")) / "verify"

SAMPLE = (
    "Šel k lesu a v něm, o 2 500 Kč, od 21. 6. 2024, i s. r. o., zápas o 5 : 3, "
    "1948–1989, tzv. klikání, M. J. Hegel, prof. Ing. arch. Novák, Jan Novák, Ph.D., "
    "50 %, § 23, 19 °C, 1 000 000 Kč, ČSN 01 6910, PS PČR, viz tab. 3, s. 12, "
    "pomlčka s mezerami – ta zůstává, +420 800 123 987, 16. ledna 1972."
)

CASES = {
    # fast path (no raw, no toggles)
    "plain": f"#show: apply-vlna\n{SAMPLE}\n",
    "debug": f"#show: apply-vlna.with(debug: true)\n{SAMPLE}\n",
    "number-word": f"#show: apply-vlna.with(number-word: true)\nPřišlo 500 lidí na 5. pluk, viz strana 2, Karel IV. {SAMPLE}\n",
    "one-letter": f"#show: apply-vlna.with(bind-two-letter-words: false)\n{SAMPLE}\n",
    "explicit-set": f'#show: apply-vlna.with(short-words: "vksuozVKSUOZAI")\n{SAMPLE}\n',
    "word-array": f'#show: apply-vlna.with(short-words: ("v", "k", "na", "Na"))\n{SAMPLE}\n',
    "all-off": (
        "#show: apply-vlna.with(short-words: none, initials: false, titles: false, "
        "numbers: false, ratios: false, dates: false, abbreviations: false, "
        f"dashes: false, links: false)\n{SAMPLE}\n"
    ),
    "narrow": f"#show: apply-vlna\n#box(width: 30mm)[{SAMPLE}]\n",
    "links": (
        "#show: apply-vlna\n#box(width: 24mm)[\n"
        '#link("https://a.example.com//b//c/d?x=1&y=2\\#frag~tilde_under%20pct")\n'
        '#link("mailto:a@b.cz")[a\\@b.cz]\n'
        '#link("https://x.com/SenatCZ")[\\@SenatCZ]\n]\n'
    ),
    # per-language sets: context kept even on the fast path
    "lang-dict": (
        '#show: apply-vlna.with(short-words: (cs: "AIiVvOoUuSsZzKk", sk: "AIiVvOoUuSsZzKk"))\n'
        f"{SAMPLE}\n\n#text(lang: \"en\")[a trip to a lake with i and v words]\n"
        '\n#text(lang: "sk")[išli sme k jazeru a v ňom]\n'
    ),
    "lang-forced": (
        '#show: apply-vlna.with(short-words: (cs: "AIiVvOoUuSsZzKk"), lang: "cs")\n'
        '#text(lang: "en")[A trip with v word binds too.]\n'
    ),
    # dynamic path: raw and mid-document toggles
    "raw": f"#show: apply-vlna\n{SAMPLE}\n\n`k lesu 2 500 Kč`\n\n```\nk lesu\na. s. 1 : 2\n```\n",
    "toggles": (
        "#import lib: vlna-on, vlna-off\n#show: apply-vlna\n"
        f"Váže: k lesu a 50 %. #vlna-off() Neváže: k lesu, 2 500 Kč, 21. 6. #vlna-on() Zase: k lesu. {SAMPLE}\n"
    ),
    "debug-toggles": (
        "#import lib: vlna-debug-on, vlna-debug-off\n#show: apply-vlna\n"
        f"Bez: k lesu. #vlna-debug-on() S rámečky: k lesu a v něm. #vlna-debug-off() Zase bez: k lesu. {SAMPLE}\n"
    ),
    "raw-and-toggles": (
        "#import lib: vlna-off, vlna-on\n#show: apply-vlna\n"
        f"{SAMPLE} #vlna-off() nic: k lesu #vlna-on()\n\n`k lesu`\n"
    ),
    "nested-scopes": (
        "#show: apply-vlna\n"
        f"vnější: {SAMPLE}\n\n#[#show: apply-vlna.with(debug: true); vnitřní: {SAMPLE}]\n"
        f"\n#[#show: apply-vlna.with(units: ()); bez jednotek: {SAMPLE}]\n"
    ),
    # raw produced only during layout: the pre-layout scan cannot see it,
    # the document-level query must still catch it
    "late-raw-context": (
        f"#show: apply-vlna\n{SAMPLE}\n\n#context [`k lesu 2 500 Kč`]\n"
    ),
    "late-raw-show": (
        "#show: apply-vlna\n#show heading: it => raw(\"k lesu 2 500 Kč\")\n"
        f"= Nadpis\n\n{SAMPLE}\n"
    ),
    # Narrow measures: separate rules nest, so an oversized outer box still
    # protects the number group / date / dash inside it. A single merged rule
    # cannot, and broke "1 000 000" into "1 000 | 000" here.
    "narrow-12mm": (
        "#set page(width: 12mm, margin: 1mm)\n#set par(justify: false)\n"
        "#show: apply-vlna\ncena o 1 000 000 Kč celkem\n\ntermín od 21. 6. 2024\n"
        "\npomlčka s mezerami – ta\n"
    ),
    "narrow-16mm": (
        "#set page(width: 16mm, margin: 1mm)\n#set par(justify: false)\n"
        "#show: apply-vlna\ncena o 1 000 000 Kč celkem\n\ntermín od 21. 6. 2024\n"
        "\npomlčka s mezerami – ta\n"
    ),
    "narrow-20mm-justified": (
        "#set page(width: 20mm, margin: 1mm)\n#show: apply-vlna\n"
        "cena o 1 000 000 Kč celkem\n\nmapa 1 : 50 000 a firma a. s. i s. r. o.\n"
        "\ntelefon +420 800 123 987 platí\n"
    ),
    "narrow-table-cell": (
        "#show: apply-vlna\n"
        "#table(columns: (14mm, 14mm), [cena o 1 000 000 Kč], [od 21. 6. 2024],\n"
        "  [mapa 1 : 50 000], [text s mezerami – ta])\n"
    ),
    # Units carrying regex metacharacters, on top of the exported default list.
    "units-meta": (
        "#show: apply-vlna.with(units: default-units + "
        '("m/s", "Kč/ks", "m^2", "(ks)", "a|b", "$"))\n'
        "rychlost 12 m/s, cena 30 Kč/ks, plocha 5 m^2, počet 7 (ks), "
        f"volba 3 a|b, suma 9 \\$.\n{SAMPLE}\n"
    ),
    # The toggles must not inject anything queryable into the user's document.
    "no-metadata-leak": (
        "#import lib: vlna-off, vlna-on\n#show: apply-vlna\n"
        f"{SAMPLE} #vlna-off() nic: k lesu #vlna-on() zase: k lesu\n"
        "\n#context [METADATA: #query(metadata).len()]\n"
    ),
}

HEAD = """#import "{lib}" as lib
#import "{lib}": apply-vlna, default-units
#set text(lang: "cs", size: 9pt)
#set page(width: 120mm, height: auto, margin: 5mm)
#set par(justify: true)
"""


def render(lib, name, src, tag):
    """Compile a case; return (word-box dump, page rasters, stderr)."""
    d = WORK / tag
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{name}.typ"
    f.write_text(HEAD.format(lib=lib) + src)
    pdf = d / f"{name}.pdf"
    r = subprocess.run(
        ["typst", "compile", "--root", "/", str(f), str(pdf)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return None, None, r.stderr.strip()[:400]
    subprocess.run(["pdftotext", "-bbox", str(pdf), str(d / f"{name}.xml")], check=True)
    subprocess.run(
        ["typst", "compile", "--root", "/", str(f),
         str(d / f"{name}-{{p}}.png"), "--ppi", "150"],
        capture_output=True, text=True, check=True,
    )
    pages = [Image.open(p).convert("RGB") for p in sorted(d.glob(f"{name}-*.png"))]
    return words(d / f"{name}.xml"), pages, r.stderr.strip()


def words(xml):
    """Every word with its position, rounded to 1/1000 pt (~0.35 µm)."""
    return [
        (m.group(5), *(round(float(m.group(i)), 3) for i in range(1, 5)))
        for m in re.finditer(
            r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>',
            xml.read_text(),
        )
    ]


def raster_delta(old, new):
    """(max channel delta, share of differing pixels) over all pages."""
    if len(old) != len(new) or any(a.size != b.size for a, b in zip(old, new)):
        return 255, 1.0
    worst, diff, total = 0, 0, 0
    for a, b in zip(old, new):
        total += a.size[0] * a.size[1]
        for count, value in ImageChops.difference(a, b).convert("L").getcolors(1 << 16):
            if value:
                worst = max(worst, value)
                diff += count
    return worst, diff / total


fails = 0
for name, src in CASES.items():
    xo, ro, eo = render(OLD, name, src, "old")
    xn, rn, en = render(NEW, name, src, "new")
    if xo is None or xn is None:
        print(f"{name:>16}  COMPILE FAILED\n    old: {eo}\n    new: {en}")
        fails += 1
        continue
    worst, share = raster_delta(ro, rn)
    # Every word in the same place, and the rendering — debug frames included
    # — the same up to antialiasing rounding.
    ok = xo == xn and worst <= 2 and share < 0.001
    fails += 0 if ok else 1
    print(
        f"{name:>20}  {'same' if ok else 'DIFFERENT'}"
        f"  {len(xo)} words {'in identical places' if xo == xn else 'MOVED'}"
        f"  raster Δmax {worst}/255 on {share * 100:.4f}% of pixels"
    )
print(f"\n{len(CASES) - fails}/{len(CASES)} configurations typographically identical")
sys.exit(1 if fails else 0)
