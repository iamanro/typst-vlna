#!/usr/bin/env python3
"""Bar chart of p95 compile time per vlna version (501-page Czech document)."""
import json
import os
import subprocess
from pathlib import Path

# Without $VLNA_BENCH_DIR the committed dataset next to this script is used,
# so the published chart can be redrawn without re-running the benchmark.
ROOT = Path(os.environ.get("VLNA_BENCH_DIR") or Path(__file__).resolve().parent)
RAW = json.loads((ROOT / "results.json").read_text())
# bench.py writes {runs, cores, threads, series: {...}}; accept a bare
# series map too, so an older results.json still charts.
DATA = RAW.get("series", RAW)

ORDER = [
    ("no vlna", "bare document (reference)", "#9aa3ad"),
    ("0.1.1", "v0.1.1", "#c2504a"),
    ("0.2.0", "v0.2.0", "#d99a2b"),
    ("0.3.0", "v0.3.0", "#4a7fc2"),
    ("optimised", "v0.4.0", "#2e9e5b"),
    ("0.3.0-raw", "v0.3.0 · same doc + a raw block", "#9dbbe0"),
    ("optimised-raw", "v0.4.0 · same doc + a raw block", "#7fbf95"),
]
rows = [(lbl, name, col, DATA[lbl]) for lbl, name, col in ORDER if lbl in DATA]

W, H = 980, 84 + 52 * len(rows) + 92
PAD_L, PAD_R, PAD_T = 250, 160, 84
plot_w = W - PAD_L - PAD_R
top = max(r[3]["p95"] for r in rows)
scale = plot_w / (top * 1.06)
base = DATA["no vlna"]["p95"]

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
    f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
    '<style>text{font-family:"DejaVu Sans",Arial,sans-serif}</style>',
    f'<text x="28" y="36" font-size="19" font-weight="700" fill="#1b1f24">'
    f'vlna: compile time p95 — 501-page Czech document</text>',
    f'<text x="28" y="58" font-size="12.5" fill="#5b6570">'
    f'typst 0.15.0 · {rows[0][3]["runs"]} interleaved runs per version after 2 '
    f'warm-ups · pinned to 8 cores · all rule groups firing · lower is better</text>',
]

# vertical grid
step = 2 if top < 16 else 5
t = 0
while t <= top * 1.06:
    x = PAD_L + t * scale
    svg.append(f'<line x1="{x:.1f}" y1="{PAD_T - 8}" x2="{x:.1f}" y2="{PAD_T + 52 * len(rows) - 16}" '
               f'stroke="#e6e9ec" stroke-width="1"/>')
    svg.append(f'<text x="{x:.1f}" y="{PAD_T + 52 * len(rows) + 2}" font-size="11" '
               f'fill="#8b949e" text-anchor="middle">{t}s</text>')
    t += step

for i, (lbl, name, col, r) in enumerate(rows):
    y = PAD_T + 52 * i
    w = r["p95"] * scale
    stalls = len([x for x in r["times"] if x > r["p50"] * 1.10])
    svg += [
        f'<text x="{PAD_L - 14}" y="{y + 21}" font-size="13.5" fill="#1b1f24" '
        f'text-anchor="end">{name}</text>',
        f'<rect x="{PAD_L}" y="{y}" width="{w:.1f}" height="30" rx="3" fill="{col}"/>',
        f'<text x="{PAD_L + w + 10}" y="{y + 21}" font-size="13" font-weight="700" '
        f'fill="#1b1f24">{r["p95"]:.2f}s</text>',
    ]
    factor = r["p95"] / base
    note = (
        "1.00x (reference)" if lbl == "no vlna" else f"{factor:.2f}x the bare document"
    )
    svg.append(f'<text x="{PAD_L - 14}" y="{y + 38}" font-size="11" fill="#8b949e" '
               f'text-anchor="end">{note} · p50 {r["p50"]:.2f}s</text>')
    # min-max whisker, plus a tick at p50: the gap between the tick and the
    # bar end is the stall tail, not the package.
    x0, x1 = PAD_L + r["min"] * scale, PAD_L + r["max"] * scale
    xm = PAD_L + r["p50"] * scale
    svg.append(f'<line x1="{x0:.1f}" y1="{y + 15}" x2="{x1:.1f}" y2="{y + 15}" '
               f'stroke="#ffffff" stroke-opacity="0.75" stroke-width="1.5"/>')
    svg.append(f'<line x1="{xm:.1f}" y1="{y + 4}" x2="{xm:.1f}" y2="{y + 26}" '
               f'stroke="#1b1f24" stroke-opacity="0.55" stroke-width="2"/>')
    if stalls:
        svg.append(f'<text x="{PAD_L + w + 66}" y="{y + 21}" font-size="10.5" '
                   f'fill="#8b949e">{stalls}/{r["runs"]} stalled</text>')

y = PAD_T + 52 * len(rows) + 26
opt, old = DATA.get("optimised"), DATA.get("0.3.0")
if opt and old:
    gain = (1 - opt["p95"] / old["p95"]) * 100
    ovh = (opt["p95"] - base) / (old["p95"] - base)
    svg.append(
        f'<text x="28" y="{y + 12}" font-size="12.5" fill="#2e5b3d">'
        f'v0.4.0 vs v0.3.0: {gain:.0f}% faster p95 '
        f'({old["p95"]:.2f}s → {opt["p95"]:.2f}s).</text>'
    )
    svg.append(
        f'<text x="28" y="{y + 30}" font-size="12.5" fill="#5b6570">'
        f'Package overhead above the bare document: '
        f'{old["p95"] - base:.2f}s → {opt["p95"] - base:.2f}s '
        f'({ovh * 100:.0f}% of what it was). White line = min–max spread, dark tick = p50.</text>'
    )
svg.append("</svg>")
out = ROOT / "p95.svg"
out.write_text("\n".join(svg))
print(out)

# A PNG next to the SVG: README images are proxied by GitHub, and the proxy
# is reliable for raster formats only. typst is already a prerequisite here.
png = ROOT / "p95.png"
wrap = ROOT / "p95-wrap.typ"
wrap.write_text(
    f'#set page(width: auto, height: auto, margin: 0pt)\n#image("{out.name}")\n'
)
subprocess.run(
    ["typst", "compile", "--format", "png", "--ppi", "192", str(wrap), str(png)],
    check=True,
)
wrap.unlink()
print(png)
for lbl, name, _, r in rows:
    print(f"{name:>34}  p95 {r['p95']:6.3f}s  p50 {r['p50']:6.3f}s  "
          f"min {r['min']:6.3f}s  max {r['max']:6.3f}s  n={r['runs']}")
