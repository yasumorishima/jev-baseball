"""How much did Study 1 miss? The original extractor read reviewDetails only on the pitch event, so
challenges whose final call ended the plate appearance (the review sits on the play) were dropped.
Compare, for Aug 1 - Sep 27 2026, the old set (review on the pitch) with the full set, and re-score the
distance-only baseline on the full September set. Jev is not re-asked (no calls).
Run in ~/claude-scratch/absdeep with the merged challenges file.
"""
import json
import math
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/yasu/claude-scratch/jev-baseball")
from prepare import load

rows, dropped = load(sys.argv[1] if len(sys.argv) > 1 else "challenges_all.jsonl")
d = pd.DataFrame(rows)
d = d[(d.date >= "2026-08-01") & (d.date <= "2026-09-27")]
print(f"Aug-Sep rows {len(d)} (dropped {dropped}); review on pitch {int((d.review_on == 'pitch').sum())}, on play {int((d.review_on == 'play').sum())}")
print(d.groupby("review_on").agg(n=("y", "size"), overturned=("y", "mean")).round(3))
d["decides"] = np.where(d.original_call == "strike", d.strikes == 2, d.balls == 3)
print("play-level rows: share where the final call ends the PA:",
      round(((d.review_on == "play") & ((d.y == 1) != d.decides) | (d.review_on == "play") & (d.y == 1) & d.decides).mean(), 3))
print(pd.crosstab([d.review_on, d.original_call], d.y, margins=True))

# distance-only baseline: fit on August (full), score September (full) and September (old set only)
tr, ev = d[d.date < "2026-09-01"], d[d.date >= "2026-09-01"]


def fit(x, y, lam=0.01, it=200):
    w = np.zeros(2)
    X = np.c_[np.ones(len(x)), x]
    for _ in range(it):
        p = 1 / (1 + np.exp(-X @ w))
        g = X.T @ (p - y) + lam * np.r_[0, w[1]]
        H = X.T @ (X * (p * (1 - p))[:, None]) + lam * np.diag([0, 1])
        w -= np.linalg.solve(H, g)
    return w


for name, t in (("old set (pitch only)", tr[tr.review_on == "pitch"]), ("full set", tr)):
    w = fit(t.wrong_side_in.values, t.y.values)
    for ename, e in (("Sep old set", ev[ev.review_on == "pitch"]), ("Sep full", ev)):
        p = 1 / (1 + np.exp(-(w[0] + w[1] * e.wrong_side_in.values)))
        print(f"fit on Aug {name:20s} w={np.round(w, 3)} -> {ename:12s} n {len(e):4d} Brier {np.mean((p - e.y.values) ** 2):.4f} overturned {e.y.mean():.3f}")
