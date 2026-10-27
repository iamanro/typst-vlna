#!/usr/bin/env python3
"""Compile-time benchmark: p50/p95 wall time per vlna version, all versions at once.

    python3 examples/benchmark/bench.py              # every series, ~1 minute
    python3 examples/benchmark/bench.py 0.4.0 0.4.1  # a subset

Self-contained: takes each version's lib.typ from git, generates the document
and the drivers into $VLNA_BENCH_DIR, then compiles every series IN PARALLEL.
Each series gets its own physical cores (taskset, both SMT siblings) and the
same thread count, so the series do not steal CPU from each other, and
whatever load the machine has hits them all at the same moment. Every series
compiles until the time budget runs out, at least MIN_RUNS times.
"""
import concurrent.futures as cf
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = Path(os.environ.get("VLNA_BENCH_DIR", "/tmp/vlna-bench"))
PARAGRAPHS = int(os.environ.get("VLNA_BENCH_PARAGRAPHS", 690))  # ~60 A4 pages
BUDGET = float(os.environ.get("VLNA_BENCH_SECONDS", 40))  # measuring time per series
MIN_RUNS = 3

# label: (git revision of lib.typ, None = working tree; apply-vlna arguments; raw block?)
VERSIONS = {
    "0.1.1": ("d93be1a", "", False),
    "0.2.0": ("v0.2.0", "", False),
    "0.3.0": ("v0.3.0", "", False),
    "0.4.0": ("v0.4.0", "", False),
    "0.4.1": (None, "", False),
    "0.4.1-legal": (None, ".with(legal: true)", False),
    "0.3.0-raw": ("v0.3.0", "", True),
    "0.4.0-raw": ("v0.4.0", "", True),
    "0.4.1-raw": (None, "", True),
}
HEAD = (
    '#set text(lang: "cs", size: 10pt)\n'
    '#set page(paper: "a4", margin: 2cm)\n'
    "#set par(justify: true)\n"
)


def p95(xs):
    """Linear-interpolated 95th percentile (same definition as numpy's default)."""
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    pos = 0.95 * (len(s) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def physical_cores():
    """Usable CPUs grouped by physical core: [[0, 1], [2, 3], ...]."""
    groups = {}
    for cpu in sorted(os.sched_getaffinity(0)):
        sib = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology/thread_siblings_list")
        key = sib.read_text().strip() if sib.exists() else str(cpu)
        groups.setdefault(key, []).append(cpu)
    return list(groups.values())


def prepare(labels):
    """Write lib.typ, body.typ and the driver for every series; return its dir."""
    body = subprocess.run(
        [sys.executable, HERE / "gen.py", str(PARAGRAPHS)],
        check=True, capture_output=True, text=True,
    ).stdout
    dirs = {}
    for label in labels:
        rev, args, raw = VERSIONS[label]
        d = ROOT / "versions" / label
        d.mkdir(parents=True, exist_ok=True)
        lib = (REPO / "lib.typ").read_text() if rev is None else subprocess.run(
            ["git", "show", f"{rev}:lib.typ"], cwd=REPO, check=True,
            capture_output=True, text=True,
        ).stdout
        (d / "lib.typ").write_text(lib)
        (d / "body.typ").write_text(body + ("\n`kód`\n" if raw else ""))
        (d / "head-on.typ").write_text(
            f'#import "lib.typ": apply-vlna\n{HEAD}#show: apply-vlna{args}\n#include "body.typ"\n'
        )
        (d / "head-off.typ").write_text(f'{HEAD}#include "body.typ"\n')
        dirs[label] = d
    return dirs


def measure(label, cwd, src, cpus):
    """Warm up once, then compile until the budget is spent; return wall times."""
    env = dict(os.environ, RAYON_NUM_THREADS=str(len(cpus)))
    cmd = ["taskset", "-c", ",".join(map(str, cpus)), "typst", "compile",
           "--root", ".", src, str(ROOT / f"out-{label}.pdf")]
    times = []
    start = None
    while start is None or len(times) < MIN_RUNS or time.perf_counter() - start < BUDGET:
        t0 = time.perf_counter()
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
        dt = time.perf_counter() - t0
        if r.returncode != 0:
            raise SystemExit(f"compile failed for {label}:\n{r.stderr[:2000]}")
        if start is None:
            start = time.perf_counter()  # the first compile was the warm-up
        else:
            times.append(dt)
    return times


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
        f"min {res['min']:6.3f}s  max {res['max']:6.3f}s  n={res['runs']}",
        flush=True,
    )
    return res


def main():
    labels = sys.argv[1:] or list(VERSIONS)
    unknown = [l for l in labels if l not in VERSIONS]
    if unknown:
        raise SystemExit(f"unknown series {unknown}; known: {list(VERSIONS)}")
    dirs = prepare(labels)
    # The bare document (no package) is the reference every factor is taken against.
    targets = [("no vlna", dirs[labels[0]], "head-off.typ")]
    targets += [(label, dirs[label], "head-on.typ") for label in labels]

    cores = physical_cores()
    per = len(cores) // len(targets)
    if per == 0:
        raise SystemExit(f"{len(targets)} series need as many physical cores, "
                         f"only {len(cores)} usable; pass fewer series")
    slots = [sum(cores[i * per:(i + 1) * per], []) for i in range(len(targets))]
    print(f"{PARAGRAPHS} paragraphs, {len(targets)} series in parallel, "
          f"{per} physical core(s) / {len(slots[0])} threads each, {BUDGET:.0f} s budget\n")

    with cf.ThreadPoolExecutor(len(targets)) as pool:
        futures = [pool.submit(measure, label, cwd, src, cpus)
                   for (label, cwd, src), cpus in zip(targets, slots)]
        times = [f.result() for f in futures]
    results = [summarise(label, t) for (label, _, _), t in zip(targets, times)]
    # One run = one dataset: never merge with earlier results, which were
    # measured under different machine load.
    (ROOT / "results.json").write_text(json.dumps({
        "paragraphs": PARAGRAPHS,
        "pages": int(subprocess.run(
            ["pdfinfo", ROOT / "out-no vlna.pdf"], capture_output=True, text=True,
        ).stdout.split("Pages:")[1].split()[0]),
        "budget_s": BUDGET,
        "threads": len(slots[0]),
        "typst": subprocess.run(["typst", "--version"], capture_output=True,
                                text=True).stdout.split()[1],
        "series": {r["label"]: r for r in results},
    }, indent=1))
    print(f"\nwrote {ROOT / 'results.json'}")


if __name__ == "__main__":
    main()
