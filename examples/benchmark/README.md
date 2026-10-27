# Benchmark and equivalence harness

The compile-time figures in the main README come from these scripts, and
`p95.svg` (plus the `p95.png` the main README embeds) is the chart they
produce. Everything writes to `$VLNA_BENCH_DIR` (default `/tmp/vlna-bench`).

## Measure

```sh
python3 examples/benchmark/bench.py                          # every series, under a minute
VLNA_BENCH_DIR=/tmp/vlna-bench python3 examples/benchmark/chart.py   # p95.svg + p95.png
```

`bench.py` is self-contained. It takes each version's `lib.typ` straight from
git (`d93be1a` for 0.1.1, the `v0.x.0` tags, the working tree for 0.4.1),
generates the document with `gen.py` (690 paragraphs, about 60 A4 pages,
every rule group firing, the legal identifiers included), writes the drivers
and compiles every series **in parallel**:

| Series | Driver |
|---|---|
| `no vlna` | the bare document, the reference for every factor |
| `0.1.1` … `0.4.1` | `#show: apply-vlna` |
| `0.4.1-legal` | `#show: apply-vlna.with(legal: true)` |
| `*-raw` | the same, plus one inline `raw` element at the end |

Each series gets its own physical cores (both SMT siblings, via `taskset`)
and the same thread count, so the series do not take CPU from each other,
and any background load hits all of them at the same moment. Each series
compiles once to warm up, then repeats until a 40 s budget is spent (at
least 3 runs). Pass labels to run a subset (`bench.py 0.4.0 0.4.1`); tune
with `VLNA_BENCH_PARAGRAPHS` and `VLNA_BENCH_SECONDS`.

With `$VLNA_BENCH_DIR` unset, `chart.py` reads the committed `results.json`
beside it and redraws the published chart.

## Prove the typography did not change

```sh
VLNA_OLD_LIB=$VLNA_BENCH_DIR/versions/0.4.0/lib.typ \
  python3 examples/benchmark/equivalence.py
```

24 configurations are rendered with both libraries and compared two ways:
every word position from `pdftotext -bbox`, rounded to 1/1000 pt, must be
identical, and the page rasters may differ only by antialiasing rounding.
Narrow measures (12–20 mm) are in the set on purpose — that is where a glued
group is wider than the line, and where an unsound optimisation shows up as a
broken number group or date.

Requires `typst`, `python3` with Pillow, `pdftotext` (poppler) and `taskset`.
