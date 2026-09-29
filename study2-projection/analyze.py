"""Score Jev and the comparators exactly as PREREG.md declares. Standard library only."""
import json
import math
import random

SEED = 20260929
FEATS = ["woba_c", "gap", "k_rate", "bb_rate", "iso", "babip", "age", "pa600"]
GRID = [10, 20, 50, 100, 300]
DRAWS = 200
LAMBDA = 1.0


def ncdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def bin_of(d, cuts):
    return sum(d > c for c in cuts)


def normal_bins(mu, s, cuts):
    cdf = [ncdf((c - mu) / s) for c in cuts]
    return [cdf[0]] + [cdf[k] - cdf[k - 1] for k in range(1, 4)] + [1 - cdf[3]]


def rps(probs, b):
    cp, tot = 0.0, 0.0
    for k in range(4):
        cp += probs[k]
        tot += (cp - (1.0 if b <= k else 0.0)) ** 2
    return tot / 4


def mean(xs):
    return sum(xs) / len(xs)


def solve(a, b):
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(m[r][c]))
        m[c], m[p] = m[p], m[c]
        for r in range(n):
            if r != c:
                f = m[r][c] / m[c][c]
                m[r] = [x - f * y for x, y in zip(m[r], m[c])]
    return [m[i][n] / m[i][i] for i in range(n)]


def fit_ridge(units):
    mu = {f: mean([u[f] for u in units]) for f in FEATS}
    sd = {f: math.sqrt(mean([(u[f] - mu[f]) ** 2 for u in units])) or 1.0 for f in FEATS}
    xs = [[(u[f] - mu[f]) / sd[f] for f in FEATS] for u in units]
    ys = [u["delta"] for u in units]
    ybar = mean(ys)
    p = len(FEATS)
    a = [[sum(x[i] * x[j] for x in xs) + (LAMBDA if i == j else 0) for j in range(p)] for i in range(p)]
    b = [sum(x[i] * (y - ybar) for x, y in zip(xs, ys)) for i in range(p)]
    w = solve(a, b)
    res = [y - ybar - sum(wi * xi for wi, xi in zip(w, x)) for x, y in zip(xs, ys)]
    s = max(math.sqrt(sum(r * r for r in res) / max(len(res) - 1, 1)), 0.005)

    def predict(u):
        return ybar + sum(wi * (u[f] - mu[f]) / sd[f] for wi, f in zip(w, FEATS)), s
    return predict


def marcel(u):
    lg = u["lg"]
    proj = lg + u["pa"] / (u["pa"] + 600) * (u["woba"] - lg)
    age = u["age"]
    proj *= (1 + 0.006 * (29 - age)) if age < 29 else (1 - 0.003 * (age - 29))
    return proj - u["woba"]


def boot(a, b, n=10000):
    rng = random.Random(SEED)
    idx = range(len(a))
    ds = sorted(mean([a[i] - b[i] for i in s]) for s in ([rng.choice(idx) for _ in idx] for _ in range(n)))
    return mean([x - y for x, y in zip(a, b)]), ds[int(0.025 * n)], ds[int(0.975 * n) - 1]


def main():
    fz = json.load(open("frozen.json"))
    cuts, p_up_train = fz["cuts"], fz["p_up_train"]
    train, test, probe = (json.load(open(f)) for f in ("train.json", "test.json", "probe.json"))
    jev = {}
    for a in map(json.loads, open("jev_answers.jsonl")):
        jev[(a["set"], a["idx"])] = a
    tb = [bin_of(u["delta"], cuts) for u in test]
    up = [1 if u["delta"] > 0 else 0 for u in test]
    done = [i for i in range(len(test)) if ("test", i) in jev]
    if len(done) < len(test):
        print(f"PARTIAL: Jev answered {len(done)}/{len(test)} test batters; all arms scored on those rows")

    def per_row(pred_bins, pred_up):
        return ([rps(pred_bins[i], tb[i]) for i in done], [(pred_up[i] - up[i]) ** 2 for i in done])

    arms = {}
    arms["JEV"] = per_row({i: jev[("test", i)]["bin_probs"] for i in done},
                          {i: jev[("test", i)]["p_up"] for i in done})
    arms["CLIM"] = per_row({i: [0.2] * 5 for i in done}, {i: p_up_train for i in done})
    s_m = math.sqrt(mean([(u["delta"] - marcel(u)) ** 2 for u in train]))
    arms["MARCEL-LITE"] = per_row({i: normal_bins(marcel(test[i]), s_m, cuts) for i in done},
                                  {i: 1 - ncdf(-marcel(test[i]) / s_m) for i in done})
    full = fit_ridge(train)

    def ridge_rows(pred):
        return per_row({i: normal_bins(*pred(test[i]), cuts) for i in done},
                       {i: 1 - ncdf(-pred(test[i])[0] / pred(test[i])[1]) for i in done})
    arms["RIDGE(all)"] = ridge_rows(full)

    print(f"test batters {len(test)} (scored {len(done)}), train pairs {len(train)}, dropouts {fz['dropouts']}")
    print(f"{'arm':12s} {'RPS':>7s} {'Brier(up)':>10s}")
    for k, (r, b) in arms.items():
        print(f"{k:12s} {mean(r):7.4f} {mean(b):10.4f}")

    print("\nRIDGE(n) learning curve (RPS over 200 random training draws)")
    rng = random.Random(SEED)
    curve = {}
    for n in GRID:
        vals = []
        for _ in range(DRAWS):
            pred = fit_ridge(rng.sample(train, n))
            vals.append(mean(ridge_rows(pred)[0]))
        vals.sort()
        curve[n] = mean(vals)
        print(f"  n={n:4d}  mean {mean(vals):.4f}  2.5-97.5% [{vals[int(0.025*DRAWS)]:.4f}, {vals[int(0.975*DRAWS)-1]:.4f}]")
    curve["all"] = mean(arms["RIDGE(all)"][0])
    print(f"  n= all  {curve['all']:.4f}")

    jr = mean(arms["JEV"][0])
    print("\nPaired bootstrap, RPS(JEV) - RPS(other):")
    for k in ("CLIM", "MARCEL-LITE", "RIDGE(all)"):
        d, lo, hi = boot(arms["JEV"][0], arms[k][0])
        print(f"  vs {k:12s} {d:+.4f}  95% [{lo:+.4f}, {hi:+.4f}]")
    print("Paired bootstrap, Brier(up)(JEV) - Brier(up)(other):")
    for k in ("CLIM", "MARCEL-LITE", "RIDGE(all)"):
        d, lo, hi = boot(arms["JEV"][1], arms[k][1])
        print(f"  vs {k:12s} {d:+.4f}  95% [{lo:+.4f}, {hi:+.4f}]")

    d_c = boot(arms["JEV"][0], arms["CLIM"][0])
    d_m = boot(arms["JEV"][0], arms["MARCEL-LITE"][0])
    cross = next((n for n in GRID + ["all"] if curve[n] <= jr), None)
    print("\nPre-declared reading:")
    if not d_c[2] < 0:
        print("  -> Jev shows no skill (RPS interval vs CLIM not entirely below 0)")
    elif d_m[1] > 0:
        print("  -> Jev is worse than a textbook rule (MARCEL-LITE)")
    else:
        label = ("never within the grid" if cross is None else f"n = {cross}")
        tier = ("Jev carries substantial baseball prior knowledge" if cross in (300, "all", None)
                else "Jev ~ a prior worth tens of seasons of examples" if cross in (50, 100)
                else "Jev ~ a crude prior")
        print(f"  -> crossover {label}: {tier}")

    # Recall probe
    pdone = [i for i in range(len(probe)) if ("probe", i) in jev]
    if pdone:
        src = [probe[i]["src"][0] for i in pdone]
        if all(("test", s) in jev for s in src):
            pb = [bin_of(probe[i]["delta"], cuts) for i in pdone]
            j_bl = [rps(jev[("probe", i)]["bin_probs"], b) for i, b in zip(pdone, pb)]
            j_or = [rps(jev[("test", s)]["bin_probs"], tb[s]) for s in src]
            r_bl = [rps(normal_bins(*full(probe[i]), cuts), b) for i, b in zip(pdone, pb)]
            r_or = [rps(normal_bins(*full(test[s]), cuts), tb[s]) for s in src]
            dj = [a - b for a, b in zip(j_bl, j_or)]
            dr = [a - b for a, b in zip(r_bl, r_or)]
            d, lo, hi = boot(dj, dr)
            print(f"\nRecall probe (n={len(pdone)}): dRPS Jev {mean(dj):+.4f}, RIDGE(all) {mean(dr):+.4f}; "
                  f"difference {d:+.4f} 95% [{lo:+.4f}, {hi:+.4f}]")
            print("  -> evidence that Jev recalled players" if lo > 0 else "  -> no evidence of recall")
    json.dump({k: v for k, v in arms.items()}, open("arms.json", "w"))


if __name__ == "__main__":
    main()
