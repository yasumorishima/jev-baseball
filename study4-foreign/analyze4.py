"""Study 4 analysis, as registered in PREREG.md.

Sample: pillar-1 players (feat_bat.csv / feat_pit.csv from ~/claude-scratch/npbmlb) with MLB pitch data
(column n present) and a pre-arrival Wikipedia text (states.json). Primary outcome rows: NPB first season
>= 100 PA / >= 30 IP (ok100). Arms: NUM (MLB numbers + text-length controls) and TEXT (NUM + five Jev
features of the player's role). Ridge, leave-one-arrival-year-out. Primary: d = MAE_TEXT - MAE_NUM against
a floor that permutes the five Jev columns jointly across players within arrival year.

  python3 analyze4.py                 # real answers (answers.json)
  python3 analyze4.py --synthetic X   # dry run, X in {informative, noise, numonly}: no answers read
"""
import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jevq4  # noqa: E402

NP = os.path.expanduser("~/claude-scratch/npbmlb/")
FD = os.path.expanduser("~/claude-scratch/jev/foreign/")
ALPHA = 10.0
NSHUF = 500
NBOOT = 5000
SEED = 20261002
NUMCOLS = {"bat": ["woba", "xwoba"], "pit": ["kbb", "csw", "start_share"]}
YCOL = {"bat": "Y1", "pit": "P1"}
FEATS = {"bat": jevq4.BAT, "pit": jevq4.PIT}
SIGN = {"power": 1, "contact_concern": -1, "discipline": 1, "injury": -1, "declining": -1,
        "velocity": 1, "put_away": 1, "control_concern": -1}


def load(kind, states):
    rows = []
    for r in csv.DictReader(open(NP + "feat_%s.csv" % kind, encoding="utf-8")):
        k = str(int(float(r["key_mlbam"])))
        if not r["n"].strip() or k not in states:
            continue
        s = states[k]
        L = s.get("ja_full_len", 0) + s.get("en_full_len", 0)
        row = {"pid": k, "year": int(r["year"]), "ok": r["ok100"] == "True",
               "y": float(r[YCOL[kind]]) if r[YCOL[kind]] not in ("", "nan") else np.nan,
               "loglen": np.log1p(L), "has_ja": float(bool(s["ja"])), "has_en": float(bool(s["en"]))}
        for c in NUMCOLS[kind]:
            row[c] = float(r[c])
        rows.append(row)
    return rows


def ridge_oof(X, y, years):
    pred = np.full(len(y), np.nan)
    for fy in np.unique(years):
        tr, te = years != fy, years == fy
        mu, sd = X[tr].mean(0), X[tr].std(0)
        sd[sd == 0] = 1
        Z, Zt = (X[tr] - mu) / sd, (X[te] - mu) / sd
        ym = y[tr].mean()
        b = np.linalg.solve(Z.T @ Z + ALPHA * np.eye(Z.shape[1]), Z.T @ (y[tr] - ym))
        pred[te] = ym + Zt @ b
    return pred


def const_oof(y, years):
    return np.array([y[years != fy].mean() for fy in years])


def run(kind, rows, ans):
    rows = [r for r in rows if r["ok"] and np.isfinite(r["y"]) and r["pid"] in ans]
    y = np.array([r["y"] for r in rows])
    yr = np.array([r["year"] for r in rows])
    N = np.array([[r[c] for c in NUMCOLS[kind] + ["loglen", "has_ja", "has_en"]] for r in rows])
    F = np.array([[ans[r["pid"]][f] for f in FEATS[kind]] for r in rows])
    mae = lambda p: np.mean(np.abs(y - p))
    pn = ridge_oof(N, y, yr)
    pt = ridge_oof(np.hstack([N, F]), y, yr)
    pc = const_oof(y, yr)
    d = mae(pt) - mae(pn)
    rng = np.random.default_rng(SEED + (0 if kind == "bat" else 1))
    floor = []
    for _ in range(NSHUF):
        Fs = F.copy()
        for g in np.unique(yr):
            ix = np.where(yr == g)[0]
            Fs[ix] = F[rng.permutation(ix)]
        floor.append(mae(ridge_oof(np.hstack([N, Fs]), y, yr)) - mae(pn))
    floor = np.array(floor)
    p = (1 + np.sum(floor <= d)) / (NSHUF + 1)
    pm = (1 + np.sum(floor >= d)) / (NSHUF + 1)
    e = np.abs(y - pt) - np.abs(y - pn)
    bs = np.array([e[rng.integers(0, len(e), len(e))].mean() for _ in range(NBOOT)])
    # coefficient signs on the full sample (standardised ridge, same alpha)
    X = np.hstack([N, F])
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1
    Z = (X - mu) / sd
    b = np.linalg.solve(Z.T @ Z + ALPHA * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))[N.shape[1]:]
    return dict(kind=kind, n=len(y), mae_const=mae(pc), mae_num=mae(pn), mae_text=mae(pt), d=d,
                floor_mean=floor.mean(), floor_sd=floor.std(), p=p, p_mirror=pm,
                boot_ci=(np.percentile(bs, 2.5), np.percentile(bs, 97.5)),
                signs={f: (round(float(c), 4), "as declared" if np.sign(c) == SIGN[f] else "opposite")
                       for f, c in zip(FEATS[kind], b)})


def synthetic(mode, rows_by_kind):
    rng = np.random.default_rng(int(os.environ.get("SYN_SEED", "7")))
    ans = {}
    for kind, rows in rows_by_kind.items():
        y = np.array([r["y"] if np.isfinite(r["y"]) else 0 for r in rows])
        z = (y - np.nanmean(y)) / (np.nanstd(y) or 1)
        for i, r in enumerate(rows):
            a = {}
            for f in FEATS[kind]:
                if mode == "informative":
                    a[f] = float(1 / (1 + np.exp(-(SIGN[f] * float(os.environ.get("SYN_C", "1.5")) * z[i] + rng.normal()))))
                elif mode == "numonly":    # a function of what NUM already has
                    a[f] = float(1 / (1 + np.exp(-(r[NUMCOLS[kind][0]] - np.mean([q[NUMCOLS[kind][0]] for q in rows])) * 20)))
                else:
                    a[f] = float(rng.uniform())
            ans[r["pid"]] = a
    return ans


def holm(ps):
    order = np.argsort(ps)
    adj, run_max = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        run_max = max(run_max, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run_max
    return adj


def main():
    states = json.load(open(FD + "states.json", encoding="utf-8"))
    rows = {k: load(k, states) for k in ("bat", "pit")}
    if len(sys.argv) > 2 and sys.argv[1] == "--synthetic":
        ans = synthetic(sys.argv[2], rows)
    else:
        raw = json.load(open(FD + "answers.json"))
        ans = {pid: {f: a[f]["noul"] for f in a if "noul" in a[f]} for pid, a in raw.items()}
    # A role with fewer than 30 answered primary rows gets no reading and does not enter Holm.
    res = []
    for k in ("bat", "pit"):
        n = sum(1 for r in rows[k] if r["ok"] and np.isfinite(r["y"]) and r["pid"] in ans)
        res.append(run(k, rows[k], ans) if n >= 30 else
                   dict(kind=k, n=n, reading="TOO FEW ANSWERED (no reading)"))
    live = [r for r in res if "p" in r]
    for r, pa, pm in zip(live, holm([r["p"] for r in live]), holm([r["p_mirror"] for r in live])):
        r["p_holm"], r["p_mirror_holm"] = pa, pm
        # Holm over the roles with a reading, for both directions. ADDS also needs TEXT to beat NUM
        # outright (d < 0); WORSE also needs d > 0.
        r["reading"] = ("TEXT ADDS" if pa < 0.05 and r["d"] < 0 else
                        "TEXT WORSE THAN SHUFFLED" if pm < 0.05 and r["d"] > 0 else "NO GAIN")
    for r in res:
        print(json.dumps(r, default=lambda o: float(o) if isinstance(o, np.floating) else str(o)))
    if not (len(sys.argv) > 2):
        # Jev's role answer is reported only; the role used is pillar-1 kind
        for kind in ("bat", "pit"):
            want = "hitter" if kind == "bat" else "pitcher"
            rr = [r for r in rows[kind] if r["pid"] in raw]
            print("role agreement", kind, sum(raw[r["pid"]]["role"]["choice"] == want for r in rr), "of", len(rr))
        if not os.path.exists(FD + "probe.json"):
            print("memory probe: not run")
            return
        probe = json.load(open(FD + "probe.json"))
        # memory probe (separate requests, never an input): AUC of the probe for an above-median outcome
        for kind in ("bat", "pit"):
            rr = [r for r in rows[kind] if r["ok"] and np.isfinite(r["y"]) and r["pid"] in probe]
            if len(rr) < 10:
                print("memory probe", kind, "answered", len(rr), "(too few)")
                continue
            y = np.array([r["y"] for r in rr])
            pr = np.array([probe[r["pid"]]["probe_good_japan"]["noul"] for r in rr])
            hi = y > np.median(y)
            P, Nn = pr[hi], pr[~hi]
            auc = (np.sum(P[:, None] > Nn[None, :]) + 0.5 * np.sum(P[:, None] == Nn[None, :])) / (len(P) * len(Nn))
            print("memory probe", kind, "n", len(y), "AUC(above-median outcome)", round(float(auc), 4))


if __name__ == "__main__":
    main()
