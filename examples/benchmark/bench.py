#!/usr/bin/env python3
"""Compile-time benchmark: p50/p95 wall time per vlna version on a 501-page document."""
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("VLNA_BENCH_DIR", "/tmp/vlna-bench"))
RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 20
WARMUP = 2
# Pin every compile to the same 8 cores with the same thread count. Typst
# lays out pages in parallel, so on a machine with other load (browsers) the
# unpinned wall time swings by seconds; pinning makes the versions comparable.
CORES = "0-7"
THREADS = "8"


def p95(xs):
    """Linear-interpolated 95th percentile (same definition as numpy's default)."""
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    pos = 0.95 * (len(s) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def run_once(cwd, src, out):
    env = dict(os.environ, RAYON_NUM_THREADS=THREADS)
    t0 = time.perf_counter()
    r = subprocess.run(
        ["taskset", "-c", CORES, "typst", "compile", "--root", ".", src, str(out)],
        cwd=cwd, capture_output=True, text=True, env=env,
    )
    dt = time.perf_counter() - t0
    if r.returncode != 0:
        raise SystemExit(f"compile failed in {cwd}:\n{r.stderr[:2000]}")
    return dt


def summarise(label, times):
    res = {
        "label": label,
        "runs": len(times),
        "min": min(times),
        "p50": statistics.median(times),
        "p95": p95(times),
        "max": max(times),
        "mean": statistics.fmean(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0.0,
        "times": times,
    }
    print(
        f"{label:>16}  p50 {res['p50']:6.3f}s  p95 {res['p95']:6.3f}s  "
        f"min {res['min']:6.3f}s  max {res['max']:6.3f}s  sd {res['stdev']:.3f}",
        flush=True,
    )
    return res


def main():
    targets = [("no vlna", ROOT / "versions/0.3.0", "head-off.typ")]
    for spec in sys.argv[2:] or ["0.1.1", "0.2.0", "0.3.0"]:
        targets.append((spec, ROOT / "versions" / spec, "head-on.typ"))

    print(f"501-page document, {RUNS} interleaved rounds (+{WARMUP} warm-ups)\n")
    # Round-robin, so machine drift hits every version equally instead of
    # penalising whichever one happened to run during a busy stretch.
    times = {label: [] for label, _, _ in targets}
    for r in range(WARMUP + RUNS):
        for label, cwd, src in targets:
            dt = run_once(cwd, src, ROOT / f"out-{label}.pdf")
            if r >= WARMUP:
                times[label].append(dt)
        print(f"  round {r + 1}/{WARMUP + RUNS} done", flush=True)
    print()
    results = [summarise(label, times[label]) for label, _, _ in targets]
    # One run = one dataset. Merging into previous results silently mixes
    # measurements taken under different machine load, and comparing two
    # versions across such a mix produces confident nonsense.
    (ROOT / "results.json").write_text(
        json.dumps(
            {
                "runs": RUNS,
                "cores": CORES,
                "threads": THREADS,
                "series": {r["label"]: r for r in results},
            },
            indent=1,
        )
    )
    print(f"\nwrote {ROOT / 'results.json'}")


if __name__ == "__main__":
    main()
