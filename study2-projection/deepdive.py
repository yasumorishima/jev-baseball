"""POST-HOC deep dive for the write-up (not pre-registered; no new Jev calls).

1. Direction: Jev's expected change vs the actual change, next to MARCEL-LITE (scatter data).
2. Why: how much weight Jev puts on regression to the mean and on luck (wOBA - xwOBA), compared with
   the weights the 1,620 training pairs support.
3. Spread: if Jev's direction is kept and only the width is repaired, how good does it get?
   a) JEV-CENTER: Normal(Jev's expected change, s) with s = the training residual sd of MARCEL-LITE.
   b) JEV-TEMP: Jev's bins sharpened/flattened p^(1/T) and mixed with 20% bins, (T, w) chosen by
      10-fold cross-validation over the 227 test batters (each fold scored with parameters fitted
      on the other nine folds).
4. Named examples (public data) for the article.
Run in the data directory (test.json, train.json, frozen.json, jev_answers.jsonl, mart parquet).
"""
import json
import math
import random

import numpy as np
import pandas as pd

from analyze import marcel, normal_bins, rps, bin_of

test = json.load(open("test.json"))
train = json.load(open("train.json"))
fz = json.load(open("frozen.json"))
cuts = fz["cuts"]
J = {a["idx"]: a for a in map(json.loads, open("jev_answers.jsonl")) if a["set"] == "test"}
n = len(test)
assert sorted(J) == list(range(n))
P = np.array([J[i]["bin_probs"] for i in range(n)], float)
P = P / P.sum(1, keepdims=True)
d = np.array([u["delta"] for u in test])
b = np.array([bin_of(x, cuts) for x in d])
mar = np.array([marcel(u) for u in test])

# bin -> typical change, from the training pairs only
td = np.array([u["delta"] for u in train])
tb = np.array([bin_of(x, cuts) for x in td])
bin_mean = np.array([td[tb == k].mean() for k in range(5)])
jev_delta = P @ bin_mean                                # Jev's expected change in wOBA
print("bin means from training pairs (wOBA points):", np.round(bin_mean * 1000, 1))


def corr(x, y):
    return float(np.corrcoef(x, y)[0, 1])


print("\n1. Direction (correlation with the actual change)")
print(f"  Jev expected change {corr(jev_delta, d):.3f}  MARCEL-LITE {corr(mar, d):.3f}")
print(f"  sd of forecasts: Jev {jev_delta.std() * 1000:.1f}  MARCEL-LITE {mar.std() * 1000:.1f}  actual change {d.std() * 1000:.1f} (points)")
np.savetxt("scatter_jev_marcel.csv", np.c_[jev_delta, mar, d], delimiter=",",
           header="jev_expected_delta,marcel_delta,actual_delta", comments="")

print("\n2. Weights on regression to the mean (woba_c) and luck (gap), both in wOBA points per point")
X = lambda us: np.c_[np.ones(len(us)), [u["woba_c"] for u in us], [u["gap"] for u in us]]
w_train, *_ = np.linalg.lstsq(X(train), td, rcond=None)
w_jev, *_ = np.linalg.lstsq(X(test), jev_delta, rcond=None)
w_mar, *_ = np.linalg.lstsq(X(test), mar, rcond=None)
w_test, *_ = np.linalg.lstsq(X(test), d, rcond=None)
for name, w in (("training pairs (actual)", w_train), ("test batters (actual)", w_test),
                ("Jev", w_jev), ("MARCEL-LITE", w_mar)):
    print(f"  {name:24s} woba_c {w[1]:+.3f}  gap {w[2]:+.3f}")

print("\n3. Repairing only the width (RPS, lower is better)")
res_sd = float(np.std([u["delta"] - marcel(u) for u in train]))
base = {"JEV": np.mean([rps(P[i], b[i]) for i in range(n)]),
        "MARCEL-LITE": np.mean([rps(normal_bins(mar[i], res_sd, cuts), b[i]) for i in range(n)])}
center = np.array([rps(normal_bins(jev_delta[i], res_sd, cuts), b[i]) for i in range(n)])
print(f"  JEV {base['JEV']:.4f} | MARCEL-LITE {base['MARCEL-LITE']:.4f} (s = {res_sd * 1000:.1f} points)")
print(f"  JEV-CENTER (Jev's expected change, MARCEL-LITE's width) {center.mean():.4f}")


def temp(p, T, w):
    q = p ** (1 / T)
    q = q / q.sum(1, keepdims=True)
    return (1 - w) * q + w * 0.2


grid = [(T, w) for T in np.arange(0.5, 4.01, 0.1) for w in np.arange(0, 0.81, 0.05)]
rng = random.Random(20260929)
order = list(range(n))
rng.shuffle(order)
folds = [order[k::10] for k in range(10)]
cv = np.zeros(n)
chosen = []
for f in folds:
    tr = [i for i in range(n) if i not in f]
    best = min(grid, key=lambda g: np.mean([rps(r, b[i]) for i, r in zip(tr, temp(P[tr], *g))]))
    chosen.append(best)
    for i, r in zip(f, temp(P[f], *best)):
        cv[i] = rps(r, b[i])
print(f"  JEV-TEMP (10-fold CV) {cv.mean():.4f}; chosen (T, w) per fold: "
      + ", ".join(f"({t:.1f},{w:.2f})" for t, w in chosen))
full = min(grid, key=lambda g: np.mean([rps(r, b[i]) for i, r in enumerate(temp(P, *g))]))
print(f"  (T, w) on all 227, for the chart only: ({full[0]:.1f}, {full[1]:.2f})")
tp = temp(P, *full)
print("  bin shares after the repair:", np.round(tp.mean(0), 3), " actual:", np.round(np.bincount(b, minlength=5) / n, 3))

rngb = np.random.default_rng(20260929)
mrow = np.array([rps(normal_bins(mar[i], res_sd, cuts), b[i]) for i in range(n)])
for name, a in (("JEV-CENTER", center), ("JEV-TEMP", cv)):
    diffs = [(a[s] - mrow[s]).mean() for s in (rngb.integers(0, n, n) for _ in range(10000))]
    print(f"  {name} - MARCEL-LITE {np.mean(a - mrow):+.4f}  95% [{np.percentile(diffs, 2.5):+.4f}, {np.percentile(diffs, 97.5):+.4f}]")

print("\n4. Examples")
m = pd.read_parquet("mart_batter_season.parquet")
names = dict(zip(m.player_id, m.player_name))
rows = []
for i, u in enumerate(test):
    rows.append(dict(i=i, name=names.get(u["player_id"], "?"), age=u["age"], pa=u["pa"], woba=u["woba"],
                     xwoba=u["xwoba"], gap=u["gap"], delta=u["delta"], bin=int(b[i]),
                     jev=" ".join(f"{x:.2f}" for x in P[i]), jev_d=jev_delta[i], mar=mar[i]))
df = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print("  biggest drops:\n", df.nsmallest(6, "delta").to_string(index=False))
print("  biggest rises:\n", df.nlargest(6, "delta").to_string(index=False))
print("  largest luck (wOBA - xwOBA):\n", df.nlargest(6, "gap").to_string(index=False))
print("  most negative luck:\n", df.nsmallest(6, "gap").to_string(index=False))
