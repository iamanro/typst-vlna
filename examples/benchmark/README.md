# Benchmark and equivalence harness

The compile-time figures in the main README come from these four scripts, and
`p95.svg` is the chart they produce. Everything writes to `$VLNA_BENCH_DIR`
(default `/tmp/vlna-bench`).

## Set up

```sh
export VLNA_BENCH_DIR=/tmp/vlna-bench
mkdir -p "$VLNA_BENCH_DIR/versions"

# one worktree per version you want to compare
for v in 0.1.1:d93be1a 0.2.0:v0.2.0 0.3.0:v0.3.0; do
  git worktree add "$VLNA_BENCH_DIR/versions/${v%%:*}" "${v##*:}"
done
mkdir -p "$VLNA_BENCH_DIR/versions/optimised"
cp lib.typ "$VLNA_BENCH_DIR/versions/optimised/"

# 5740 paragraphs of Czech text where every rule group fires = 501 A4 pages
python3 examples/benchmark/gen.py 5740 > "$VLNA_BENCH_DIR/body.typ"

# the two `-raw` series: the same document with one raw block appended.
# Run this AFTER the drivers below exist in versions/0.3.0 and versions/optimised.
for v in 0.3.0 optimised; do
  d="$VLNA_BENCH_DIR/versions/$v-raw"
  mkdir -p "$d"
  cp "$VLNA_BENCH_DIR/versions/$v/lib.typ" "$d/"
  cp "$VLNA_BENCH_DIR/versions/$v/head-on.typ" "$d/"
  { cat "$VLNA_BENCH_DIR/body.typ"; printf '\n`kód`\n'; } > "$d/body.typ"
done
```

Each version directory needs `body.typ` plus two drivers: `head-on.typ`
(`#show: apply-vlna` + `#include "body.typ"`) and `head-off.typ` (the same
without the package), both with `#set text(lang: "cs", size: 10pt)`,
`#set page(paper: "a4", margin: 2cm)` and `#set par(justify: true)`.

## Measure

```sh
python3 examples/benchmark/bench.py 25 0.1.1 0.2.0 0.3.0 optimised 0.3.0-raw optimised-raw
python3 examples/benchmark/chart.py   # writes $VLNA_BENCH_DIR/p95.svg
```

The committed figures come from exactly that command. With `$VLNA_BENCH_DIR`
unset, `chart.py` reads the committed `results.json` beside it and redraws
the published `p95.svg`.

`bench.py` runs the versions round-robin, so machine drift hits all of them
equally, and pins every compile to the same 8 cores with the same thread
count — unpinned wall time swings by seconds when a browser is busy, which
is enough to reorder the versions.

## Prove the typography did not change

```sh
VLNA_OLD_LIB=$VLNA_BENCH_DIR/versions/0.3.0/lib.typ \
  python3 examples/benchmark/equivalence.py
```

24 configurations are rendered with both libraries and compared two ways:
every word position from `pdftotext -bbox`, rounded to 1/1000 pt, must be
identical, and the page rasters may differ only by antialiasing rounding.
Narrow measures (12–20 mm) are in the set on purpose — that is where a glued
group is wider than the line, and where an unsound optimisation shows up as a
broken number group or date.

Requires `typst`, `python3` with Pillow, `pdftotext` (poppler) and `taskset`.
