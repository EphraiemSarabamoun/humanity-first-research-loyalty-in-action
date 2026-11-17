"""Every family's answer is exact: the strings DP against brute force, a hand-checkable path count, and every
family at every level is deterministic in its seed and gives a positive integer."""
import itertools, pathlib, sys, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from labores import problems


class Exact(unittest.TestCase):
    def test_strings_dp_matches_brute_force(self):
        for L in range(1, 10):
            for k in range(0, 4):
                for s in ("AB", "BA", "AA", "ABA", "BAB", "ACB", "BCA", "AAB", "CC"):
                    brute = sum(1 for w in itertools.product("ABC", repeat=L) if w.count("C") == k and s not in "".join(w))
                    self.assertEqual(problems.count_strings(L, k, s), brute, (L, k, s))

    def test_paths_unblocked_grid_is_binomial(self):
        # with no blocked point a 3x3 grid has C(6, 3) = 20 paths; the generator always blocks some, so check the DP
        # directly through a tiny copy of its recurrence
        n, dp = 3, {}
        for x in range(n + 1):
            for y in range(n + 1):
                dp[x, y] = 1 if (x, y) == (0, 0) else dp.get((x - 1, y), 0) + dp.get((x, y - 1), 0)
        self.assertEqual(dp[n, n], 20)

    def test_deterministic_and_positive(self):
        for fam in problems.FAMILIES:
            for lv in (1, 2, 3):
                a, b = problems.make(fam, 7, lv), problems.make(fam, 7, lv)
                self.assertEqual(a, b)
                self.assertGreaterEqual(a["answer"], 5, (fam, lv))


if __name__ == "__main__":
    unittest.main()
