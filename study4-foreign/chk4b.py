import json, csv, re
import numpy as np
F = "/home/yasu/claude-scratch/jev/foreign/"
A = json.load(open(F + "answers.json")); S = json.load(open(F + "states.json", encoding="utf-8"))
kind = {}
for k in ("bat", "pit"):
    for r in csv.DictReader(open("/home/yasu/claude-scratch/npbmlb/feat_%s.csv" % k, encoding="utf-8")):
        kind[str(int(float(r["key_mlbam"])))] = k
feats = {"bat": ["power", "contact_concern", "discipline", "injury", "declining"],
         "pit": ["velocity", "put_away", "control_concern", "injury", "declining"]}
for k in ("bat", "pit"):
    ids = [p for p in A if kind.get(p) == k]
    print(k, len(ids), {f: (round(np.mean([A[p][f]["noul"] for p in ids]), 2), round(np.std([A[p][f]["noul"] for p in ids]), 2)) for f in feats[k]})
ids = [p for p in A if kind.get(p) == "pit"]
kw = np.array([bool(re.search(r"(9[5-9]|10[0-5])\s*(mph|MPH|マイル)|1[5-6]\d\s*km", S[p]["ja"] + " " + S[p]["en"])) for p in ids])
v = np.array([A[p]["velocity"]["noul"] for p in ids])
P, N = v[kw], v[~kw]
auc = (np.sum(P[:, None] > N[None, :]) + 0.5 * np.sum(P[:, None] == N[None, :])) / (len(P) * len(N))
print("velocity vs >=95mph/150km keyword: n kw", kw.sum(), "mean", round(P.mean(), 2), round(N.mean(), 2), "AUC", round(auc, 3))
