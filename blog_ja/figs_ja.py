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
