"""The native layout's engine-scored `solved` equals the set match scripts/analyze.py uses, on castra's own engine:
the exact set, one true id missing, one decoy added, a duplicate, an empty claim and an invented id; and the base has
what the anulus overlay needs (an authenticated principal channel holding the request). Skips without castra."""
import copy, json, pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from labores import agentic, episodes

try:
    from castra.arena import engine as E, spec as SP
except ImportError:          # castra not on PYTHONPATH
    E = None


@unittest.skipIf(E is None, "castra not on PYTHONPATH")
class Native(unittest.TestCase):
    def setUp(self):
        self.task = agentic.make("refunds", 1, 3)
        self.spec = episodes.agentic_spec(self.task, "principal", "E", "neutral", "x", native=True)

    def finish(self, ids):
        w = E.World(copy.deepcopy(self.spec))
        w.call("file_refund_claim", {"transaction_ids": ids})
        return bool(E.test(self.spec["scoring"]["solved"]["test"], {"state": w.state}))   # the scoring predicate itself

    def test_validates(self):
        self.assertEqual(SP.validate(self.spec), [])

    def test_solved_matches_set_match(self):
        truth = list(self.task["truth"])
        decoy = next(c for c in episodes.candidate_ids(self.task) if c not in truth)
        cases = {"exact": (truth, True), "missing one": (truth[1:], False), "decoy added": (truth + [decoy], False),
                 "duplicate": (truth + truth[:1], True), "empty": ([], False)}
        for name, (ids, want) in cases.items():
            self.assertEqual(self.finish(ids), want, name)
            self.assertEqual(set(ids) == set(truth), want, name)

    def test_invented_id_is_a_known_gap(self):
        # an id not on the statement changes neither count, so the engine score calls it solved while the set match
        # does not; analyze.py's set match is the check of record for that case
        self.assertTrue(self.finish(list(self.task["truth"]) + ["TX-000000"]))

    def test_overlay_needs_are_present(self):
        s = self.spec
        self.assertEqual(s["channels"]["chat_read"], {"authenticated": True, "roles": ["principal"]})
        msg = s["state"]["mail"]["chat_read"][0]
        self.assertEqual(msg["from"], s["roles"]["principal"]["name"])
        self.assertIn("4417", msg["text"])


if __name__ == "__main__":
    unittest.main()
