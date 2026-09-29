"""Two figures for the write-up, read from results/analyze_output.txt and the Jev answers."""
import json
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"axes.titlesize": 17, "axes.labelsize": 14, "xtick.labelsize": 13,
                     "ytick.labelsize": 13, "legend.fontsize": 12, "axes.spines.top": False,
                     "axes.spines.right": False})
out = open("results/analyze_output.txt").read()
arm = {m.group(1): float(m.group(2)) for m in re.finditer(r"^(JEV|CLIM|MARCEL-LITE|RIDGE\(all\))\s+([0-9.]+)", out, re.M)}
curve = [(int(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)))
         for m in re.finditer(r"n=\s*(\d+)\s+mean ([0-9.]+)\s+2\.5-97\.5% \[([0-9.]+), ([0-9.]+)\]", out)]
curve.append((1620, arm["RIDGE(all)"], arm["RIDGE(all)"], arm["RIDGE(all)"]))

# Figure 1: learning curve with Jev as a horizontal line
fig, ax = plt.subplots(figsize=(9, 5.5))
ns = [c[0] for c in curve]
ax.fill_between(ns, [c[2] for c in curve], [c[3] for c in curve], color="#9ecae1", alpha=0.5, lw=0)
ax.plot(ns, [c[1] for c in curve], "o-", color="#3182bd", lw=2.5, label="Model fitted on n past examples")
ax.axhline(arm["JEV"], color="#e6550d", lw=2.5, label="Jev (zero examples)")
ax.axhline(arm["MARCEL-LITE"], color="#636363", lw=1.8, ls="--", label="Marcel-style rule")
ax.axhline(arm["CLIM"], color="#bdbdbd", lw=1.8, ls=":", label="Guessing (20% per bin)")
ax.set_xscale("log")
ax.set_xticks(ns)
ax.set_xticklabels([str(n) for n in ns])
ax.set_xlabel("Number of past examples the model learned from")
ax.set_ylabel("RPS (lower is better)")
ax.set_title("Jev is worth about 20-50 examples")
ax.legend(frameon=False, loc="upper right")
fig.tight_layout()
fig.savefig("results/fig_learning_curve.png", dpi=150)

# Figure 2: average probability per bin vs how often it happened
test = json.load(open("test.json"))
cuts = json.load(open("frozen.json"))["cuts"]
J = [a for a in map(json.loads, open("results/jev_answers.jsonl")) if a["set"] == "test"]
n = len(test)
jev = [sum(a["bin_probs"][k] for a in J) / len(J) for k in range(5)]
act = [sum(1 for u in test if sum(u["delta"] > c for c in cuts) == k) / n for k in range(5)]
labels = ["Big\ndrop", "Small\ndrop", "About\nsame", "Small\nrise", "Big\nrise"]
fig, ax = plt.subplots(figsize=(9, 5.5))
x = range(5)
ax.bar([i - 0.2 for i in x], act, 0.4, color="#9e9ac8", label="What actually happened")
ax.bar([i + 0.2 for i in x], jev, 0.4, color="#e6550d", label="Jev's average probability")
ax.set_xticks(list(x))
ax.set_xticklabels(labels)
ax.set_ylabel("Share of hitters")
ax.set_title("Jev rarely expects big moves")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig("results/fig_spread.png", dpi=150)
print("ok", arm, curve[:2], [round(v, 3) for v in jev], [round(v, 3) for v in act])
