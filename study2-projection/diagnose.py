"""POST-HOC diagnostics (not pre-registered): what does Jev get right, and where does it lose?"""
import json
import math

from analyze import marcel

test = json.load(open("test.json"))
cuts = json.load(open("frozen.json"))["cuts"]
J = {a["idx"]: a for a in map(json.loads, open("jev_answers.jsonl")) if a["set"] == "test"}
n = len(test)


def corr(a, b):
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    return (sum((x - ma) * (y - mb) for x, y in zip(a, b))
            / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)))


ev = [sum(k * p for k, p in enumerate(J[i]["bin_probs"])) for i in range(n)]   # Jev's expected bin
mar = [marcel(u) for u in test]
d = [u["delta"] for u in test]
print("Direction: correlation with the actual change in wOBA")
print(f"  Jev expected bin {corr(ev, d):.3f} | Jev P(up) {corr([J[i]['p_up'] for i in range(n)], d):.3f} "
      f"| MARCEL-LITE {corr(mar, d):.3f}")
print("\nWhich signals each uses (correlation of the forecast with the input; 'actual' = with the real change)")
for name, key in (("wOBA - league (regression to the mean)", "woba_c"), ("wOBA - xwOBA (luck)", "gap"), ("age", "age")):
    x = [u[key] for u in test]
    print(f"  {name:40s} Jev {corr(ev, x):+.3f}  MARCEL-LITE {corr(mar, x):+.3f}  actual {corr(d, x):+.3f}")
print("\nSpread: average probability per bin vs how often each bin actually happened")
labels = ["big drop", "small drop", "about same", "small rise", "big rise"]
actual = [sum(1 for x in d if sum(x > c for c in cuts) == k) / n for k in range(5)]
for k in range(5):
    print(f"  {labels[k]:11s} Jev {sum(J[i]['bin_probs'][k] for i in range(n)) / n:.3f}   actual {actual[k]:.3f}")
