"""refunds_q is refunds with only the duplicate postings' notes changed: same statement, same truth, the reversal still
named only on the credit; refunds itself is untouched."""
import unittest
from labores import agentic


class RefundsQ(unittest.TestCase):
    def test_only_duplicate_notes_change(self):
        for level in (1, 2, 3):
            for seed in (1, 2, 701):
                a, b = agentic.make("refunds", seed, level), agentic.make("refunds_q", seed, level)
                self.assertEqual((a["truth"], a["state"]["statement"], a["tools"], a["rules"]),
                                 (b["truth"], b["state"]["statement"], b["tools"], b["rules"]))
                changed = {k for k in a["state"]["detail"] if a["state"]["detail"][k] != b["state"]["detail"][k]}
                self.assertTrue(set(a["truth"]) <= changed)
                self.assertTrue(all(b["state"]["detail"][k]["note"] == agentic.OUTAGE_NOTE for k in changed))
                credits = [d["note"] for d in b["state"]["detail"].values() if d["note"].startswith("Reversal of")]
                self.assertEqual(len(changed), len(a["truth"]) + len(credits))   # each reversed duplicate's second posting

    def test_refunds_notes_unchanged(self):
        a = agentic.make("refunds", 701, 1)
        self.assertTrue(all(a["state"]["detail"][t]["note"] == "Posted normally." for t in a["truth"]))


if __name__ == "__main__":
    unittest.main()
