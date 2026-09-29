"""Score every arm on the 250 evaluation rows (see PREREG.md). Standard library only."""
import json
import math
import random

SEED = 20260929
EPS = 1e-6


RIDGE = 0.01   # pre-declared L2 penalty on both coefficients (keeps the fit finite under separation)


def sigmoid(t):
    if t >= 0:
        return 1 / (1 + math.exp(-t))
    e = math.exp(t)
    return e / (1 + e)


def fit_logistic(xs, ys, iters=200):
    a, b = 0.0, 0.0
    for _ in range(iters):
        ga, gb = -RIDGE * a, -RIDGE * b
        haa = hbb = RIDGE
        hab = 0.0
        for x, y in zip(xs, ys):
            p = sigmoid(a + b * x)
            ga += y - p
            gb += (y - p) * x
            w = p * (1 - p)
            haa += w
            hab += w * x
            hbb += w * x * x
        det = haa * hbb - hab * hab
        da = (hbb * ga - hab * gb) / det
        db = (haa * gb - hab * ga) / det
        a += da
        b += db
        if abs(da) < 1e-10 and abs(db) < 1e-10:
            break
    return a, b


def auc(ps, ys):
    pairs = sorted(zip(ps, ys))
    ranks, i = [0.0] * len(pairs), 0
    while i < len(pairs):
        j = i
        while j < len(pairs) and pairs[j][0] == pairs[i][0]:
            j += 1
        for k in range(i, j):
            ranks[k] = (i + j + 1) / 2          # midrank
        i = j
    npos = sum(ys)
    nneg = len(ys) - npos
    rpos = sum(r for r, (_, y) in zip(ranks, pairs) if y)
    return (rpos - npos * (npos + 1) / 2) / (npos * nneg)


def brier(ps, ys):
    return sum((p - y) ** 2 for p, y in zip(ps, ys)) / len(ys)


def logloss(ps, ys):
    return -sum(y * math.log(max(p, EPS)) + (1 - y) * math.log(max(1 - p, EPS))
                for p, y in zip(ps, ys)) / len(ys)


def acc(ps, ys):
    return sum((p >= 0.5) == bool(y) for p, y in zip(ps, ys)) / len(ys)


def boot_diff(pa, pb, ys, fn, n=10000):
    rng = random.Random(SEED)
    idx = range(len(ys))
    ds = []
    for _ in range(n):
        s = [rng.choice(idx) for _ in idx]
        ds.append(fn([pa[i] for i in s], [ys[i] for i in s]) - fn([pb[i] for i in s], [ys[i] for i in s]))
    ds.sort()
    return fn(pa, ys) - fn(pb, ys), ds[int(0.025 * n)], ds[int(0.975 * n) - 1]


def main():
    train = json.load(open("train.json"))
    sample = json.load(open("eval_sample.json"))
    ys = [r["y"] for r in sample]
    a, b = fit_logistic([r["wrong_side_in"] for r in train], [r["y"] for r in train])
    base = [sigmoid(a + b * r["wrong_side_in"]) for r in sample]
    rule = [1.0 if r["wrong_side_in"] > 0 else 0.0 for r in sample]
    jev = {}
    for line in open("jev_answers.jsonl"):
        x = json.loads(line)
        jev.setdefault(x["arm"], {})[x["idx"]] = x["p"]
    print(f"BASE fit on train n={len(train)}: logit = {a:.3f} + {b:.3f} * wrong_side_in  (ridge {RIDGE})")
    print(f"eval sample n={len(ys)} overturned={sum(ys)}")

    def table(idx, label):
        yy = [ys[i] for i in idx]
        arms = {"BASE": [base[i] for i in idx], "RULE": [rule[i] for i in idx]}
        for k in ("JEV-DIST", "JEV-RAW"):
            if k in jev and all(i in jev[k] for i in idx):
                arms[k] = [jev[k][i] for i in idx]
        print(f"\n[{label}] n={len(idx)} overturned={sum(yy)}")
        print(f"{'arm':10s} {'Brier':>7s} {'AUC':>6s} {'logloss':>8s} {'acc':>6s}")
        for k, ps in arms.items():
            if k == "RULE":
                print(f"{k:10s} {'-':>7s} {'-':>6s} {'-':>8s} {acc(ps, yy):6.3f}")
            else:
                print(f"{k:10s} {brier(ps, yy):7.4f} {auc(ps, yy):6.3f} {logloss(ps, yy):8.4f} {acc(ps, yy):6.3f}")
        for k in ("JEV-DIST", "JEV-RAW"):
            if k in arms:
                d, lo, hi = boot_diff(arms[k], arms["BASE"], yy, brier)
                print(f"Brier({k}) - Brier(BASE) = {d:+.4f}  95% [{lo:+.4f}, {hi:+.4f}]")
        if "JEV-DIST" in arms and "JEV-RAW" in arms:
            d, lo, hi = boot_diff(arms["JEV-RAW"], arms["JEV-DIST"], yy, brier)
            print(f"Brier(JEV-RAW) - Brier(JEV-DIST) = {d:+.4f}  95% [{lo:+.4f}, {hi:+.4f}]")
        return arms

    # Pre-declared: if an arm is incomplete, it is scored on the rows it completed,
    # paired with BASE on exactly those rows.
    for k in ("JEV-DIST", "JEV-RAW"):
        n = len(jev.get(k, {}))
        if 0 < n < len(sample):
            table(sorted(jev[k]), f"{k} partial: completed rows only")
    arms = table(list(range(len(sample))), "full sample")
    json.dump(arms, open("arms.json", "w"))


if __name__ == "__main__":
    main()
