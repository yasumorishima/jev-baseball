# Pre-registration: Jev on MLB ABS pitch challenges

Written and committed **before any Jev call on the evaluation set**. Anything changed after
the first Jev call is logged under "Amendments" with the reason.

## Question

TypeSafe's Jev returns a calibrated probability for a yes/no question about a text "state".
Does Jev predict whether an ABS (Automated Ball-Strike) pitch challenge is **overturned**
as well as a one-variable baseline built from the pitch's distance to the strike-zone edge?

## Data

- MLB 2026 regular season, games from 2026-08-01 to 2026-09-27, from the public MLB
  StatsAPI game feeds (no key). One row per pitch event with `reviewDetails.reviewType == "MJ"`
  (challenge of a pitch result). `collect.sh` + `extract.jq`.
- Label: `reviewDetails.isOverturned`.
- **The feed's `call` field is the call after the review** and therefore encodes the label.
  It is never used. The original call is derived from the challenging side: the batting
  team challenges called strikes, the fielding team challenges called balls.
- Count and outs are taken from the last event before the challenged pitch that carries a
  count (so pitch-clock automatic balls/strikes and pickoff outs are included).
- The sample depends on which games were collected, so the md5 of `eval_sample.json` is
  recorded below before the first Jev call.
- Rows are dropped only if pX, pZ, sz_top or sz_bot is missing (count reported).

## Geometry

- Plate half-width 17/2 in = 0.7083 ft; ball radius 1.45 in = 0.1208 ft (a strike if any
  part of the ball touches the zone).
- Zone top / bottom = the feed's `strikeZoneTop` / `strikeZoneBottom` for that pitch.
- `edge_in` = signed distance (inches) from the ball's surface to the zone: the signed
  distance from the ball centre to the plain zone rectangle, minus the ball radius
  (the set of centres whose ball touches the zone is a rounded-corner rectangle).
  Positive = the ball misses the zone, negative = it touches.
- Caveat: the feed's `strikeZoneTop/Bottom` and `pX/pZ` may not be exactly the zone and
  plane ABS judges with; the RULE arm's accuracy shows how closely they reproduce it.
- `wrong_side_in` = `edge_in` if the original call was a strike, `-edge_in` if it was a ball
  (how far the pitch is on the wrong side of the original call; >0 means the geometry says
  the call was wrong).

## Split

- **Train** (baseline fitting only): games dated 2026-08-01 .. 2026-08-31.
- **Evaluation**: games dated 2026-09-01 .. 2026-09-27. A fixed random sample of
  **250** evaluation rows (Python `random.Random(20260929).sample`, rows ordered by
  (gamePk, inning, half, balls, strikes, pX)) is sent to Jev. The same 250 rows are
  used for every arm (paired).

## Arms

1. **BASE** - logistic regression of overturned on `wrong_side_in`, fitted on Train with a
   fixed L2 penalty of 0.01 on both coefficients (keeps the fit finite if the training
   data are separable).
2. **RULE** - deterministic: 1 if `wrong_side_in > 0` else 0 (reported for context; not a
   probability, so only accuracy is reported).
3. **JEV-RAW** - Jev `noul`, state = original call, who challenged, count, outs, inning,
   pitch type and speed, and the raw geometry (pX, pZ, zone top/bottom, plate half-width,
   ball radius, all in feet with their definitions). Jev must do the geometry itself.
4. **JEV-DIST** - same state as JEV-RAW plus `wrong_side_in` with its definition.

Model: `typesafe/jev-1.13` via OpenRouter `POST /api/alpha/decisions`. One call per row per
arm = 500 calls. The API key has a hard credit limit of $0.01; if a call is refused the run
stops and whatever was completed is reported (never retried with a larger limit).
JEV-DIST runs first (it is the primary arm). An incomplete arm is scored on the rows it
completed, paired with BASE on exactly those rows, and labelled as partial.

## Metrics and reading

- Primary: **Brier score** of JEV-DIST vs BASE on the 250 rows. Secondary: AUC and log loss
  for every probabilistic arm; accuracy at 0.5 for every arm.
- Uncertainty: paired bootstrap (10,000 resamples, seed 20260929) of the difference.
- Pre-declared reading for the primary comparison:
  - "Jev better" if the 95% interval of Brier(JEV-DIST) - Brier(BASE) is entirely below 0.
  - "Baseline better" if it is entirely above 0.
  - Otherwise "no detectable difference at n = 250".
- JEV-RAW vs JEV-DIST is reported as "how much of Jev's gap is the geometry it had to do".

## Frozen sample

- md5 of `eval_sample.json`: `289725a5e351b8e085b8e995c37ad04d` (2,678 challenges from 777 games; train 1,431 / eval 1,247; sample 250, 145 overturned)

## Amendments

(none yet — the edits above were made after an independent audit and before any Jev call
on the evaluation set; git history shows them)
