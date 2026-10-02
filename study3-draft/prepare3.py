"""Study 3 sample: draft years 2017-2020 (five or more seasons to debut), a random sample sized to the
free credit left on the key. Writes ~/claude-scratch/jev/draft/sample.json and prints its md5.

Players drafted more than once keep their earliest draft (its report is the first pre-draft read).
Cost model: one call with the final question set on a 2021 holdout player (338 characters) used 680
input tokens, so input tokens ~ 595 + chars/4 (chars/4 is a rough token count); $0.042 per million.
"""
import hashlib
import json
import os
import random

D = os.path.expanduser("~/claude-scratch/jev/draft/")
BUDGET = 0.0108          # dollars; remaining was 0.011863 after the cost probes (margin ~0.001)
PRICE = 0.042e-6

R0 = sorted((r for r in json.load(open(D + "picks.json"))["rows"] if 2017 <= r["year"] <= 2020),
            key=lambda r: (r["year"], r["pick"]))
seen, R = set(), []
for r in R0:
    if r["pid"] not in seen:
        seen.add(r["pid"])
        R.append(r)
print("rows", len(R0), "players", len(R))
rng = random.Random(20261002)
order = sorted(R, key=lambda r: (r["year"], r["pid"]))
rng.shuffle(order)
sample, cost = [], 0.0
for r in order:
    c = (595 + len(r["blurb"]) / 4) * PRICE
    if cost + c > BUDGET:
        break
    sample.append(r)
    cost += c
# kept in the shuffled order: if the credit limit stops the run, the answered part is still random
blob = json.dumps(sample, sort_keys=True).encode()
open(D + "sample.json", "wb").write(blob)
print("pool", len(R), "sample", len(sample), "expected cost $%.5f" % cost)
print("by year", {y: sum(1 for r in sample if r["year"] == y) for y in range(2017, 2021)})
print("debut rate pool %.3f sample %.3f" % (sum(1 for r in R if r["debut"]) / len(R),
                                             sum(1 for r in sample if r["debut"]) / len(sample)))
print("sample md5", hashlib.md5(blob).hexdigest())
