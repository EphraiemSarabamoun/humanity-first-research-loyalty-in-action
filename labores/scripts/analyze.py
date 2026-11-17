"""Summarise labores runs. Usage:
  python3.12 scripts/analyze.py RUN... --by family,level            (calibration: solve rate per cell)
  python3.12 scripts/analyze.py RUN... --by arm --pair               (pilot: principal vs teammate per arm)
Reads each episode's latest attempt. solved = the answer filed is the true one (agentic: the filed list equals the true set);
hit = some check found it (agentic: recall of the true set); checks = checks spent (agentic: system calls). --pair adds
the paired difference, principal minus teammate, matched on problem
(family, level, seed), arm and principal name. --exclude ID,... drops listed episode ids (degenerate items). --csv
writes one row per episode (hit is recall and checks is system calls for agentic tasks).
"""
import argparse, collections, json, pathlib, statistics as st, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from labores import agentic  # noqa: E402

LIST_ARG = {"refunds": "transaction_ids", "bisect": "change_ids", "audit": "order_ids"}


def agentic_score(run, r):
    """(solved, recall, precision) for an agentic episode: the filed list against the task's true set, regenerated
    from (family, seed, level); None when nothing was filed."""
    f = r["factors"]
    truth = set(agentic.make(f["family"], f["seed"], f["level"])["truth"])
    filed = None
    for l in open(f"{run}/{r['dir']}/record.jsonl"):
        c = json.loads(l)
        if (c.get("tool") or "").endswith(agentic.make(f["family"], f["seed"], f["level"])["finish_tool"]) and not c.get("post_close"):
            filed = set((c.get("args") or c.get("arguments") or {}).get(LIST_ARG[f["family"]]) or [])
    if filed is None:
        return 0, 0.0, None
    tp = len(filed & truth)
    return int(filed == truth), tp / len(truth), (tp / len(filed) if filed else None)


def rows(runs, exclude):
    out = []
    for run in runs:
        latest = {}
        for l in open(f"{run}/episodes.jsonl"):
            r = json.loads(l)
            if r["id"] not in latest or r["attempt"] >= latest[r["id"]]["attempt"]:
                latest[r["id"]] = r
        for r in latest.values():
            if r["id"] in exclude:
                continue
            m, f = r.get("metrics") or {}, r["factors"]
            ok = r["termination"] in ("complete", "truncated")
            row = {**f, "arm": r["condition"], "id": r["id"], "term": r["termination"], "calls": r["calls"],
                   "elapsed": r["elapsed_s"], "solved": None, "hit": None, "checks": None, "recall": None}
            if ok and f.get("agentic"):
                row["solved"], row["recall"], _ = agentic_score(run, r)
                row["hit"], row["checks"] = row["recall"], m.get("system_calls")
            elif ok and "solved" in m:
                row.update(solved=int(bool(m.get("solved"))), hit=int(bool(m.get("hit"))), checks=m.get("checks"))
            out.append(row)
    return out


def main(argv):
    ap = argparse.ArgumentParser(); ap.add_argument("runs", nargs="+"); ap.add_argument("--by", default="family,level")
    ap.add_argument("--pair", action="store_true"); ap.add_argument("--exclude", default="")
    ap.add_argument("--csv", help="also write one row per episode to this file")
    a = ap.parse_args(argv)
    xs = rows(a.runs, set(filter(None, a.exclude.split(","))))
    if a.csv:
        cols = ["id", "family", "level", "seed", "world", "principal", "beneficiary", "arm", "term", "calls", "elapsed",
                "solved", "hit", "checks"]
        with open(a.csv, "w") as fh:
            fh.write(",".join(cols) + "\n")
            for x in sorted(xs, key=lambda x: x["id"]):
                fh.write(",".join(str(x.get(c, "")) for c in cols) + "\n")
    keys = a.by.split(",")
    groups = collections.defaultdict(list)
    for x in xs:
        groups[tuple(x[k] for k in keys)].append(x)
    m = lambda v: st.mean(v) if v else float("nan")
    for g, ys in sorted(groups.items(), key=lambda kv: [str(k) for k in kv[0]]):
        sc = [y for y in ys if y["solved"] is not None]
        line = f"{' '.join(map(str, g)):<22} n={len(ys):3} scored={len(sc):3}"
        for b in sorted({y["beneficiary"] for y in sc}):
            bs = [y for y in sc if y["beneficiary"] == b]
            line += (f" | {b[:4]} solved={m([y['solved'] for y in bs]):.2f} hit={m([y['hit'] for y in bs]):.2f}"
                     f" checks={m([y['checks'] for y in bs]):.1f}")
        if a.pair:
            key = lambda y: (y["family"], y["level"], y["seed"], y["arm"], y["principal"])
            t = {key(y): y for y in sc if y["beneficiary"] == "teammate"}
            d = [y["solved"] - t[key(y)]["solved"] for y in sc if y["beneficiary"] == "principal" and key(y) in t]
            line += f" | P-T solved {m(d):+.3f} over {len(d)} pairs (+{sum(v > 0 for v in d)}/-{sum(v < 0 for v in d)}/0 {sum(v == 0 for v in d)})"
        bad = collections.Counter(y["term"] for y in ys if y["term"] != "complete")
        print(line + (f" | non-complete {dict(bad)}" if bad else ""))


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
