"""Study 3 analysis (frozen with PREREG.md before any scored Jev call).

NUM  = logistic regression on draft-time numbers + role (from Jev, shared by both arms)
TEXT = NUM + six Jev yes/no judgments read from the masked pre-draft report
Outcome = MLB debut by the collection date. Out-of-fold probabilities from 20 repeats of stratified
10-fold CV, averaged per player. Primary: the log-loss difference TEXT - NUM against a floor of the six
features shuffled within role x pick tier (see PREREG.md).
"""
import json
import os
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jevq  # noqa: E402

D = os.environ.get("JEV3_DIR", os.path.expanduser("~/claude-scratch/jev/draft/"))
S = json.load(open(D + "sample.json"))
A = {int(k): v for k, v in json.load(open(D + "answers.json")).items()}
rows = [r for r in S if r["pid"] in A]
print("sample", len(S), "answered", len(rows))
y = np.array([1 if r["debut"] else 0 for r in rows])


def ans(r, k):
    a = A[r["pid"]][k]
    return a["noul"] if a["type"] == "noul" else a["choice"]


def num_block(rs):
    out = []
    for r in rs:
        role = ans(r, "role")
        out.append([
            np.log(r["pick"]),
            np.log(r["rank"]) if r["rank"] else np.log(300.0),
            0.0 if r["rank"] else 1.0,
            np.log(r["pick_value"]) if r["pick_value"] else 0.0,   # slot value, set before the draft
            0.0 if r["pick_value"] else 1.0,                       # no slot (after round 10)
            r["age"],
            1.0 if r["bats"] == "L" else 0.0,
            1.0 if r["bats"] == "S" else 0.0,
            1.0 if r["throws"] == "L" else 0.0,
            1.0 if role == "pitcher" else 0.0,
            1.0 if role == "two_way" else 0.0,
        ] + [1.0 if r["year"] == yy else 0.0 for yy in (2018, 2019, 2020)])
    return np.array(out)


XN = num_block(rows)
XT = np.array([[ans(r, k) for k in jevq.FEATURES] for r in rows])
XR = np.array([[ans(r, "reached")] for r in rows])


def oof(X, repeats=20, seed=0):
    p = np.zeros(len(y))
    for k in range(repeats):
        for tr, te in StratifiedKFold(10, shuffle=True, random_state=seed + k).split(X, y):
            sc = StandardScaler().fit(X[tr])
            m = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(X[tr]), y[tr])
            p[te] += m.predict_proba(sc.transform(X[te]))[:, 1]
    return p / repeats


def ll(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def boot(d, n=5000, seed=1):
    rg = np.random.default_rng(seed)
    b = np.array([d[rg.integers(0, len(d), len(d))].mean() for _ in range(n)])
    return d.mean(), np.percentile(b, 2.5), np.percentile(b, 97.5)


pN = oof(XN)
pT = oof(np.hstack([XN, XT]))
d = ll(pT) - ll(pN)
m, lo, hi = boot(d)

# floor: the six judgments shuffled across players within role x pick tier (200 shuffles, same 20
# CV repeats as the real arms)
role = np.array([ans(r, "role") for r in rows])
tier = np.digitize([r["pick"] for r in rows], [31, 101, 301])
grp = np.array([g + str(t) for g, t in zip(role, tier)])
rg = np.random.default_rng(7)
null = []
for k in range(200):
    XP = XT.copy()
    for g in np.unique(grp):
        ix = np.flatnonzero(grp == g)
        XP[ix] = XT[rg.permutation(ix)]
    null.append((ll(oof(np.hstack([XN, XP]))) - ll(pN)).mean())
null = np.array(null)
p_floor = (1 + (null <= m).sum()) / 201
print("\nlog loss NUM %.4f TEXT %.4f" % (ll(pN).mean(), ll(pT).mean()))
print("AUC     NUM %.4f TEXT %.4f" % (roc_auc_score(y, pN), roc_auc_score(y, pT)))
print("d logloss TEXT-NUM %+.4f  95%% CI [%+.4f, %+.4f]  (secondary: against zero)" % (m, lo, hi))
print("FLOOR (shuffle within role x pick tier, 200): mean %+.4f sd %.4f" % (null.mean(), null.std()))
print("PRIMARY d - floor mean %+.4f ; floor p = %.4f" % (m - null.mean(), p_floor))
print("READING:", "TEXT ADDS" if p_floor < 0.05 else ("TEXT WORSE THAN SHUFFLED" if (1 + (null >= m).sum()) / 201 < 0.05 else "NO GAIN"))

# coefficient signs on the full sample (declared: concern/injury/raw negative, upside/makeup positive)
X = np.hstack([XN, XT])
sc = StandardScaler().fit(X)
cf = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(X), y).coef_[0][XN.shape[1]:]
decl = {"hit_concern": -1, "cmd_concern": -1, "injury": -1, "raw": -1, "upside": 1, "makeup": 1}
for k, c in zip(jevq.FEATURES, cf):
    print("coef %-12s %+.3f  declared %+d  %s" % (k, c, decl[k], "match" if np.sign(c) == decl[k] else "opposite"))

# memory probe: Jev asked directly whether the player reached the majors (never a model input)
print("\nPROBE reached alone AUC %.4f (NUM %.4f)" % (roc_auc_score(y, XR[:, 0]), roc_auc_score(y, pN)))
pR = oof(np.hstack([XN, XT, XR]))
m2, lo2, hi2 = boot(ll(pR) - ll(pT))
print("PROBE added to TEXT: d logloss %+.4f [%+.4f, %+.4f]" % (m2, lo2, hi2))
print("PROBE INFORMATIVE:", "YES" if (hi2 < 0 or roc_auc_score(y, XR[:, 0]) > roc_auc_score(y, pN) + 0.03) else "no")

# sensitivity: without the first 30 picks (the most famous players)
k = np.array([r["pick"] > 30 for r in rows])
print("\nSENS pick>30: n %d  d logloss %+.4f  AUC NUM %.4f TEXT %.4f" % (
    k.sum(), d[k].mean(), roc_auc_score(y[k], pN[k]), roc_auc_score(y[k], pT[k])))
np.savez(D + "oof3.npz", y=y, pN=pN, pT=pT, pR=pR, null=null)
