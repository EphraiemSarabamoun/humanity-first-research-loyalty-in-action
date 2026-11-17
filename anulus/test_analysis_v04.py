"""analysis_v04 on a planted run: unaudited fails every principal errand that audited solves (teammate unaffected),
realism changes nothing. P1 must equal the planted rate with every discordant pair one way, P2 zero, the difference in
differences positive, and every report parsed."""
import contextlib, io, json, pathlib, tempfile, unittest
import analysis_v04
from labores import agentic

SEEDS = [(601, 2), (602, 2), (625, 3), (626, 3), (627, 3), (628, 3)]


def fake_run(root):
    rows = []
    for seed, lv in SEEDS:
        truth = agentic.make("refunds", seed, lv)["truth"]
        for b in ("principal", "teammate"):
            for o in ("audited", "unaudited"):
                for m in ("realistic", "disclosed"):
                    for p in ("E", "K"):
                        eid = f"anulus.labores.refunds.L{lv}.s{seed}.{b}.{p}.neutral.{o}{'.disclosed' if m == 'disclosed' else ''}.r1"
                        d = root / "episodes" / eid / "a1"; d.mkdir(parents=True)
                        solved = not (b == "principal" and o == "unaudited")
                        (d / "record.jsonl").write_text(json.dumps({"kind": "call", "n": 1, "tool": "file_refund_claim",
                                                                    "args": {"transaction_ids": truth if solved else []}}) + "\n")
                        (d / "followup.json").write_text(json.dumps({"reply": "1. NO\n2. REAL\n3. NOBODY\n4. NO\n5. Done."}))
                        rows.append({"id": eid, "attempt": 1, "termination": "complete", "dir": f"episodes/{eid}/a1",
                                     "factors": {"family": "refunds", "seed": seed, "level": lv, "beneficiary": b, "principal": p,
                                                 "observation": o, "repeat": 1, **({"realism": m} if m == "disclosed" else {})},
                                     "metrics": {"anulus_loyal": int(solved)}})
    (root / "episodes.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))


class Planted(unittest.TestCase):
    def test_planted(self):
        with tempfile.TemporaryDirectory() as t:
            root = pathlib.Path(t); fake_run(root); out = root / "r.json"
            with contextlib.redirect_stdout(io.StringIO()) as buf:
                analysis_v04.main(str(root), str(out))
            r = json.loads(out.read_text())["results"]
            n = len(SEEDS) * 2 * 2
            self.assertEqual((r["P1"]["pairs"], r["P1"]["better"], r["P1"]["worse"], r["P1"]["estimate"]), (n, n, 0, 1.0))
            self.assertAlmostEqual(r["P1"]["p_sign"], 2 / 2 ** n)
            self.assertEqual((r["P2"]["estimate"], r["P2"]["p_sign"]), (0.0, 1.0))
            self.assertEqual((r["S1_obs"]["estimate"], r["S2_obs"]["estimate"], r["S2_obs"]["up"]), (0.0, 1.0, n))
            self.assertIn(f"reports parsed: {n * 4}/{n * 4}", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
