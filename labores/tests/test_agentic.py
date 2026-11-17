"""The agentic tasks' answers are what they claim: every true duplicate is the later posting of a same-merchant,
same-amount pair minutes apart on an outage day with no reversal; every reversed duplicate has a credit whose detail
names it; bisect's rules fail exactly when every culprit is in the run."""
import pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from labores import agentic


class Refunds(unittest.TestCase):
    def test_truth_is_the_later_posting_of_an_unreversed_pair(self):
        for seed in range(1, 13):
            for lv in (1, 2, 3):
                t = agentic.make("refunds", seed, lv)
                rows = [r for p in t["state"]["statement"]["pages"].values() for r in p]
                notes = " ".join(d["note"] for d in t["state"]["detail"].values())
                for tid in t["truth"]:
                    r = next(x for x in rows if x["id"] == tid)
                    twins = [x for x in rows if x["id"] != tid and x["merchant"] == r["merchant"] and x["amount"] == r["amount"]
                             and x["date"] == r["date"] and x["status"] == "posted"]
                    self.assertEqual(len(twins), 1, (seed, lv, tid))
                    self.assertLess((twins[0]["date"], twins[0]["time"]), (r["date"], r["time"]), (seed, lv, tid))
                    self.assertIn(r["date"], ("2026-10-14", "2026-10-15"))
                    self.assertNotIn(tid, notes, (seed, lv, tid))


class Bisect(unittest.TestCase):
    def test_culprits_exist(self):
        for seed in range(1, 13):
            for lv in (1, 2, 3, 4, 5):
                t = agentic.make("bisect", seed, lv)
                ids = {c["id"] for c in t["state"]["changes"]}
                self.assertTrue(set(t["truth"]) <= ids)
                self.assertEqual(len(t["truth"]), 2 if lv in (3, 5) else 1)
                flaky = [r for r in t["rules"] if r["id"] == "run-flaky-pass"]
                self.assertEqual(bool(flaky), lv >= 4)
                if flaky:   # the flaky rule must come before the failing rule, or it never fires
                    ids_in_order = [r["id"] for r in t["rules"]]
                    self.assertLess(ids_in_order.index("run-flaky-pass"), ids_in_order.index("run-fail"))


if __name__ == "__main__":
    unittest.main()


class Audit(unittest.TestCase):
    def test_truth_recomputes_from_what_the_tools_serve(self):
        for seed in range(1, 13):
            for lv in (1, 2, 3, 4):
                t = agentic.make("audit", seed, lv)
                st = t["state"]
                flagged = []
                for page in st["orders"]["pages"].values():
                    for o in page:
                        d, line = st["order_detail"][o["id"]], st["lines"][o["budget_line"]]
                        items = [dict(i) for i in d["items"]]
                        for h in st.get("history", {}).get(o["id"], []):   # apply amendments as the history states them
                            if "raised from" in h:
                                items[0]["qty"] = int(h.rsplit(" to ", 1)[1].split()[0])
                            if "revised the unit price" in h:
                                items[0]["unit_price"] = float(h.rsplit(" to ", 1)[1].rstrip("."))
                        total = round((sum(i["qty"] * i["unit_price"] for i in items) + d["shipping"]) * 1.06, 2)
                        if line["committed"] + total > line["cap"]:
                            flagged.append(o["id"])
                self.assertEqual(sorted(flagged), t["truth"], (seed, lv))


class AuditAmendments(unittest.TestCase):
    def test_amendments_flip_some_flags(self):
        flips = 0
        for seed in range(1, 13):
            t = agentic.make("audit", seed, 4)
            st = t["state"]
            for page in st["orders"]["pages"].values():
                for o in page:
                    d, line = st["order_detail"][o["id"]], st["lines"][o["budget_line"]]
                    naive = line["committed"] + round((sum(i["qty"] * i["unit_price"] for i in d["items"]) + d["shipping"]) * 1.06, 2) > line["cap"]
                    flips += naive != (o["id"] in t["truth"])
        self.assertGreater(flips, 12 * 4)   # at least four flips a task on average: skipping the history costs answers
