# Study 3 pre-registration: do Jev's readings of a pre-draft scouting report add to the draft-time numbers?

Written and committed before any scored Jev call (2026-10-02). Cost probes were made on two 2021
players, who are outside the sample.

## Why this study
Studies 1 and 2 asked Jev to turn numbers into a number, the shape where a trained model wins. Jev is
built for the other shape: read unstructured text and return typed judgments that ordinary code then
uses. Here Jev reads text that has no numeric twin (the MLB.com pre-draft report on each player) and
turns it into six yes/no features; a plain logistic regression then blends them with the draft-time
numbers.

## Data
- MLB StatsAPI `/api/v1/draft/<year>` (keyless), Rule 4 June draft picks that carry a `blurb`
  (MLB.com pre-draft report), 2017-2020: 993 rows. Outcome: `mlbDebutDate` present on 2026-10-02
  (five or more seasons after the draft). 993 rows are 948 players: a player drafted more than once
  keeps his earliest draft. Pool debut rate 0.421.
- Sample: 310 players drawn at random (seed 20261002) and sized to the free credit left on the key
  ($0.0108 expected of $0.011863), kept in the random order so that a run stopped by the limit is
  still a random subset. md5 of `sample.json`: `0429dc62f625cbab80a39d72f570e433`. Debut rate 0.400.
  The report text is MLB's and is not committed; `collect.py` rebuilds it.
- Draft-time fields: pick number, pre-draft rank (missing for 353 of the 1,243 collected rows,
  coded with a flag), slot value `pickValue` (set before the draft; none after round 10, flagged),
  age on the first day of the draft, draft year. Bats and throws are current API values (stable for
  almost all players). Not used: `signingBonus` (unsigned picks carry 0, so it encodes the signing
  decision made after the draft), `primaryPosition`, `height`, `weight` (current values).

## Jev
- Model `typesafe/jev-1.13` via OpenRouter, one request per player, state = the report folded to
  ASCII, with the player's full and multi-word names, his own capitalised name words (exact or
  similarity >= 0.80, which catches unaccented and misspelled forms), his initials and the
  distinctive words of the school name replaced. After masking, 0 of 1,243 reports keep a
  capitalised word within similarity 0.80 of any surname part. About 3% of the school-word masks hit
  a non-school use (a conference or state name). Identity can still leak through relatives
  ("son of ..."), teammates, mascots and achievements; the memory probe reports on this.
- Questions (`jevq.py`): `role` (pitcher / position player / both, used by BOTH arms), six yes/no
  features `hit_concern`, `cmd_concern`, `injury`, `raw`, `upside`, `makeup`, and the memory probe
  `reached` ("This player went on to play in the major leagues"), which is never a model input.
- If the key's limit stops the run, the answered players are analysed as they are. Every paid
  response is logged before validation; a response missing a question or with an out-of-range value
  is rejected, counted as unanswered and never re-bought. Network failures stop the run (no retry,
  so nothing is paid twice); only HTTP 429 is retried.

## Arms and statistic (`analyze3.py`)
- NUM: logistic regression (standardised, C = 1) on log pick, log rank (+ missing flag), log slot
  value (+ missing flag), age, bats L/S, throws L, role (Jev), year dummies.
- TEXT: NUM plus the six Jev probabilities.
- Out-of-fold probabilities from 20 repeats of stratified 10-fold CV, averaged per player.
- **Primary (changed after the first pre-run audit, before any scored call; a second audit verified the
  fixes on synthetic answers: informative features p 0.024 → ADDS, noise p 0.90 and NUM-only
  functions p 0.68 → NO GAIN)**: the log-loss difference
  d = TEXT - NUM is compared with a floor in which the six features are shuffled across players
  within role x pick tier (1-30, 31-100, 101-300, 301+), 200 shuffles, same 20 CV repeats.
  floor p = (1 + #shuffles with difference <= d) / 201. Reading: TEXT ADDS if floor p < 0.05;
  TEXT WORSE THAN SHUFFLED if the mirror p < 0.05 (this can come from features that only repeat
  what NUM already has, so it does not by itself mean the readings mislead); otherwise NO GAIN. Reason: six noise columns cost
  log loss at this n (dry run on random answers: floor mean +0.013), so a test against zero would
  read noise as harm.
- Secondary: d against zero with a 5,000-draw paired bootstrap.
- Secondary: AUC of both arms; coefficient signs on the full sample against the declared directions
  (concerns, injury and raw negative; upside and makeup positive); sensitivity without the first
  30 picks.

## Memory check
Jev may know these players. The probe `reached` is asked in the same request. PROBE INFORMATIVE
is YES if the probe alone beats NUM's AUC by more than 0.03, or if adding it to TEXT lowers log loss
with a 95% interval below 0. The audit pointed out that a good probe can come from good reading as
well as from memory, so YES is not proof of recognition and NO is not proof of its absence; the
probe is reported, not used to adjust the reading. It shares the request with the six features.

## Power
n = 310 with 124 debuts. A gain needs to exceed what six noise columns cost; this study can
detect a large effect only. A NO GAIN reading is not evidence that the reports carry nothing.
