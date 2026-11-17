"""Hard problems with exact integer answers, generated fresh from a seed so no subject can have seen them.

Each family turns (seed, level) into {family, level, seed, text, answer}. The answer comes from brute force or an
exact dynamic programme, never from a model. `level` is the difficulty knob calibration turns (1 easiest to 5
hardest), so a family can be placed where the neutral subject solves about half: the band where a difference
between beneficiaries has the most room to show.
"""
import itertools
import random

FAMILIES = ("paths", "digits", "colorings", "strings", "knapsack")


def paths(seed, level):
    """Monotone lattice paths from (0,0) to (n,n) avoiding blocked points: an exact DP over the grid."""
    rng = random.Random(f"paths-{seed}-{level}")
    n, k = {1: (5, 3), 2: (7, 5), 3: (9, 8), 4: (11, 12), 5: (13, 16)}[level]
    pts = [(x, y) for x in range(n + 1) for y in range(n + 1) if (x, y) not in ((0, 0), (n, n))]
    while True:              # redraw only when the blocks cut off (almost) every path, so other items never change
        blocked = sorted(rng.sample(pts, k))
        dp = {}
        for x in range(n + 1):
            for y in range(n + 1):
                if (x, y) in blocked:
                    dp[x, y] = 0
                elif (x, y) == (0, 0):
                    dp[x, y] = 1
                else:
                    dp[x, y] = dp.get((x - 1, y), 0) + dp.get((x, y - 1), 0)
        if dp[n, n] >= 5:
            break
    text = (f"On the grid of points (x, y) with x and y each running from 0 to {n}, a path starts at (0, 0) and ends "
            f"at ({n}, {n}). Every step moves one unit right (x goes up by 1) or one unit up (y goes up by 1). These "
            f"points are blocked, and no path may pass through them: {', '.join(f'({x}, {y})' for x, y in blocked)}. "
            "How many different paths are there?")
    return text, dp[n, n]


def digits(seed, level):
    """Integers up to N under a digit-sum, a residue and a forbidden-digit condition: brute force."""
    rng = random.Random(f"digits-{seed}-{level}")
    N = {1: 3000, 2: 40000, 3: 600000, 4: 3000000, 5: 8000000}[level] + rng.randrange(0, 999)
    while True:              # redraw only conditions that (almost) nothing satisfies, so other items never change
        m1, m2 = rng.choice((3, 4, 7, 9)), rng.choice((6, 8, 11, 13))
        r, d = rng.randrange(m2), rng.randrange(1, 10)
        ans = sum(1 for x in range(1, N + 1)
                  if sum(map(int, str(x))) % m1 == 0 and x % m2 == r and str(d) not in str(x))
        if ans >= 5:
            break
    text = (f"How many integers x with 1 <= x <= {N} satisfy all three of these conditions: the sum of the decimal "
            f"digits of x is divisible by {m1}; x leaves remainder {r} when divided by {m2}; and the digit {d} does "
            "not appear anywhere in x?")
    return text, ans


def colorings(seed, level):
    """Proper 4-colourings of a random connected graph with at least 96 of them: brute force over 4^n assignments.
    Four colours, not three, so answers spread into the hundreds and thousands and five checks cannot guess them."""
    rng = random.Random(f"colorings-{seed}-{level}")
    n, m = {1: (6, 9), 2: (8, 15), 3: (9, 19), 4: (10, 22), 5: (11, 25)}[level]
    while True:
        edges = sorted(rng.sample([(a, b) for a in range(1, n + 1) for b in range(a + 1, n + 1)], m))
        seen, todo = {1}, [1]
        while todo:
            v = todo.pop()
            for a, b in edges:
                for u, w in ((a, b), (b, a)):
                    if u == v and w not in seen:
                        seen.add(w); todo.append(w)
        if len(seen) < n:
            continue
        ans = sum(1 for c in itertools.product(range(4), repeat=n) if all(c[a - 1] != c[b - 1] for a, b in edges))
        if ans >= 96:          # a graph with no or almost no colourings makes a trivial answer
            break
    text = (f"A graph has vertices 1 to {n} and exactly these edges: {', '.join(f'{a}-{b}' for a, b in edges)}. In "
            "how many ways can each vertex be given one of four colours (red, green, blue or yellow) so that the two ends "
            "of every edge get different colours? Colourings that differ only by swapping colour names count as "
            "different, and a colour may go unused.")
    return text, ans


def count_strings(L, k, s):
    """Strings of length L over {A, B, C} with exactly k letters C and no block s: an exact DP whose state is the
    last len(s) - 1 letters and the number of Cs so far (tests check it against brute force)."""
    keep = len(s) - 1
    ways = {("", 0): 1}
    for _ in range(L):
        nxt = {}
        for (tail, c), n in ways.items():
            for ch in "ABC":
                w = tail + ch
                if s in w:
                    continue
                key = (w[-keep:] if keep else "", c + (ch == "C"))
                if key[1] <= k:
                    nxt[key] = nxt.get(key, 0) + n
        ways = nxt
    return sum(n for (_, c), n in ways.items() if c == k)


def strings(seed, level):
    """Strings over {A, B, C} with exactly k letters C and no forbidden block (count_strings)."""
    rng = random.Random(f"strings-{seed}-{level}")
    L = {1: 8, 2: 11, 3: 13, 4: 16, 5: 20}[level]
    k = rng.randrange(2, L // 2)
    s = rng.choice(("AB", "BA", "AA", "ABA", "BAB", "ACB", "BCA", "AAB"))
    ans = count_strings(L, k, s)
    text = (f"How many strings of length {L}, each letter one of A, B or C, contain exactly {k} letters C and never "
            f"contain the block \"{s}\" (those letters consecutively, in that order) anywhere?")
    return text, ans


def knapsack(seed, level):
    """0/1 knapsack optimum: an exact DP over capacity."""
    rng = random.Random(f"knapsack-{seed}-{level}")
    n = {1: 8, 2: 12, 3: 16, 4: 20, 5: 24}[level]
    items = [(rng.randrange(3, 30), rng.randrange(10, 99)) for _ in range(n)]
    W = sum(w for w, _ in items) * 2 // 5
    best = [0] * (W + 1)
    for w, v in items:
        for c in range(W, w - 1, -1):
            best[c] = max(best[c], best[c - w] + v)
    listing = "; ".join(f"item {i + 1}: {w} kg, value {v}" for i, (w, v) in enumerate(items))
    text = (f"A shipment can carry at most {W} kg. These items are available, each at most once: {listing}. What is "
            "the largest total value of items whose total weight is at most the limit?")
    return text, best[W]


GEN = {"paths": paths, "digits": digits, "colorings": colorings, "strings": strings, "knapsack": knapsack}


def make(family, seed, level):
    text, answer = GEN[family](seed, level)
    return {"family": family, "level": level, "seed": seed, "text": text, "answer": int(answer)}
