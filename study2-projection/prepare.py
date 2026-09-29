"""Build test units, training pairs, bins and the recall probe (see PREREG.md).

Needs pyarrow only to read the parquet; everything else is standard library.
"""
import hashlib
import json
import math
import random

import pyarrow.parquet as pq

SEED = 20260929
MIN_PA = 250
PARQUET = "mart_batter_season.parquet"
FEATS = ["woba_c", "gap", "k_rate", "bb_rate", "iso", "babip", "age", "pa600"]
POS_GROUP = {"C": "C", "1B": "IF", "2B": "IF", "3B": "IF", "SS": "IF",
             "LF": "OF", "CF": "OF", "RF": "OF", "DH": "DH"}


def league_woba(rows, season):
    rs = [r for r in rows if r["season"] == season and r["pa"] and r["woba"] is not None]
    return sum(r["woba"] * r["pa"] for r in rs) / sum(r["pa"] for r in rs)


def unit(r, nxt, lg):
    u = {k: r[k] for k in ("player_id", "season", "age", "pa", "woba", "xwoba", "k_rate", "bb_rate",
                           "iso", "babip", "gb_rate", "fb_rate", "pull_air_rate", "sprint_speed",
                           "primary_position")}
    u["lg"] = lg
    u["woba_c"] = r["woba"] - lg
    u["gap"] = r["woba"] - r["xwoba"]
    u["pa600"] = r["pa"] / 600
    u["delta"] = nxt["woba"] - r["woba"]
    return u


def pairs(rows, y, lgs):
    by = {(r["player_id"], r["season"]): r for r in rows}
    out = []
    for (pid, s), r in by.items():
        if s != y or (r["pa"] or 0) < MIN_PA:
            continue
        n = by.get((pid, y + 1))
        if n is None or (n["pa"] or 0) < MIN_PA:
            continue
        if None in (r["woba"], r["xwoba"], r["k_rate"], r["bb_rate"], r["iso"], r["babip"], r["age"], n["woba"]):
            continue
        out.append(unit(r, n, lgs[y]))
    return out


def quantile(xs, q):
    xs = sorted(xs)
    i = q * (len(xs) - 1)
    lo = math.floor(i)
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (i - lo)


def standardise(units, ref):
    mu = {f: sum(u[f] for u in ref) / len(ref) for f in FEATS}
    sd = {f: math.sqrt(sum((u[f] - mu[f]) ** 2 for u in ref) / len(ref)) for f in FEATS}
    return [[(u[f] - mu[f]) / sd[f] for f in FEATS] for u in units]


def main():
    md5 = hashlib.md5(open(PARQUET, "rb").read()).hexdigest()
    rows = pq.read_table(PARQUET).to_pylist()
    lgs = {y: league_woba(rows, y) for y in range(2015, 2027)}
    train = []
    for y in range(2016, 2025):
        if y in (2019, 2020):          # pairs touching the 60-game 2020 season
            continue
        train += pairs(rows, y, lgs)
    test = pairs(rows, 2025, lgs)
    test.sort(key=lambda u: u["player_id"])
    q2025 = [r for r in rows if r["season"] == 2025 and (r["pa"] or 0) >= MIN_PA]
    dropouts = len(q2025) - len(test)
    cuts = [quantile([u["delta"] for u in train], q) for q in (0.2, 0.4, 0.6, 0.8)]
    p_up = sum(u["delta"] > 0 for u in train) / len(train)

    # Recall probe: blend each probed batter with his nearest neighbour among the test batters.
    rng = random.Random(SEED)
    probe_idx = sorted(rng.sample(range(len(test)), 50))
    z = standardise(test, test)
    probe = []
    for i in probe_idx:
        j = min((k for k in range(len(test)) if k != i),
                key=lambda k: sum((a - b) ** 2 for a, b in zip(z[i], z[k])))
        a, b = test[i], test[j]
        m = {}
        for k, v in a.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool) and b.get(k) is not None and v is not None:
                m[k] = (v + b[k]) / 2
            else:
                m[k] = v
        m["primary_position"] = a["primary_position"]
        m["player_id"] = f'{a["player_id"]}+{b["player_id"]}'
        m["src"] = [i, j]
        probe.append(m)

    json.dump({"md5": md5, "lg2025": lgs[2025], "cuts": cuts, "p_up_train": p_up,
               "n_train": len(train), "n_test": len(test), "dropouts": dropouts,
               "probe_idx": probe_idx}, open("frozen.json", "w"), indent=1)
    json.dump(train, open("train.json", "w"))
    json.dump(test, open("test.json", "w"))
    json.dump(probe, open("probe.json", "w"))
    print(f"parquet md5 {md5}")
    print(f"train pairs {len(train)}  test batters {len(test)}  2025 qualifiers without 2026 250 PA: {dropouts}")
    print(f"league wOBA 2025 {lgs[2025]:.4f}  P(up) in train {p_up:.3f}")
    print("bin cut points (delta wOBA):", [round(c, 4) for c in cuts])
    print("test counts per bin:", [sum(1 for u in test if sum(u['delta'] > c for c in cuts) == b) for b in range(5)])
    print("probe_idx", probe_idx[:10], "...")


if __name__ == "__main__":
    main()
