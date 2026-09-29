"""POST-HOC diagnostics (not pre-registered): where does Jev lose to the baseline?

Reads arms.json and eval_sample.json written by analyze.py / prepare.py.
"""
import json

arms = json.load(open("arms.json"))
sample = json.load(open("eval_sample.json"))
ys = [r["y"] for r in sample]
jev, base = arms["JEV-DIST"], arms["BASE"]


def mean(xs):
    return sum(xs) / len(xs)


print("Calibration by predicted-probability bin (full sample, n=250)")
for name, ps in (("JEV-DIST", jev), ("BASE", base)):
    for lo, hi in ((0, .2), (.2, .4), (.4, .6), (.6, .8), (.8, 1.01)):
        idx = [i for i, p in enumerate(ps) if lo <= p < hi]
        if idx:
            print(f"  {name:8s} p in [{lo:.1f},{min(hi, 1):.1f}]: n={len(idx):3d}  "
                  f"mean p={mean([ps[i] for i in idx]):.2f}  actual={mean([ys[i] for i in idx]):.2f}")

print("\nBy distance on the wrong side of the original call (inches)")
for lo, hi, label in ((-99, -1, "< -1 (clearly agrees with the call)"), (-1, 0, "-1 .. 0"),
                      (0, 1, "0 .. 1"), (1, 99, ">= 1 (clearly contradicts the call)")):
    idx = [i for i, r in enumerate(sample) if lo <= r["wrong_side_in"] < hi]
    print(f"  {label:36s} n={len(idx):3d}  actual={mean([ys[i] for i in idx]):.2f}  "
          f"Jev={mean([jev[i] for i in idx]):.2f}  BASE={mean([base[i] for i in idx]):.2f}")
