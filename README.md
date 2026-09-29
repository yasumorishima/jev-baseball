# jev-baseball

Testing [TypeSafe Jev](https://docs.typesafe.ai) — a "decision-only" model that answers typed
questions with probabilities instead of text — on MLB data, with every study pre-registered
before the first Jev call.

| Study | Question | Pre-declared reading |
|---|---|---|
| **2. [Next-season wOBA](study2-projection/)** (main) | Given an anonymised 2025 batting line, how will the hitter's wOBA move in 2026? How many past examples does a fitted model need to match zero-shot Jev? | **Jev has skill but is worse than a textbook rule (Marcel-lite).** It knows the direction; it badly underestimates how far hitters move. |
| 1. ABS challenges (control) | Will an ABS pitch challenge be overturned? | Baseline better — as it had to be: the outcome is a fixed-zone rule, not a judgement. |

## Study 2 — is Jev a usable baseball prior when data are scarce?

Design, metrics and readings: [`study2-projection/PREREG.md`](study2-projection/PREREG.md)
(committed before any Jev call; an independent audit's fixes were added before the first call).
227 batters with ≥ 250 PA in both 2025 and 2026 (82 of the 2025 qualifiers did not reach 250 PA in
2026 and are excluded — the result is about hitters who kept playing). Jev saw no name, team or
exact age. Outcome: the change in wOBA, in five ordered bins; primary metric RPS (lower is better).

| Forecaster | RPS ↓ | Brier of P(up) ↓ |
|---|---|---|
| CLIM (20% per bin) | 0.1945 | 0.2465 |
| **Jev (zero-shot)** | **0.1795** | **0.2100** |
| Ridge fitted on 20 past pairs (mean of 200 draws) | 0.1904 | |
| Ridge fitted on 50 past pairs | 0.1608 | |
| MARCEL-LITE (shrink to the mean + age rule, no fitting) | 0.1489 | 0.1918 |
| Ridge fitted on all 1,620 past pairs | 0.1454 | 0.1925 |

- Jev beats climatology: RPS −0.015, 95% [−0.029, −0.001]. So it has *some* skill.
- Jev loses to the textbook rule: +0.031, 95% [+0.017, +0.044] → **pre-declared reading:
  "Jev is worse than a textbook rule."** On the learning curve it sits between a ridge fitted on
  20 and on 50 past examples.
- Without the 17 extreme lines (any feature |z| > 2.5, i.e. stars that rounding cannot hide),
  Jev vs climatology is −0.010, 95% [−0.024, +0.005]: the skill is no longer distinguishable from zero.
- Recall probe (blend each of 50 hitters with a statistical neighbour to destroy identity): Jev did
  *better* on blended lines than the fitted model did (difference −0.031, 95% [−0.055, −0.007]),
  the opposite of what recalling players would produce. No evidence of recall at this power
  (smallest detectable gap ≈ 0.024).

**Where it loses (post-hoc, not pre-registered — [`results/diagnose_output.txt`](study2-projection/results/diagnose_output.txt)).**
Jev gets the *direction* nearly as well as the rule (correlation with the real change 0.57 vs
0.62). It uses the right signals — it expects hitters far above the league mean to fall back,
and it leans on the wOBA − xwOBA "luck" gap even more than reality does (−0.68 vs −0.43). What it
gets wrong is the **size of the moves**: it puts 2% on a big drop (actual 14.5%) and 9% on a big
rise (actual 22.5%). Real hitters move much further than Jev believes, and RPS punishes that.

Cost: 277 calls, 189,677 input tokens, $0.0080 at list price, from OpenRouter's free allowance
(account balance $0, no card). Full output: [`results/analyze_output.txt`](study2-projection/results/analyze_output.txt).

## Study 1 — ABS pitch challenges (control)

In hindsight this was the wrong task for a judgement model: an ABS review compares tracked
coordinates with a fixed zone, so the outcome is a rule and a one-variable model had to win.
It is kept as a control and for the StatsAPI data traps it documents.

**The pre-declared reading is "baseline better".** On 250 fixed September challenges,
Brier(Jev) − Brier(baseline) = **+0.067**, 95% paired-bootstrap interval **[+0.049, +0.084]**
(entirely above 0). Scope: this model version (`typesafe/jev-1.13-20260917`), this prompt
format (see `run_jev.py`) and MLB challenges from September 2026 only.

| Arm (n = 250, 145 overturned) | Brier ↓ | AUC ↑ | log loss ↓ | accuracy |
|---|---|---|---|---|
| **BASE** — logistic on distance to the zone edge, fitted on August | **0.113** | **0.927** | **0.329** | 0.816 |
| RULE — "overturned if the pitch is on the wrong side" | – | – | – | 0.800 |
| **JEV-DIST** — Jev, given the geometry *and* the precomputed distance | 0.180 | 0.836 | 0.543 | 0.808 |

JEV-RAW (Jev given only the raw coordinates) hit the key's $0.01 credit limit after 170 of
250 rows, as the pre-registration allowed for. On those 170 rows: BASE 0.111 / JEV-DIST 0.192 /
JEV-RAW 0.202 Brier, AUC 0.926 / 0.817 / 0.773, accuracy 0.818 / 0.806 / 0.706.
RAW − DIST Brier = +0.010, 95% [−0.017, +0.036]: no detectable difference in Brier, but the
interval does not rule out a gap of about 0.04, and RAW is lower on AUC and accuracy.
Full output: [`results/analyze_output.txt`](results/analyze_output.txt).

### Where Jev loses in Study 1 (post-hoc, not pre-registered)

Jev **ranks** challenges reasonably (AUC 0.84, and similar accuracy to the baseline at a 0.5
threshold: 0.808 vs 0.816) but its probabilities are **too timid on the clear cases**:

| Pitch position vs the original call | n | actually overturned | Jev | baseline |
|---|---|---|---|---|
| ≥ 1 in on the wrong side (call clearly wrong) | 82 | 0.99 | 0.65 | 0.98 |
| 0–1 in on the wrong side | 55 | 0.64 | 0.60 | 0.77 |
| 0–1 in on the right side | 50 | 0.58 | 0.23 | 0.32 |
| > 1 in on the right side (call clearly right) | 63 | 0.00 | 0.18 | 0.02 |

Even when told the pitch was more than an inch on the wrong side, Jev stays near 0.65, so the
Brier score punishes it on exactly the cases a simple model gets right. Full output:
[`results/diagnose_output.txt`](results/diagnose_output.txt).

A side observation: within one inch *inside* the called side, 58% of challenges were still
overturned, so the StatsAPI zone (`strikeZoneTop/Bottom`, `pX/pZ`) does not reproduce the ABS
zone exactly near the edge (RULE accuracy 0.80).

### Cost of Study 1

420 Jev calls (plus one earlier connectivity test on a hand-written state, not an evaluation row), 254,501 input tokens, **$0.0107 at list price, covered by
OpenRouter's free allowance for new accounts**: the account's `total_credits` stayed at $0 and no
card was registered. About $0.000026 per call. The key's $0.01 limit is checked after a call
completes, so usage ended slightly above it ($0.01071).

### How Study 1 works

| Step | File | What it does |
|---|---|---|
| 1 | `collect.sh` + `extract.jq` | Pulls every MLB 2026 regular-season game feed (2026-08-01 .. 09-27) from the public MLB StatsAPI (no key) and keeps pitch events whose review type is `MJ` (a challenge of a pitch result). |
| 2 | `prepare.py` | Derives the original call, the signed distance to the zone edge, the Aug (train) / Sep (evaluation) split and a fixed 250-row evaluation sample. |
| 3 | `run_jev.py` | Sends each evaluation row to Jev (`typesafe/jev-1.13` via OpenRouter) as a `noul` question, in two arms: raw geometry only, and geometry plus the precomputed distance. |
| 4 | `analyze.py` | Brier score, AUC, log loss and accuracy for Jev and the baseline, with a paired bootstrap. |
| 5 | `diagnose.py` | Post-hoc (not pre-registered): calibration bins and behaviour by distance band. |

Collected: 778 final regular-season games scheduled, 777 with play data (game 823490 returned
no plays), 2,678 challenges. Everything is Python 3.11 standard library. The raw game data are not committed; rerun
`./collect.sh 2026-08-01 2026-09-28` then `python3 prepare.py` (the sample's md5 is in
`PREREG.md`). Jev's answers are in [`results/jev_answers.jsonl`](results/jev_answers.jsonl).

The design, the metrics and the pre-declared reading are fixed in [`PREREG.md`](PREREG.md)
before any Jev call on the evaluation set.

### Two traps in the StatsAPI feed

- On a challenged pitch, `details.call.description` is the call **after** the review, so it
  encodes the answer. The original call is inferred from who challenged (the batting team
  challenges strikes, the fielding team challenges balls); `prepare.py` asserts that this
  inference agrees with the post-review call on every row.
- A play event's `count` is the count **after** that pitch. The count before the challenged
  pitch is taken from the previous event that carries a count.

## Data source

MLB StatsAPI game feeds. Data © MLB Advanced Media; used here for non-commercial research.
