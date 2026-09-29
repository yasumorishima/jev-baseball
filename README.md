# jev-baseball

Testing [TypeSafe Jev](https://docs.typesafe.ai) — a "decision-only" model that answers typed
questions with calibrated probabilities instead of text — on **MLB ABS (Automated Ball-Strike)
pitch challenges**.

**Question:** given a challenged pitch, does Jev predict whether the call is overturned as well
as a one-variable baseline built from the pitch's distance to the strike-zone edge?

Status: data collection and pre-registration done; Jev run pending. Results will be added here.

## How it works

| Step | File | What it does |
|---|---|---|
| 1 | `collect.sh` + `extract.jq` | Pulls every MLB 2026 regular-season game feed (2026-08-01 .. 09-27) from the public MLB StatsAPI (no key) and keeps pitch events whose review type is `MJ` (a challenge of a pitch result). |
| 2 | `prepare.py` | Derives the original call, the signed distance to the zone edge, the Aug (train) / Sep (evaluation) split and a fixed 250-row evaluation sample. |
| 3 | `run_jev.py` | Sends each evaluation row to Jev (`typesafe/jev-1.13` via OpenRouter) as a `noul` question, in two arms: raw geometry only, and geometry plus the precomputed distance. |
| 4 | `analyze.py` | Brier score, AUC, log loss and accuracy for Jev and the baseline, with a paired bootstrap. |

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
