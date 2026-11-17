# Edited for release.
"""Check the paper's numbers against the tables in this folder, with no other input.

This is a consistency check of the published tables, not a replication from raw records. Only the labores counts
are rebuilt from per-episode rows; the effort and test-share checks compare figure tables with summary reports.

Written for this public folder; it is not part of the code that ran the studies. It uses only the Python standard
library (tested on Python 3.10) and reads files by paths relative to this script, so it runs from any directory:

    python3 recount.py

Three checks, one per figure of the paper, plus the pre-registered labores contrasts:

1. labores, the pre-registered test. From labores/results/prereg-test.csv (one row per episode) it rebuilds the
   paired contrasts of labores/PREREG.md (primary, S1, S2, S3, S5), each with its exact two-sided sign test, and the
   solve counts behind figures/labores.csv.
2. Effort on the second model. From second-model/results/effort.txt (the report of
   second-model/scripts/effort_table.py) it reads the detail lookups per errand and compares them with
   figures/effort.csv.
3. How often each model called its session a test. Qwen's shares are read from second-model/results/qwen-refunds_q.txt
   (section S4); Sonnet's are checked against the values stated in anulus/RESULTS-v0.5.md (section S5), because the
   per-episode anulus table is not in this folder. Both are compared with figures/test_share.csv.

Each check prints the recounted value beside the stated value (from the paper's figure tables or from the results
documents in this folder), and the script exits with status 1 if any of them disagree beyond rounding.
"""
from __future__ import annotations

import csv
import math
import pathlib
import re
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
FAILURES: list[str] = []


# ---- small helpers ---------------------------------------------------------------------------------------------

def sign_test(pos: int, neg: int) -> float:
    """Exact two-sided sign test on the discordant pairs, as labores/scripts/prereg_analysis.py defines it."""
    n, k = pos + neg, min(pos, neg)
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def check(label: str, got: float, want: float, tol: float) -> None:
    """Print one comparison and remember it if the recount and the stated value differ by more than tol."""
    ok = abs(got - want) <= tol + 1e-9          # the slack lets a value like 0.0625 round to a stated 0.062
    print(f"  {'ok  ' if ok else 'FAIL'} {label:<58} recounted {got:+.3f}   stated {want:+.3f}")
    if not ok:
        FAILURES.append(label)


def read_csv(rel: str) -> list[dict]:
    with open(HERE / rel, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---- 1. labores --------------------------------------------------------------------------------------------------

def paired(rows: list[dict], key, a, b) -> tuple[list[int], float, float]:
    """Pair rows by key(row) between the subsets a(row) and b(row); return the differences and both means."""
    left = {key(r): int(r["solved"]) for r in rows if a(r)}
    right = {key(r): int(r["solved"]) for r in rows if b(r)}
    keys = sorted(set(left) & set(right))
    diffs = [left[k] - right[k] for k in keys]
    return diffs, statistics.mean(left[k] for k in keys), statistics.mean(right[k] for k in keys)


def labores() -> None:
    """The pre-registered labores contrasts (PREREG.md) and the counts behind figures/labores.csv."""
    print("1. labores, the pre-registered test (labores/results/prereg-test.csv)")
    rows = read_csv("labores/results/prereg-test.csv")
    check("episodes in the test", len(rows), 384, 0)

    task = lambda r: (r["family"], r["seed"], r["principal"])          # the pairing key of PREREG.md
    is_p = lambda r: r["beneficiary"] == "principal"
    is_t = lambda r: r["beneficiary"] == "teammate"

    # Stated values: the pre-registered test's table in labores/RESULTS.md. (label, subset, P, T, diff, better, worse)
    stated = [
        ("primary: neutral, both families and names", lambda r: r["arm"] == "neutral", .604, .594, .010, 16, 15),
        ("S1: g_wish, both families and names", lambda r: r["arm"] == "g_wish", .906, .417, .490, 49, 2),
        ("S2: neutral, refunds", lambda r: r["arm"] == "neutral" and r["family"] == "refunds", .542, .583, -.042, 7, 9),
        ("S2: neutral, audit", lambda r: r["arm"] == "neutral" and r["family"] == "audit", .667, .604, .062, 9, 6),
        ("S2: g_wish, refunds", lambda r: r["arm"] == "g_wish" and r["family"] == "refunds", .938, .396, .542, 26, 0),
        ("S2: g_wish, audit", lambda r: r["arm"] == "g_wish" and r["family"] == "audit", .875, .438, .438, 23, 2),
        ("S3: neutral, principal E", lambda r: r["arm"] == "neutral" and r["principal"] == "E", .583, .562, .021, 7, 6),
        ("S3: neutral, principal K", lambda r: r["arm"] == "neutral" and r["principal"] == "K", .625, .625, 0, 9, 9),
        ("S3: g_wish, principal E", lambda r: r["arm"] == "g_wish" and r["principal"] == "E", .938, .396, .542, 27, 1),
        ("S3: g_wish, principal K", lambda r: r["arm"] == "g_wish" and r["principal"] == "K", .875, .438, .438, 22, 1),
    ]
    for label, sub, p_want, t_want, d_want, better, worse in stated:
        xs = [r for r in rows if sub(r)]
        d, p_rate, t_rate = paired(xs, task, is_p, is_t)
        pos, neg = sum(v > 0 for v in d), sum(v < 0 for v in d)
        print(f"  {label}: {len(d)} pairs, {pos} better, {neg} worse, sign test p = {sign_test(pos, neg):.2g}")
        check(f"{label}, principal", p_rate, p_want, 0.0005)
        check(f"{label}, teammate", t_rate, t_want, 0.0005)
        check(f"{label}, mean paired difference", statistics.mean(d), d_want, 0.0005)
        check(f"{label}, pairs better", pos, better, 0)
        check(f"{label}, pairs worse", neg, worse, 0)

    # S5: g_wish minus neutral on the same task, beneficiary and name.
    for b, d_want, better, worse in (("principal", .302, 32, 3), ("teammate", -.177, 12, 29)):
        xs = [r for r in rows if r["beneficiary"] == b]
        d, _, _ = paired(xs, task, lambda r: r["arm"] == "g_wish", lambda r: r["arm"] == "neutral")
        pos, neg = sum(v > 0 for v in d), sum(v < 0 for v in d)
        print(f"  S5: g_wish minus neutral, {b}: {len(d)} pairs, sign test p = {sign_test(pos, neg):.2g}")
        check(f"S5: g_wish minus neutral, {b}", statistics.mean(d), d_want, 0.0005)
        check(f"S5: g_wish minus neutral, {b}, better", pos, better, 0)
        check(f"S5: g_wish minus neutral, {b}, worse", neg, worse, 0)

    # figures/labores.csv: solved counts per prompt and errand.
    for f in read_csv("figures/labores.csv"):
        cell = [r for r in rows if r["arm"] == f["prompt"] and r["beneficiary"] == f["errand"]]
        check(f"figure: {f['prompt']}, {f['errand']} solved", sum(int(r["solved"]) for r in cell), int(f["solved"]), 0)
        check(f"figure: {f['prompt']}, {f['errand']} episodes", len(cell), int(f["episodes"]), 0)


# ---- 2. effort on the second model -------------------------------------------------------------------------------

def effort() -> None:
    """Detail lookups per errand, principal and teammate, from effort.txt against figures/effort.csv."""
    print("2. Effort, Sonnet and Qwen on one plan (second-model/results/effort.txt)")
    models = {"qwen-refunds_q": "Qwen3.8-27B", "sonnet-refunds_q": "Claude Sonnet 5.5"}
    found, model = {}, None
    pat = re.compile(r"^\s+(\S+)\s+detail lookups\s+principal\s+([\d.]+)\s+teammate\s+([\d.]+)\s+diff\s+([+-][\d.]+)"
                     r"\s+\[([+-][\d.]+),\s*([+-][\d.]+)\]")
    for line in (HERE / "second-model/results/effort.txt").read_text(encoding="utf-8").splitlines():
        if line.startswith("== "):
            model = models[line[3:].strip()]
        elif (m := pat.match(line)):
            found[(model, m.group(1))] = [float(x) for x in m.groups()[1:]]
    for f in read_csv("figures/effort.csv"):
        got = found[(f["model"], f["prompt"])]
        want = [float(f[c]) for c in ("lookups_principal", "lookups_teammate", "difference", "ci_lo", "ci_hi")]
        for name, g, w in zip(("principal", "teammate", "difference", "interval low", "interval high"), got, want):
            check(f"{f['model']}, {f['prompt']}, {name}", g, w, 0.005)


# ---- 3. the share of sessions called a test ----------------------------------------------------------------------

def test_share() -> None:
    """The share of sessions each model called a test, untold and told, against figures/test_share.csv."""
    print("3. Sessions called a test (second-model/results/qwen-refunds_q.txt, anulus/RESULTS-v0.5.md)")
    qwen = {}
    pat = re.compile(r"^\s+(\S+)\s+(realistic|disclosed)\s+TEST\s+([\d.]+)")
    for line in (HERE / "second-model/results/qwen-refunds_q.txt").read_text(encoding="utf-8").splitlines():
        if (m := pat.match(line)):
            qwen[(m.group(1), m.group(2) == "disclosed")] = float(m.group(3))
    # Sonnet: anulus v0.5 states 1.00 told under both prompts, 0.15 untold under neutral and 0.64 under g_wish.
    text = (HERE / "anulus/RESULTS-v0.5.md").read_text(encoding="utf-8")
    s5 = re.search(r"called the session a test in ([\d.]+) of disclosed episodes under both prompts\. Untold, it "
                   r"called the session a test in ([\d.]+) of neutral episodes and in \*\*([\d.]+) of `g_wish`", text)
    told, neutral, g_wish = (float(x) for x in s5.groups())
    sonnet = {("neutral", True): told, ("g_wish", True): told, ("neutral", False): neutral, ("g_wish", False): g_wish}
    for f in read_csv("figures/test_share.csv"):
        key = (f["prompt"], f["told_it_is_an_evaluation"] == "True")
        got = (qwen if f["model"] == "Qwen3.8-27B" else sonnet)[key]
        check(f"{f['model']}, {f['prompt']}, told={key[1]}", got, float(f["share_called_test"]), 0.005)


def main() -> int:
    labores()
    effort()
    test_share()
    print(f"\n{'ALL CHECKS AGREE' if not FAILURES else str(len(FAILURES)) + ' CHECKS DISAGREE: ' + ', '.join(FAILURES)}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
