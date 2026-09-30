# Japanese charts for the Qiita article, Japanese-manufacturer-deck style:
# one message per chart, the message is the title, direct labels, no gridlines, one accent color.
# Numbers are copied from results/analyze_output.txt, results/diagnose_output.txt (Study 1)
# and study2-projection/results/{analyze,diagnose}_output.txt (Study 2).
import os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ORANGE, GRAY, INK, SUB, LIGHT = "#e4560f", "#b9b8b3", "#0b0b0b", "#52514e", "#dedcd6"
plt.rcParams["font.family"] = "DejaVu Sans"
OUT = "blog_ja"
os.makedirs(OUT, exist_ok=True)

def base(ax, left=False):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(left and s == "left")
    ax.spines["bottom"].set_color(GRAY)
    ax.tick_params(colors=SUB, length=0)

def title(fig, text, note=None):
    fig.text(0.04, 0.95, text, fontsize=19, color=INK, ha="left", va="top", weight="bold")
    if note:
        fig.text(0.04, 0.875, note, fontsize=13, color=SUB, ha="left", va="top")

# 1. Study 1: clear pitches, actual overturn share vs Jev's average probability
fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
fig.subplots_adjust(top=0.72, left=0.30, right=0.92, bottom=0.08)
rows = [("Wrong side of the call\nby 1 in or more (82)", 0.99, 0.65),
        ("Called side\nby more than 1 in (63)", 0.00, 0.18)]
for i, (lab, act, jev) in enumerate(rows):
    y = 1 - i
    ax.barh(y + 0.17, act, height=0.32, color=GRAY)
    ax.barh(y - 0.17, jev, height=0.32, color=ORANGE)
    ax.text(act + 0.015, y + 0.17, f"Actual {act*100:.0f}%", va="center", fontsize=14, color=SUB)
    ax.text(jev + 0.015, y - 0.17, f"Jev {jev*100:.0f}%", va="center", fontsize=14, color=ORANGE, weight="bold")
ax.set_yticks([1, 0]); ax.set_yticklabels([r[0] for r in rows], fontsize=14)
ax.set_xlim(0, 1.15); ax.set_xticks([])
base(ax); ax.spines["bottom"].set_visible(False)
title(fig, "Even on clear pitches, Jev's probabilities stay moderate", "250 ABS challenges (Sep 2026). Gray = share overturned, orange = Jev's average probability")
fig.savefig(f"{OUT}/en_1_abs.png"); plt.close(fig)

# 2. Study 2: improvement over guessing (RPS of guessing minus RPS of each method)
clim = 0.1945
arms = [("Fitted on 20 examples", 0.1904, GRAY), ("Jev (no examples)", 0.1795, ORANGE),
        ("Fitted on 50 examples", 0.1608, GRAY), ("Marcel-style rule", 0.1489, GRAY),
        ("Fitted on 1,620 examples", 0.1454, GRAY)]
fig, ax = plt.subplots(figsize=(10, 5.8), dpi=150)
fig.subplots_adjust(top=0.72, left=0.28, right=0.92, bottom=0.08)
n = len(arms)
for i, (lab, rps, c) in enumerate(arms):
    v = clim - rps; y = n - 1 - i
    ax.barh(y, v, color=c, height=0.58)
    ax.text(v + 0.0008, y, f"{v:.3f}", va="center", fontsize=15, color=ORANGE if c == ORANGE else SUB,
            weight="bold" if c == ORANGE else "normal")
ax.set_yticks(range(n)[::-1]); ax.set_yticklabels([a[0] for a in arms], fontsize=14)
for t, a in zip(ax.get_yticklabels(), arms):
    if a[2] == ORANGE:
        t.set_color(ORANGE); t.set_weight("bold")
ax.set_xlim(0, 0.058); ax.set_xticks([])
base(ax); ax.spines["bottom"].set_visible(False)
title(fig, "Jev's gain over guessing is a third of the Marcel-style rule's", "227 hitters. How far below guessing's RPS of 0.195 (bigger is better)")
fig.savefig(f"{OUT}/en_2_gain.png"); plt.close(fig)

# 3. Study 2: learning curve
ns = [10, 20, 50, 100, 300, 1620]
mean = [0.2203, 0.1904, 0.1608, 0.1529, 0.1475, 0.1454]
lo = [0.1659, 0.1565, 0.1471, 0.1451, 0.1436, 0.1454]
hi = [0.3141, 0.2423, 0.1836, 0.1651, 0.1525, 0.1454]
fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
fig.subplots_adjust(top=0.78, left=0.1, right=0.80, bottom=0.14)
ax.fill_between(ns, lo, hi, color=LIGHT, lw=0)
ax.plot(ns, mean, color=SUB, lw=3, marker="o", ms=7)
ax.axhline(0.1795, color=ORANGE, lw=3)
ax.axvspan(20, 50, color=ORANGE, alpha=0.08, lw=0)
ax.text(1800, 0.1795, "Jev (no examples)", color=ORANGE, fontsize=14, va="center", weight="bold")
ax.text(1800, 0.1470, "Model fitted\non past examples", color=SUB, fontsize=14, va="bottom")
ax.set_xscale("log"); ax.set_xticks(ns); ax.set_xticklabels([f"{v:,}" for v in ns], fontsize=13)
ax.minorticks_off(); ax.set_xlim(8.5, 1650)
ax.set_ylim(0.14, 0.26); ax.set_yticks([0.15, 0.20, 0.25]); ax.tick_params(axis="y", labelsize=13)
ax.set_xlabel("Number of past examples the model learned from (log scale)", fontsize=14, color=SUB)
ax.set_ylabel("RPS (lower is better)", fontsize=14, color=SUB)
base(ax, left=False)
title(fig, "Jev is worth a model fitted on 20 to 50 past examples", "Gray band = 95% range over 200 random draws of the examples")
fig.savefig(f"{OUT}/en_3_curve.png"); plt.close(fig)

# 4. Study 2: spread
bins = ["Big\ndrop", "Small\ndrop", "About\nsame", "Small\nrise", "Big\nrise"]
act = [c / 227 for c in (33, 52, 50, 41, 51)]   # counts behind 0.145/0.229/0.220/0.181/0.225
jev = [0.020, 0.221, 0.329, 0.343, 0.086]
fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
fig.subplots_adjust(top=0.74, left=0.06, right=0.97, bottom=0.14)
x = range(5); w = 0.38
for i in x:
    ax.bar(i - w/2, act[i], w, color=GRAY); ax.bar(i + w/2, jev[i], w, color=ORANGE)
    ax.text(i - w/2, act[i] + 0.008, f"{round(act[i]*100 + 1e-9):.0f}%", ha="center", fontsize=13, color=SUB)
    ax.text(i + w/2, jev[i] + 0.008, f"{jev[i]*100:.0f}%", ha="center", fontsize=13, color=ORANGE, weight="bold")
ax.set_xticks(list(x)); ax.set_xticklabels(bins, fontsize=14); ax.set_yticks([]); ax.set_ylim(0, 0.39)
base(ax)
fig.text(0.04, 0.83, "■ What actually happened", fontsize=13, color=SUB, ha="left", va="top")
fig.text(0.30, 0.83, "■ Jev's average probability", fontsize=13, color=ORANGE, ha="left", va="top")
title(fig, "Jev rarely expects big moves")
fig.savefig(f"{OUT}/en_4_spread.png"); plt.close(fig)
print("ok")

# ---- deep-dive charts (numbers from study2-projection/results/deepdive_output.txt and results/diagnose_output.txt) ----
# 1b. Study 1: overturn share by distance band
bands = ["Called side\nmore than 1 in", "Called side\nwithin 1 in", "Wrong side\nwithin 1 in", "Wrong side\n1 in or more"]
actual_b, jev_b, base_b = [0.00, 0.58, 0.64, 0.99], [0.18, 0.23, 0.60, 0.65], [0.02, 0.32, 0.77, 0.98]
fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
fig.subplots_adjust(top=0.74, left=0.08, right=0.84, bottom=0.16)
for vals, c, lab, lw in ((actual_b, INK, "Actual", 3), (base_b, GRAY, "Formula", 3), (jev_b, ORANGE, "Jev", 3.5)):
    ax.plot(range(4), vals, color=c, lw=lw, marker="o", ms=8)
    ax.text(3.12, vals[-1] + (0.035 if lab == "Formula" else -0.035 if lab == "Actual" else 0), f"{lab} {vals[-1]*100:.0f}%",
            color=c if c != GRAY else SUB, fontsize=14, va="center", weight="bold" if c == ORANGE else "normal")
ax.set_xticks(range(4)); ax.set_xticklabels(bands, fontsize=13); ax.set_ylim(-0.03, 1.05)
ax.set_yticks([0, 0.5, 1.0]); ax.set_yticklabels(["0%", "50%", "100%"], fontsize=13)
base(ax)
title(fig, "On clear-cut pitches, only Jev stays hesitant", "250 ABS challenges (Sep 2026). Share overturned, and each forecast's average")
fig.savefig(f"{OUT}/en_1b_bands.png"); plt.close(fig)

# 5. Study 2: forecast vs actual change (scatter)
import numpy as np
S = np.loadtxt("study2-projection/results/scatter_jev_marcel.csv", delimiter=",", skiprows=1) * 1000
fig, axs = plt.subplots(1, 2, figsize=(11, 6), dpi=150, sharey=True)
fig.subplots_adjust(top=0.76, left=0.09, right=0.97, bottom=0.14, wspace=0.08)
for ax, col, c, lab in ((axs[0], 0, ORANGE, "Jev"), (axs[1], 1, SUB, "Marcel-style rule")):
    ax.scatter(S[:, 2], S[:, col], s=22, color=c, alpha=0.6, lw=0)
    ax.plot([-100, 100], [-100, 100], color=GRAY, lw=1, ls=(0, (4, 3)))
    ax.axhline(0, color=LIGHT, lw=1); ax.axvline(0, color=LIGHT, lw=1)
    ax.set_xlim(-105, 105); ax.set_ylim(-105, 105); ax.set_xticks([-100, -50, 0, 50, 100]); ax.set_yticks([-100, -50, 0, 50, 100])
    ax.tick_params(labelsize=12)
    ax.text(-100, 92, lab, fontsize=15, color=c, weight="bold")
    ax.set_xlabel("Actual change (wOBA, 1 = 0.001)", fontsize=13, color=SUB)
    base(ax, left=True); ax.spines["left"].set_color(GRAY)
axs[0].set_ylabel("Forecast change", fontsize=13, color=SUB)
axs[1].text(0, -95, "Dashed: forecast = actual", fontsize=12, color=SUB)
title(fig, "Jev's forecasts move only about 60% as much as the rule's", "227 hitters. SD of forecasts: Jev 13, rule 21 (even a good forecast is below the actual 36)")
fig.savefig(f"{OUT}/en_5_scatter.png"); plt.close(fig)

# 6. Study 2: weights on regression to the mean and on luck (joint least squares)
fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
fig.subplots_adjust(top=0.72, left=0.27, right=0.92, bottom=0.08)
items = [("Regression to the mean\n(points above league)", 0.430, 0.201), ("Luck\n(wOBA − xwOBA)", 0.426, 0.317)]
for i, (lab, act_w, jev_w) in enumerate(items):
    y = 1 - i
    ax.barh(y + 0.17, act_w, height=0.32, color=GRAY); ax.barh(y - 0.17, jev_w, height=0.32, color=ORANGE)
    ax.text(act_w + 0.008, y + 0.17, f"Actual {act_w:.2f}", va="center", fontsize=14, color=SUB)
    ax.text(jev_w + 0.008, y - 0.17, f"Jev {jev_w:.2f}", va="center", fontsize=14, color=ORANGE, weight="bold")
ax.set_yticks([1, 0]); ax.set_yticklabels([x[0] for x in items], fontsize=14)
ax.set_xlim(0, 0.55); ax.set_xticks([])
base(ax); ax.spines["bottom"].set_visible(False)
title(fig, "Jev uses luck, but not much regression to the mean", "Points given back next season per point above, in the forecast (actual: 1,620 past pairs)")
fig.savefig(f"{OUT}/en_6_weights.png"); plt.close(fig)

# 7. Study 2: named examples (wOBA points)
ex = [("Aaron Judge (.463)", -91, -75, -20), ("Cal Raleigh (.392)", -95, -34, -15), ("George Springer (.408)", -89, -54, -23),
      ("Henry Davis (.229)", 34, 64, 35), ("Michael Conforto (.287)", 55, 11, 34)]
fig, ax = plt.subplots(figsize=(10, 6.2), dpi=150)
fig.subplots_adjust(top=0.74, left=0.30, right=0.95, bottom=0.12)
for i, (lab, act_v, mar_v, jev_v) in enumerate(ex):
    y = len(ex) - 1 - i
    lo, hi = min(act_v, mar_v, jev_v), max(act_v, mar_v, jev_v)
    ax.plot([lo, hi], [y, y], color=LIGHT, lw=2, zorder=1)
    ax.scatter([act_v], [y], s=150, color=INK, zorder=3)
    ax.scatter([mar_v], [y], s=120, color=GRAY, zorder=2)
    ax.scatter([jev_v], [y], s=150, color=ORANGE, zorder=4)
ax.axvline(0, color=GRAY, lw=1)
ax.set_yticks(range(len(ex))[::-1]); ax.set_yticklabels([e[0] for e in ex], fontsize=13)
ax.set_xlim(-105, 75); ax.set_xticks([-100, -50, 0, 50]); ax.tick_params(axis="x", labelsize=12)
ax.set_xlabel("Change in wOBA, 2025 to 2026 (1 = 0.001)", fontsize=13, color=SUB)
base(ax)
fig.text(0.04, 0.83, "● Actual", fontsize=13, color=INK, ha="left", va="top")
fig.text(0.16, 0.83, "● Jev's forecast", fontsize=13, color=ORANGE, ha="left", va="top")
fig.text(0.34, 0.83, "●", fontsize=13, color=GRAY, ha="left", va="top")
fig.text(0.36, 0.83, "Marcel-style rule", fontsize=13, color=SUB, ha="left", va="top")
title(fig, "Jev missed the stars' big drops, got the unlucky hitters right")
fig.savefig(f"{OUT}/en_7_examples.png"); plt.close(fig)

# 8. Study 2: repairing the width only
arms8 = [("Jev (as is)", 0.1795, ORANGE), ("Jev's center +\nthe rule's width", 0.1624, ORANGE),
         ("... plus the missing\nregression to the mean", 0.1505, ORANGE), ("Marcel-style rule", 0.1489, GRAY)]
fig, ax = plt.subplots(figsize=(10, 6.0), dpi=150)
fig.subplots_adjust(top=0.74, left=0.30, right=0.92, bottom=0.08)
for i, (lab, r, c) in enumerate(arms8):
    v = clim - r; y = len(arms8) - 1 - i
    ax.barh(y, v, color=c, height=0.55, alpha=1.0 if i == 0 or c == GRAY else 0.55)
    ax.text(v + 0.0008, y, f"{v:.3f}", va="center", fontsize=15, color=ORANGE if c == ORANGE else SUB,
            weight="bold" if c == ORANGE else "normal")
ax.set_yticks(range(len(arms8))[::-1]); ax.set_yticklabels([a[0] for a in arms8], fontsize=14)
ax.set_xlim(0, 0.058); ax.set_xticks([]); base(ax); ax.spines["bottom"].set_visible(False)
title(fig, "Repair width and regression, and it matches the rule", "How far below guessing's RPS of 0.195 (bigger is better). Post-hoc analysis")
fig.savefig(f"{OUT}/en_8_width.png"); plt.close(fig)
print("ok2")
