#!/usr/bin/env python3
"""Line-break regression test: units that vlna glues must never split.

Each case is set after filler of varying length in pages swept from 55 mm to
90 mm, so the line break lands in every gap of the unit at some width. A unit
"splits" when its words end up on different lines in the PDF text.

    python3 tests/breaks.py        (needs typst and pdftotext on PATH)
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIDTHS = [55 + i / 2 for i in range(71)]  # 55–90 mm by 0.5 mm
FILLER = "Text slovo pokračuje dál"

# (options for apply-vlna, unit that must stay on one line)
CASES = [
    ("", "písm. a)"),  # #2
    ("", "čl. 5"),
    ("legal: true", "sp. zn. 12 Nt 345/2026"),
    ("legal: true", "4 Tdo 123/2025"),
    ("legal: true", "2 KZV-12/2026"),
    ("legal: true", "VZV 23/2026-22"),
    ("legal: true", "I. ÚS 2438/25"),
    ("legal: true", "Pl. ÚS 45/04"),
    ("legal: true", "KRPA-12345-67/TČ-2026-000089"),
    ("legal: true", "19-1234567890/0100"),
    ("legal: true", "VINITIS s.r.o."),
    ("legal: true", "ABC a. s."),
    ("legal: true", "č. 89/2012 Sb."),
    ("legal: true", "2/1993 Sb. m. s."),
    ("legal: true", "zák. práce"),
    ("legal: true", "věty první"),
    ("legal: true", "bodu 3"),
    ("legal: true", "a sp. zn. 12 Nt 345/2026"),  # chained after a short word
]
# Without `legal` these must still break somewhere — proves both that the
# switch is opt-in and that the sweep actually reaches every gap.
BREAKABLE = [("", "sp. zn. 12 Nt 345/2026"), ("", "VINITIS s.r.o.")]


def lines(opts, unit):
    """PDF text of `unit` after filler, one page per width."""
    pages = "\n".join(
        f"#page(width: {w}mm)[{FILLER} {FILLER[: i % len(FILLER)]} {unit} konec.]"
        for i, w in enumerate(WIDTHS)
    )
    src = (
        '#import "/lib.typ": apply-vlna\n'
        '#set page(height: auto, margin: 2mm)\n#set text(lang: "cs", size: 10pt)\n'
        f"#show: apply-vlna.with({opts})\n{pages}\n"
    )
    with tempfile.TemporaryDirectory(dir=ROOT) as d:
        typ, pdf = Path(d) / "t.typ", Path(d) / "t.pdf"
        typ.write_text(src)
        subprocess.run(["typst", "compile", "--root", ROOT, typ, pdf], check=True)
        out = subprocess.run(["pdftotext", pdf, "-"], check=True, capture_output=True, text=True)
    return out.stdout.split("\f")[: len(WIDTHS)]


fails = 0
for opts, unit in CASES:
    split = [w for w, page in zip(WIDTHS, lines(opts, unit)) if unit not in page]
    if split:
        fails += 1
        print(f"FAIL {unit!r} ({opts or 'defaults'}) splits at {split[:5]} mm")
for opts, unit in BREAKABLE:
    if all(unit in page for page in lines(opts, unit)):
        fails += 1
        print(f"FAIL {unit!r} ({opts or 'defaults'}) never breaks — sweep too coarse?")
print(f"{len(CASES) + len(BREAKABLE) - fails}/{len(CASES) + len(BREAKABLE)} passed")
sys.exit(1 if fails else 0)
