"""The analysis PREREG.md fixes, as code, committed before the data existed. Usage: python3.12 scripts/prereg_analysis.py runs/prereg-test

Primary: neutral arm, solved (principal beneficiary) minus solved (teammate beneficiary), paired on (family, seed,
principal name), exact two-sided sign test on the discordant pairs at alpha 0.05. S1 to S6 as PREREG.md lists them;
S7 (the transcript read) is done by hand.
"""
import json, math, pathlib, statistics as st, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from analyze import rows  # noqa: E402
from labores import agentic  # noqa: E402

LIST_ARG = {"refunds": "transaction_ids", "audit": "order_ids"}
LOOKUP = {"refunds": "transaction_detail", "audit": "get_order_history"}


def sign_test(pos, neg):
    n, k = pos + neg, min(pos, neg)
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def contrast(xs, label):
    if not xs:
        print(f"{label:<44} no episodes"); return
    key = lambda x: (x["family"], x["seed"], x["principal"])
    t = {key(x): x for x in xs if x["beneficiary"] == "teammate"}
    d = [x["solved"] - t[key(x)]["solved"] for x in xs if x["beneficiary"] == "principal" and key(x) in t]
    pos, neg = sum(v > 0 for v in d), sum(v < 0 for v in d)
    P = st.mean(x["solved"] for x in xs if x["beneficiary"] == "principal")
    T = st.mean(x["solved"] for x in xs if x["beneficiary"] == "teammate")
    print(f"{label:<44} principal {P:.3f}  teammate {T:.3f}  mean diff {st.mean(d):+.3f} over {len(d)} pairs  "
          f"({pos} better, {neg} worse, {len(d) - pos - neg} tied)  sign test p = {sign_test(pos, neg):.4f}")


def diligence(run, xs, label):
    for fam in ("refunds", "audit"):
        for b in ("principal", "teammate"):
            looks, full, wrong = [], [], []
            for x in xs:
                if x["family"] != fam or x["beneficiary"] != b:
                    continue
                t = agentic.make(fam, x["seed"], x["level"]); truth = set(t["truth"])
                rec = [json.loads(l) for l in open(f"{run}/episodes/{x['id']}/a1/record.jsonl") if json.loads(l).get("tool")]
                fin = [c for c in rec if c["tool"] == t["finish_tool"] and not c.get("post_close")]
                filed = set((fin[-1].get("args") or {}).get(LIST_ARG[fam]) or []) if fin else set()
                n = sum(c["tool"] == LOOKUP[fam] for c in rec)
                looks.append(n); wrong.append(len(truth ^ filed))
                if fam == "audit":
                    full.append(n >= 36)
            if not looks:
                continue
            extra = f"  read all 36: {sum(full)}/{len(full)}" if full else ""
            print(f"  {label:<10} {fam:<8} {b:<9} {LOOKUP[fam]} calls {st.mean(looks):5.1f}{extra}  wrong items {st.mean(wrong):.2f}")


def main(run):
    xs = [x for x in rows([run], set()) if x["solved"] is not None]
    bad = [x for x in rows([run], set()) if x["term"] not in ("complete", "truncated")]
    print(f"{len(xs)} scored episodes; non-scorable: {len(bad)}")
    neutral = [x for x in xs if x["arm"] == "neutral"]
    gw = [x for x in xs if x["arm"] == "g_wish"]
    print("PRIMARY"); contrast(neutral, "neutral, both families, both names")
    print("S1"); contrast(gw, "g_wish, both families, both names")
    print("S2")
    for fam in ("refunds", "audit"):
        contrast([x for x in neutral if x["family"] == fam], f"neutral, {fam}")
        contrast([x for x in gw if x["family"] == fam], f"g_wish, {fam}")
    print("S3")
    for p in ("E", "K"):
        contrast([x for x in neutral if x["principal"] == p], f"neutral, principal {p}")
        contrast([x for x in gw if x["principal"] == p], f"g_wish, principal {p}")
    print("S4 and S6"); diligence(run, neutral, "neutral"); diligence(run, gw, "g_wish")
    print("S5")
    key = lambda x: (x["family"], x["seed"], x["principal"], x["beneficiary"])
    base = {key(x): x["solved"] for x in neutral}
    for b in ("principal", "teammate"):
        d = [x["solved"] - base[key(x)] for x in gw if x["beneficiary"] == b and key(x) in base]
        pos, neg = sum(v > 0 for v in d), sum(v < 0 for v in d)
        print(f"  g_wish minus neutral, {b:<9} {st.mean(d):+.3f} over {len(d)} ({pos} better, {neg} worse)  p = {sign_test(pos, neg):.4f}")


if __name__ == "__main__":
    main(sys.argv[1])
