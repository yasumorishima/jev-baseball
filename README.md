# jev-baseball

Testing [TypeSafe Jev](https://docs.typesafe.ai) — a "decision-only" model that answers typed
questions with calibrated probabilities instead of text — on **MLB ABS (Automated Ball-Strike)
pitch challenges**.

**Question:** given a challenged pitch, does Jev predict whether the call is overturned as well
as a one-variable baseline built from the pitch's distance to the strike-zone edge?

## Result

**The pre-declared reading is "baseline better".** On 250 fixed September challenges,
Brier(Jev) − Brier(baseline) = **+0.067**, 95% paired-bootstrap interval **[+0.049, +0.084]**
(entirely above 0).

| Arm (n = 250, 145 overturned) | Brier ↓ | AUC ↑ | log loss ↓ | accuracy |
|---|---|---|---|---|
| **BASE** — logistic on distance to the zone edge, fitted on August | **0.113** | **0.927** | **0.329** | 0.816 |
| RULE — "overturned if the pitch is on the wrong side" | – | – | – | 0.800 |
| **JEV-DIST** — Jev, given the geometry *and* the precomputed distance | 0.180 | 0.836 | 0.543 | 0.808 |

JEV-RAW (Jev given only the raw coordinates) hit the key's $0.01 credit limit after 170 of
250 rows, as the pre-registration allowed for. On those 170 rows: BASE 0.111 / JEV-DIST 0.192 /
JEV-RAW 0.202 Brier, AUC 0.926 / 0.817 / 0.773. RAW − DIST = +0.010, 95% [−0.017, +0.036], so
having to do the geometry itself made no detectable difference to the Brier score.
Full output: [`results/analyze_output.txt`](results/analyze_output.txt).

### Where Jev loses (post-hoc, not pre-registered)

Jev **ranks** challenges reasonably (AUC 0.84, and the same accuracy as the baseline at a 0.5
threshold) but its probabilities are **too timid on the clear cases**:

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

### Cost

420 Jev calls (plus one test call), 254,501 input tokens, **$0.0107 at list price, covered by
OpenRouter's free allowance for new accounts**: the account's `total_credits` stayed at $0 and no
card was registered. About $0.000026 per call. The key's $0.01 limit is checked after a call
completes, so usage ended slightly above it ($0.01071).

## How it works

| Step | File | What it does |
|---|---|---|
| 1 | `collect.sh` + `extract.jq` | Pulls every MLB 2026 regular-season game feed (2026-08-01 .. 09-27) from the public MLB StatsAPI (no key) and keeps pitch events whose review type is `MJ` (a challenge of a pitch result). |
| 2 | `prepare.py` | Derives the original call, the signed distance to the zone edge, the Aug (train) / Sep (evaluation) split and a fixed 250-row evaluation sample. |
| 3 | `run_jev.py` | Sends each evaluation row to Jev (`typesafe/jev-1.13` via OpenRouter) as a `noul` question, in two arms: raw geometry only, and geometry plus the precomputed distance. |
| 4 | `analyze.py` | Brier score, AUC, log loss and accuracy for Jev and the baseline, with a paired bootstrap. |
| 5 | `diagnose.py` | Post-hoc (not pre-registered): calibration bins and behaviour by distance band. |

Everything is Python 3.11 standard library. The raw game data are not committed; rerun
`./collect.sh 2026-08-01 2026-09-28` then `python3 prepare.py` (the sample's md5 is in
`PREREG.md`). Jev's answers are in [`results/jev_answers.jsonl`](results/jev_answers.jsonl).

The design, the metrics and the pre-declared reading are fixed in [`PREREG.md`](PREREG.md)
before any Jev call on the evaluation set.

## Two traps in the StatsAPI feed

- On a challenged pitch, `details.call.description` is the call **after** the review, so it
  encodes the answer. The original call is inferred from who challenged (the batting team
  challenges strikes, the fielding team challenges balls); `prepare.py` asserts that this
  inference agrees with the post-review call on every row.
- A play event's `count` is the count **after** that pitch. The count before the challenged
  pitch is taken from the previous event that carries a count.

## Data source

MLB StatsAPI game feeds. Data © MLB Advanced Media; used here for non-commercial research.
