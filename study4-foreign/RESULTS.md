# Study 4 result: NO GAIN for batters and pitchers

Registered analysis of `PREREG.md` (frozen at commit `67dce06`, md5 `9c864ffc37e9a2ae3f2f593de85bf3a9`),
run 2026-10-02. All 174 players were answered (0 unusable), in the main run and in the separate probe run.
Spend: $0.0240 main + $0.0208 probe (1.07M input tokens) on a free-tier key capped at $0.05.

## Primary
| | n | MAE constant | MAE NUM | MAE TEXT | d = TEXT - NUM | floor mean (sd) | floor p | reading |
|---|---|---|---|---|---|---|---|---|
| Batters (OPS_rel) | 51 | 0.1286 | 0.1308 | 0.1364 | +0.0056 | +0.0064 (0.0064) | 0.41 | NO GAIN |
| Pitchers (K-BB%) | 69 | 0.0458 | 0.0451 | 0.0489 | +0.0038 | +0.0033 (0.0015) | 0.62 | NO GAIN |

Holm-adjusted p 0.81 in both roles (with this run's permutation seed; an independent reimplementation with
another seed gave 0.88 and the same reading). The real Jev columns did no better than the same columns
shuffled within arrival year.

## Secondary (not readings)
- d against zero (paired bootstrap): batters [-0.012, +0.025]; pitchers [+0.0009, +0.0066]. For pitchers
  TEXT is worse than NUM, by about what five shuffled columns cost at this n (97% of the floor is above 0).
  TEXT is also worse than the constant model for pitchers.
- For batters NUM itself is worse than the constant (0.1308 vs 0.1286), as in pillar 1, so d is measured
  against a baseline without skill.
- Coefficient signs against the declared directions: pitchers 5 of 5, batters 2 of 5.
- Jev's role answer agrees with the pillar-1 role for 63 of 67 batters (the 4 others answered "both") and
  107 of 107 pitchers.

## Did Jev read the text? Yes (post-run audit)
The features are not degenerate (sd 0.14 to 0.39; mean of `declining` about 0.85). Their correlations with
each other are mostly 0.0 to 0.3, except velocity with put_away at 0.69. They track the text. Pitchers whose
text states a fastball of at least 95 mph or 150 km/h (40 of 107) average 0.89 on `velocity`; the others
average 0.34 (AUC 0.88). Keyword AUCs from the audit are injury 0.91, declining 0.94 and power 0.95. So the
null means that the readings did not improve out-of-sample prediction. It does not mean that Jev failed to
read the articles.

## Memory probe (separate requests, never an input)
AUC for an above-median outcome is batters 0.43 (two-sided permutation p 0.42) and pitchers 0.58 (p 0.23).
No detectable memory signal. The probe answers are compressed (sd 0.06 to 0.09), and at this n only an AUC
of about 0.65 or more would show, so this is weak evidence of absence.

## What not to read into it
- Not "the texts carry nothing." This test detects only a large gain over MLB numbers at n 51 / 69.
- Not "Jev has no memory of these players." The probe found no detectable signal.
- Post-hoc, unregistered, not claimed: in-sample Spearman with the outcome is power +0.36 and injury +0.32
  (opposite to the declared direction) for batters, and put_away +0.30 and velocity +0.24 for pitchers.

## Known limitations found after the freeze (the text is frozen as run)
- `prepare4.py` deletes `{{ndash}}`, so speed ranges merge in 7 players' English text ("93-95 mph" became
  "9395 MPH").
- Every feature correlates with log text length (Spearman 0.21 to 0.50). The length control in NUM absorbs
  part of that.
- `PREREG.md` repeats a sentence fragment in the masking bullet. This is an editing slip and was left
  unchanged because the file is frozen.

Files: `results/analyze4.out` (main), `results/analyze4_probe.out` (with probe), `results/jev_answers.json`,
`results/jev_probe.json`, `results/run_jev4.log`, `results/run_probe4.log`. The post-run audit wrote its own
analysis from `PREREG.md` and did not import `analyze4.py`. It reproduced d and the reading, and checked that
every paid response was used once and that no player was bought twice.
