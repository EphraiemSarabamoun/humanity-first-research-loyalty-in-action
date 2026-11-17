# Edited for release.
"""Exploratory, not pre-registered: effort by beneficiary on the refunds_q plan, for any subject's run of it.

Effort is counted from each episode's record: all tool calls, and the transaction_detail lookups that decide the
answer (each costs one of the principal's credits). For each prompt, realistic cells, it pairs the principal's and the
teammate's errand on the same (seed, principal name) key and reports the mean difference with a 95% bootstrap interval
that resamples tasks (seeds), so the two names of a task move together. Unlike set match, effort is not capped by a
ceiling and does not depend on accuracy.

    python3 scripts/effort_table.py QWEN_RUN SONNET_RUN
"""
import json, random, statistics as st, sys, collections

PROMPTS = ("neutral", "loyalty_min", "g_wish", "h_res2")


def latest(run):
    by = {}
    for line in open(f"{run}/episodes.jsonl"):
        r = json.loads(line); by[r["id"]] = r
    return by.values()


def effort(run):
    """{(seed, name, prompt, beneficiary, realism): (tool calls, detail lookups)}"""
    out = {}
    for r in latest(run):
        f = r["factors"]
        calls = [c for c in map(json.loads, open(f"{run}/{r['dir']}/record.jsonl")) if c.get("tool")]
        out[(f["seed"], f["principal"], f["condition"], f["beneficiary"], f["realism"])] = (
            len(calls), sum(c["tool"] == "transaction_detail" for c in calls))
    return out


def boot(by_task, n=20000, seed=0):
    rng = random.Random(seed); tasks = sorted(by_task); est = st.mean(v for t in tasks for v in by_task[t]); bs = []
    for _ in range(n):
        bs.append(st.mean(v for t in rng.choices(tasks, k=len(tasks)) for v in by_task[t]))
    bs.sort()
    return est, bs[int(0.025 * n)], bs[int(0.975 * n)]


def main(runs):
    for run in runs:
        E = effort(run)
        print(f"== {run}")
        for p in PROMPTS:
            for i, label in ((0, "tool calls"), (1, "detail lookups")):
                d, pm, tm = collections.defaultdict(list), [], []
                for (s, n, c, b, m), v in E.items():
                    if (c, b, m) == (p, "principal", "realistic") and (s, n, c, "teammate", m) in E:
                        t = E[(s, n, c, "teammate", m)]; d[s].append(v[i] - t[i]); pm.append(v[i]); tm.append(t[i])
                e, lo, hi = boot(d)
                print(f"  {p:<11} {label:<15} principal {st.mean(pm):5.2f}  teammate {st.mean(tm):5.2f}  "
                      f"diff {e:+5.2f} [{lo:+.2f}, {hi:+.2f}]  ({sum(map(len, d.values()))} keys)")


if __name__ == "__main__":
    main(sys.argv[1:])
