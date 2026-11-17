"""Write a JSONL of labores specs. Usage:
  python3.12 scripts/build.py OUT.jsonl --families paths,digits --levels 1,2,3 --seeds 1-4 \
      --beneficiaries principal,teammate --principals E --arms neutral [--tier calibration]
"""
import argparse, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from labores import agentic, episodes, problems  # noqa: E402


def span(text):
    a, _, b = text.partition("-")
    return range(int(a), int(b or a) + 1)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--families", default=",".join(agentic.FAMILIES))
    ap.add_argument("--levels", default="1,2,3"); ap.add_argument("--seeds", default="1-4")
    ap.add_argument("--level-map", help="family=level,... overrides --levels per family")
    ap.add_argument("--beneficiaries", default="principal"); ap.add_argument("--principals", default="E")
    ap.add_argument("--arms", default="neutral"); ap.add_argument("--tier", default="pilot")
    ap.add_argument("--native", action="store_true",
                    help="castra-native layout: authenticated principal channel and engine-scored `solved` (anulus v0.2 bases)")
    ap.add_argument("--voice", default="third", choices=("third", "first"),
                    help="request wording: both beneficiaries named in the third person (default), or the pilot's first person")
    a = ap.parse_args(argv)
    arms = json.load(open(ROOT / "config" / "arms.json"))["arms"]
    lmap = dict(kv.split("=") for kv in a.level_map.split(",")) if a.level_map else {}
    out = []
    for fam in a.families.split(","):
        levels = [int(lmap[fam])] if fam in lmap else [int(x) for x in a.levels.split(",")]
        for lv in levels:
            for seed in span(a.seeds):
                is_agentic = fam in agentic.FAMILIES
                p = agentic.make(fam, seed, lv) if is_agentic else problems.make(fam, seed, lv)
                for arm in a.arms.split(","):
                    for b in a.beneficiaries.split(","):
                        for pk in a.principals.split(","):
                            build = episodes.agentic_spec if is_agentic else episodes.spec
                            kw = {"voice": a.voice, "native": a.native} if is_agentic else {}
                            out.append(build(p, b, pk, arm, arms[arm], tier=a.tier, **kw))
    episodes.write(a.out, out)
    print(f"{len(out)} specs -> {a.out}")


if __name__ == "__main__":
    main(sys.argv[1:])
