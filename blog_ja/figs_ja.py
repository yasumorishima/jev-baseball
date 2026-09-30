# Japanese charts for the Qiita article, Japanese-manufacturer-deck style:
# one message per chart, the message is the title, direct labels, no gridlines, one accent color.
# Numbers are copied from results/analyze_output.txt, results/diagnose_output.txt (Study 1)
# and study2-projection/results/{analyze,diagnose}_output.txt (Study 2).
import os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ORANGE, GRAY, INK, SUB, LIGHT = "#e4560f", "#b9b8b3", "#0b0b0b", "#52514e", "#dedcd6"
plt.rcParams["font.family"] = "Noto Sans CJK JP"
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
rows = [("判定と逆側に\n1 インチ以上（82 球）", 0.99, 0.65),
        ("判定どおりの側に\n1 インチ以上（63 球）", 0.00, 0.18)]
for i, (lab, act, jev) in enumerate(rows):
    y = 1 - i
    ax.barh(y + 0.17, act, height=0.32, color=GRAY)
    ax.barh(y - 0.17, jev, height=0.32, color=ORANGE)
    ax.text(act + 0.015, y + 0.17, f"実際 {act*100:.0f}%", va="center", fontsize=14, color=SUB)
    ax.text(jev + 0.015, y - 0.17, f"Jev {jev*100:.0f}%", va="center", fontsize=14, color=ORANGE, weight="bold")
ax.set_yticks([1, 0]); ax.set_yticklabels([r[0] for r in rows], fontsize=14)
ax.set_xlim(0, 1.15); ax.set_xticks([])
base(ax); ax.spines["bottom"].set_visible(False)
title(fig, "明らかな球でも、Jev は覆る確率を控えめに出した", "ABS チャレンジ 250 件（2026 年 9 月）・灰色＝実際に判定が覆った割合 / 橙＝Jev の確率の平均")
fig.savefig(f"{OUT}/ja_1_abs.png"); plt.close(fig)

# 2. Study 2: improvement over guessing (RPS of guessing minus RPS of each method)
clim = 0.1945
arms = [("過去 20 件で学習", 0.1904, GRAY), ("Jev（学習なし）", 0.1795, ORANGE),
        ("過去 50 件で学習", 0.1608, GRAY), ("Marcel 法風のルール", 0.1489, GRAY),
        ("過去 1,620 件で学習", 0.1454, GRAY)]
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
title(fig, "当て推量からの上積みは、Marcel 法風ルールの 3 分の 1", "打者 227 人・当て推量の RPS 0.195 から何ポイント下げたか（大きいほど良い）")
fig.savefig(f"{OUT}/ja_2_gain.png"); plt.close(fig)

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
ax.text(1800, 0.1795, "Jev（学習なし）", color=ORANGE, fontsize=14, va="center", weight="bold")
ax.text(1800, 0.1470, "過去の例で\n学習したモデル", color=SUB, fontsize=14, va="bottom")
ax.set_xscale("log"); ax.set_xticks(ns); ax.set_xticklabels([f"{v:,}" for v in ns], fontsize=13)
ax.minorticks_off(); ax.set_xlim(8.5, 1650)
ax.set_ylim(0.14, 0.26); ax.set_yticks([0.15, 0.20, 0.25]); ax.tick_params(axis="y", labelsize=13)
ax.set_xlabel("学習に使った過去の例の数（対数目盛）", fontsize=14, color=SUB)
ax.set_ylabel("RPS（低いほど良い）", fontsize=14, color=SUB)
base(ax, left=False)
title(fig, "Jev の実力は、過去の例 20〜50 件で学習したモデルと同じくらい", "灰色の帯＝学習に使う例を 200 回選び直したときの 95% の範囲")
fig.savefig(f"{OUT}/ja_3_curve.png"); plt.close(fig)

# 4. Study 2: spread
bins = ["大きく\n下がる", "少し\n下がる", "ほぼ\n同じ", "少し\n上がる", "大きく\n上がる"]
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
fig.text(0.04, 0.83, "■ 実際に起きた割合", fontsize=13, color=SUB, ha="left", va="top")
fig.text(0.30, 0.83, "■ Jev の確率の平均", fontsize=13, color=ORANGE, ha="left", va="top")
title(fig, "Jev は「大きく動く」をほとんど想定していない")
fig.savefig(f"{OUT}/ja_4_spread.png"); plt.close(fig)
print("ok")

# ---- deep-dive charts (numbers from study2-projection/results/deepdive_output.txt and results/diagnose_output.txt) ----
# 1b. Study 1: overturn share by distance band
bands = ["判定どおりの側に\n1 インチ超", "判定どおりの側\n1 インチ以内", "判定と逆側\n1 インチ以内", "判定と逆側に\n1 インチ以上"]
actual_b, jev_b, base_b = [0.00, 0.58, 0.64, 0.99], [0.18, 0.23, 0.60, 0.65], [0.02, 0.32, 0.77, 0.98]
fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
fig.subplots_adjust(top=0.74, left=0.08, right=0.84, bottom=0.16)
for vals, c, lab, lw in ((actual_b, INK, "実際", 3), (base_b, GRAY, "距離だけの式", 3), (jev_b, ORANGE, "Jev", 3.5)):
    ax.plot(range(4), vals, color=c, lw=lw, marker="o", ms=8)
    ax.text(3.12, vals[-1] + (0.035 if lab == "距離だけの式" else -0.035 if lab == "実際" else 0), f"{lab} {vals[-1]*100:.0f}%",
            color=c if c != GRAY else SUB, fontsize=14, va="center", weight="bold" if c == ORANGE else "normal")
ax.set_xticks(range(4)); ax.set_xticklabels(bands, fontsize=13); ax.set_ylim(-0.03, 1.05)
ax.set_yticks([0, 0.5, 1.0]); ax.set_yticklabels(["0%", "50%", "100%"], fontsize=13)
base(ax)
title(fig, "はっきりした球ほど、Jev だけが確率を寄せきれない", "ABS チャレンジ 250 件（2026 年 9 月）・判定が覆った割合と、それぞれの予想の平均")
fig.savefig(f"{OUT}/ja_1b_bands.png"); plt.close(fig)

# 5. Study 2: forecast vs actual change (scatter)
import numpy as np
S = np.loadtxt("study2-projection/results/scatter_jev_marcel.csv", delimiter=",", skiprows=1) * 1000
fig, axs = plt.subplots(1, 2, figsize=(11, 6), dpi=150, sharey=True)
fig.subplots_adjust(top=0.76, left=0.09, right=0.97, bottom=0.14, wspace=0.08)
for ax, col, c, lab in ((axs[0], 0, ORANGE, "Jev"), (axs[1], 1, SUB, "Marcel 法風のルール")):
    ax.scatter(S[:, 2], S[:, col], s=22, color=c, alpha=0.6, lw=0)
    ax.plot([-100, 100], [-100, 100], color=GRAY, lw=1, ls=(0, (4, 3)))
    ax.axhline(0, color=LIGHT, lw=1); ax.axvline(0, color=LIGHT, lw=1)
    ax.set_xlim(-105, 105); ax.set_ylim(-105, 105); ax.set_xticks([-100, -50, 0, 50, 100]); ax.set_yticks([-100, -50, 0, 50, 100])
    ax.tick_params(labelsize=12)
    ax.text(-100, 92, lab, fontsize=15, color=c, weight="bold")
    ax.set_xlabel("実際の変化（wOBA、1 = 0.001）", fontsize=13, color=SUB)
    base(ax, left=True); ax.spines["left"].set_color(GRAY)
axs[0].set_ylabel("予想した変化", fontsize=13, color=SUB)
axs[1].text(20, -95, "点線＝予想と実際が同じ", fontsize=12, color=SUB)
title(fig, "Jev の予想は、ルールと比べても 6 割ほどしか動かない", "打者 227 人・予想のばらつき（標準偏差）Jev 13・ルール 21（当たる予想でも実際の 36 より小さくなる）")
fig.savefig(f"{OUT}/ja_5_scatter.png"); plt.close(fig)

# 6. Study 2: weights on regression to the mean and on luck (joint least squares)
fig, ax = plt.subplots(figsize=(10, 5.6), dpi=150)
fig.subplots_adjust(top=0.72, left=0.27, right=0.92, bottom=0.08)
items = [("平均への回帰\n（リーグ平均より高い分）", 0.430, 0.201), ("運\n（wOBA − xwOBA）", 0.426, 0.317)]
for i, (lab, act_w, jev_w) in enumerate(items):
    y = 1 - i
    ax.barh(y + 0.17, act_w, height=0.32, color=GRAY); ax.barh(y - 0.17, jev_w, height=0.32, color=ORANGE)
    ax.text(act_w + 0.008, y + 0.17, f"実際 {act_w:.2f}", va="center", fontsize=14, color=SUB)
    ax.text(jev_w + 0.008, y - 0.17, f"Jev {jev_w:.2f}", va="center", fontsize=14, color=ORANGE, weight="bold")
ax.set_yticks([1, 0]); ax.set_yticklabels([x[0] for x in items], fontsize=14)
ax.set_xlim(0, 0.55); ax.set_xticks([])
base(ax); ax.spines["bottom"].set_visible(False)
title(fig, "Jev は運を見ているが、平均への回帰をあまり見ていない", "2025 年に 1 点高かったとき、翌年に何点戻ると見ているか（実際は過去 1,620 組から）")
fig.savefig(f"{OUT}/ja_6_weights.png"); plt.close(fig)

# 7. Study 2: named examples (wOBA points)
ex = [("Aaron Judge（.463）", -91, -75, -20), ("Cal Raleigh（.392）", -95, -34, -15), ("George Springer（.408）", -89, -54, -23),
      ("Henry Davis（.229）", 34, 64, 35), ("Michael Conforto（.287）", 55, 11, 34)]
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
ax.set_xlabel("2025 → 2026 の wOBA の変化（1 = 0.001）", fontsize=13, color=SUB)
base(ax)
fig.text(0.04, 0.83, "● 実際", fontsize=13, color=INK, ha="left", va="top")
fig.text(0.16, 0.83, "● Jev の予想", fontsize=13, color=ORANGE, ha="left", va="top")
fig.text(0.34, 0.83, "● Marcel 法風のルール", fontsize=13, color=SUB, ha="left", va="top")
title(fig, "大きく下がった強打者は外し、運の悪かった打者は当てた")
fig.savefig(f"{OUT}/ja_7_examples.png"); plt.close(fig)

# 8. Study 2: repairing the width only
arms8 = [("Jev（そのまま）", 0.1795, ORANGE), ("Jev の予想の中心 ＋\nルールと同じ幅", 0.1624, ORANGE),
         ("さらに、足りない\n平均への回帰を足す", 0.1505, ORANGE), ("Marcel 法風のルール", 0.1489, GRAY)]
fig, ax = plt.subplots(figsize=(10, 6.0), dpi=150)
fig.subplots_adjust(top=0.74, left=0.30, right=0.92, bottom=0.08)
for i, (lab, r, c) in enumerate(arms8):
    v = clim - r; y = len(arms8) - 1 - i
    ax.barh(y, v, color=c, height=0.55, alpha=1.0 if i == 0 or c == GRAY else 0.55)
    ax.text(v + 0.0008, y, f"{v:.3f}", va="center", fontsize=15, color=ORANGE if c == ORANGE else SUB,
            weight="bold" if c == ORANGE else "normal")
ax.set_yticks(range(len(arms8))[::-1]); ax.set_yticklabels([a[0] for a in arms8], fontsize=14)
ax.set_xlim(0, 0.058); ax.set_xticks([]); base(ax); ax.spines["bottom"].set_visible(False)
title(fig, "幅と平均への回帰を補うと、Jev の予想はルールに並ぶ", "当て推量の RPS 0.195 から何ポイント下げたか（大きいほど良い）・結果を見た後の分析")
fig.savefig(f"{OUT}/ja_8_width.png"); plt.close(fig)
print("ok2")
