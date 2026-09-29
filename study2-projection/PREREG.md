# Pre-registration — Study 2: is Jev a usable baseball prior when data are scarce?

Written and committed **before any Jev call in this study**. Changes after the first call go
under "Amendments" with the reason.

## Why this study (and why the answer is not known in advance)

Study 1 (ABS challenges) asked Jev a question whose answer is a deterministic rule, so a fitted
one-variable model won, as it had to. Here the outcome — how a hitter's wOBA moves from one season
to the next — is genuinely uncertain (luck, regression to the mean, ageing, injuries).
We do **not** ask "does Jev beat a model fitted on all the data?" (it almost certainly does not).
We ask: **how many past examples does a fitted model need before it matches zero-shot Jev?**
Where that crossover falls is not settled by anything we know in advance, and it is the practical
question for scarce-data settings (NPB, rookies, new imports).

## Data

- `marts/mart_batter_season.parquet` from the public HF dataset `yasumorishima/mlb-stats`
  (snapshot downloaded 2026-09-29; the mart flags 2026 as `is_partial`; the max 2026 PA is 725,
  the regular season ended 2026-09-27). The file's md5 is recorded below.
- **Test units:** batters with ≥ 250 PA in 2025 and ≥ 250 PA in 2026 (227). Batters with ≥ 250 PA
  in 2025 but not in 2026 are counted and reported as drop-outs (the filter conditions on survival).
- **Training pairs (baselines only):** the same ≥ 250 / ≥ 250 PA rule for consecutive seasons
  2016→17 … 2024→25, excluding any pair touching 2020 (60-game season).
- **Outcome:** Δ = wOBA(2026) − wOBA(2025).
- **Bins:** five ordered bins, cut at the 20/40/60/80% quantiles of Δ over all training pairs
  (computed by `prepare.py`, printed and frozen below).

## What Jev sees (anonymised)

No name, team, player id or exact age. Per batter: age band (≤ 25, 26–29, 30–33, ≥ 34),
position group (C / IF / OF / DH), PA rounded to 25, wOBA and xwOBA rounded to 0.005,
K%, BB% rounded to 1 point, ISO and BABIP rounded to 0.005, GB% / FB% / pull-air% rounded to
1 point, sprint speed rounded to 0.5 ft/s, and the 2025 league wOBA (0.313) as context.

## Questions (one Jev call per batter, `typesafe/jev-1.13` via OpenRouter)

1. `score` — which of the five Δ bins (labels state the numeric ranges).
2. `noul` — will the batter's 2026 wOBA be higher than his 2025 wOBA?

## Comparators (all fitted/evaluated on the same 227 test batters)

- **CLIM** — 20% in every bin; P(up) = share of training pairs with Δ > 0.
- **MARCEL-LITE** — projected wOBA = lg + PA/(PA+600)·(wOBA − lg), times an age factor
  (1 + 0.006·(29 − age) under 29, 1 − 0.003·(age − 29) over 29); Δ̂ = projection − wOBA;
  predictive distribution Normal(Δ̂, s) with s the residual sd of this rule on the training pairs.
- **RIDGE(n)** — linear ridge regression of Δ on standardised [wOBA − lg, wOBA − xwOBA, K%, BB%,
  ISO, BABIP, age, PA/600], λ = 1 on the slopes, intercept unpenalised; predictive distribution
  Normal(Δ̂, s) with s = residual sd on its own training sample (n − 1 denominator, floored at
  0.005). Fitted on n ∈ {10, 20, 50, 100, 300, all} training pairs drawn at random
  (200 draws per n, seed 20260929; "all" is one fit).

## Metrics

- Primary: **ranked probability score (RPS)** over the five bins, averaged over test batters.
- Secondary: Brier score of P(up).
- RIDGE(n) curve: mean and 2.5–97.5% range of RPS across the 200 draws.
- Jev vs CLIM, Jev vs MARCEL-LITE, Jev vs RIDGE(all): paired bootstrap of the RPS difference
  (10,000 resamples of batters, seed 20260929).

## Pre-declared reading

1. If the 95% interval of RPS(Jev) − RPS(CLIM) is not entirely below 0: **"Jev shows no skill."**
2. Else if RPS(Jev) − RPS(MARCEL-LITE) has a 95% interval entirely above 0:
   **"Jev is worse than a textbook rule."**
3. Crossover n = the smallest n in the grid whose mean RIDGE(n) RPS ≤ RPS(Jev).
   - crossover ≤ 20 → "Jev ≈ a crude prior";
   - 50 or 100 → "Jev ≈ a prior worth tens of seasons of examples";
   - ≥ 300 or never → "Jev carries substantial baseball prior knowledge".

## Recall (leak) probe

Jev's version is dated 2026-09-17 and may know 2026 results. Anonymisation may not suffice for
star lines. Probe: 50 test batters (seed 20260929). For each, build a **blended line** = the
average of his features and those of his nearest neighbour among the other test batters
(Euclidean on the standardised RIDGE features), with outcome = the average of the two Δs.
Blending keeps the statistical information but destroys identity. Compare
ΔRPS = RPS(blended) − RPS(original, same 50) for Jev and for RIDGE(all).
If Jev's ΔRPS exceeds RIDGE(all)'s by more than the 95% bootstrap interval allows
(interval of the difference entirely above 0): **"evidence that Jev recalled players"**, and the
main result is reported with that caveat.

## Budget

227 + 50 = 277 calls. Key credit limit $0.02, OpenRouter free allowance only (balance $0, no
card). A refused call stops the run; incomplete work is scored on completed rows and labelled
partial. No retry with a larger limit.

## Frozen values

From `prepare.py` (run 2026-09-29, before any Jev call in this study):

- parquet md5 `bcdbddd9ffd1d2da616536833f261bc4`
- training pairs 1,620; test batters 227; 2025 qualifiers without 250 PA in 2026 (drop-outs): 82
- league wOBA 2025 0.3131; P(Δ > 0) in training pairs 0.440
- bin cut points (Δ wOBA): −0.0363, −0.0144, 0.0029, 0.0248; test batters per bin 33 / 52 / 50 / 41 / 51
- probe indices: the 50 from `random.Random(20260929).sample(range(227), 50)` (in `frozen.json`)
- Comparator values are computed by `analyze.py` from these files and do not depend on Jev.

## Changes after the independent audit (made before any Jev call in this study)

1. **RIDGE(n) predictive sd** uses the honest degrees of freedom: residual SS / (n − p − 1) with
   p = 8 slopes; when n ≤ p + 1 it uses the sd of Δ in the draw. (The original n − 1 made small-n
   ridge overconfident, which would have moved the crossover for reasons unrelated to Jev.)
   MARCEL-LITE's s is the RMS error of the rule on the training pairs.
2. **Label order check:** the first call is made alone (`run_jev.py --limit 1`) and its raw reply
   is inspected to confirm that `score` probability key "0" is the first criterion ("Big drop").
3. **Call order** is shuffled with seed 20260929 (test and probe interleaved), so a run that stops
   early is not biased toward some players and does not lose the probe.
4. **Secondary result (pre-declared):** the Jev-vs-comparator RPS differences are also reported
   without "extreme" lines — any standardised 2025 feature with |z| > 2.5 over the 227 test
   batters — because rounding cannot hide star players.
5. **Recall probe:** the same blended-minus-original ΔRPS is also computed for MARCEL-LITE and
   CLIM as null references, and the half-width of each interval is printed as the smallest gap
   the probe can detect. The probe is scored on every blended row whose source row Jev answered.
   The reading stays: evidence of recall only if the JEV − RIDGE(all) interval is entirely above 0.

## Amendments

(none)
