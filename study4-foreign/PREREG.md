# Study 4 pre-registration: do Jev's readings of pre-arrival Wikipedia text add to MLB numbers for a foreign player's first NPB season?

Written and committed before any scored Jev call (2026-10-02). One cost probe was made on a player outside
the sample (MLBAM 453307, no MLB pitch data in the window): 4,723 input tokens, $0.000198 (`probe4.py`).
A pre-freeze audit (an independent model, which ran the code) found wrong articles in the text set; the
identity gate below was added because of it, before any scored call.

## Why this study
Study 3 tested the shape Jev is built for (read text, return typed judgments, blend them with numbers in an
ordinary model) on draft reports and found NO GAIN. The case we care about is foreign players in NPB: the
pillar-1 study (repo `npb-foreign-statcast`) found that MLB numbers barely predict the first NPB season
(OPS_rel: constant 0.1309 / wOBA 0.1304 / xwOBA 0.1247 MAE). Here Jev reads the Wikipedia articles as they
stood before the player arrived in Japan and turns them into five yes/no features per role; a ridge
regression blends them with the MLB numbers.

## What has and has not been looked at
- Pillar 1's MLB-number vs NPB-outcome associations are known (published). The dry runs below also printed
  the NUM and constant MAEs on the real outcome (they are pillar-1 quantities).
- The texts were fetched and a keyword census was made over all of them (how many articles mention velocity,
  pitch types, control, power...). **No text feature or keyword has been related to any NPB outcome.**
- One Jev answer was seen, on the out-of-sample probe player.

## Data
- Players: pillar-1 tables `feat_bat.csv` / `feat_pit.csv` (built by the frozen pillar-1 `ana1.py`), first
  NPB season 2016-2025, rows with MLB pitch-level data in the pillar-1 window (column `n` present): 68
  batters, 109 pitchers, no player in both tables. Role = pillar-1 `kind`. The text cutoff year equals the
  feature-table year for every row (checked in the audit).
- Text: the latest ja.wikipedia revision before 1 March of the first NPB year, and the latest en.wikipedia
  revision before 1 January of that year (`fetch_ja_text.py`, `fetch_en_text.py`; titles from a name search
  in `cov_ja.py` / `cov_en.py`; revision id and timestamp stored and asserted to be before the cutoff). The
  text is CC BY-SA and is **not committed**; the scripts rebuild it.
- **Identity gate (`idgate4.py`)**: a text is kept only if the article's Wikidata item carries the MLB ID
  (P3541) equal to the player's MLBAM id. Result: ja 231 kept / 5 another person / 20 no MLB ID on the item;
  en 240 / 5 / 18. A player keeps the languages that pass; with none left he is dropped. (Examples caught:
  Anthony Bass's ja search hit Randy Bass; a disambiguation page; a team article; a namesake born in 1985.)
  Items without P3541 are dropped even when the article is right, which costs a few players.
- `prepare4.py` strips markup (references, tables, templates except year templates, files, categories,
  HTML tags and entities, and everything from the notes/references/external-links section on) and keeps the
  first 3,000 ja and 6,000 en characters (5 ja and 35 en texts are cut). It masks the player's own names:
  the katakana NPB names and the parts of the ja title; the English first and last name and title words
  (including possessives). Known gaps: middle names stay; 6 ja texts use an older katakana spelling of the
  name that is not masked; a surname or common first name also masks other people who share it (e.g.
  another player named Jones); a mask can sit next to other katakana.   share it; masks can sit next to other katakana. Masking is hygiene only: a career description identifies
  a well-known player (see Memory). `{{仮リンク}}` templates are removed whole, so some team and place names
  inside them are lost.
- A revision just before 1 March can describe the NPB signing and spring camp. That is information
  available before the season and is allowed.
- Sample after the gate: 67 of 68 batters and 107 of 109 pitchers have text (174 calls). Primary outcome rows
  (NPB first season >= 100 PA / >= 30 IP): **batters 51, pitchers 69**.

## Jev
- `typesafe/jev-1.13` via OpenRouter, one request per player, state = the ja and en texts ("(none)" when a
  language is missing). Questions (`jevq4.py`): `role`; hitter features `power`, `contact_concern`,
  `discipline`; pitcher features `velocity`, `put_away`, `control_concern`; both `injury`, `declining`.
  Jev answers all of them for every player.
- Features used: batters `power, contact_concern, discipline, injury, declining`; pitchers
  `velocity, put_away, control_concern, injury, declining`. Declared directions: power, discipline,
  velocity, put_away positive; concerns, injury, declining negative.
- Jev's `role` answer is reported only (agreement with pillar-1 kind); a disagreement changes nothing.
- Calls run in a fixed random order (seed 20261002). The key is a free-tier key capped at $0.05; expected
  spend about $0.022 for the main run; the probe resends the same texts (about $0.022 more), so the total is
  close to the cap and the probe may be cut short. If the limit stops the main run, the answered players are
  analysed as they are; a role with fewer than 30 answered primary rows gets no reading and does not enter
  Holm. Answers are rebuilt from `raw.jsonl` at every start, so a crash after logging loses nothing; a
  stopped run exits with code 1.
- Logging (`run_jev4.py`): the raw response bytes are appended to `raw.jsonl` before parsing; any exception
  stops the run; a player already in `raw.jsonl` is never called again; an unparseable or invalid response
  counts as unanswered. Only HTTP 429 is retried.

## Arms and statistic (`analyze4.py`)
- Outcomes: batters Y1 = OPS_rel (player OPS / league OPS of that year); pitchers P1 = K-BB% (as pillar 1).
- NUM: ridge (standardised in the training fold, alpha = 10) on the MLB numbers of pillar 1 (batters wOBA,
  xwOBA; pitchers K-BB%, CSW%, starter share) plus three text controls: log total cleaned text length (before
  the cap), has-ja, has-en. The length control is there because Study 3 found that a text feature can stand
  in for how much attention a player got.
- TEXT: NUM plus the five Jev probabilities of the role.
- Leave-one-arrival-year-out (10 folds). Score: mean absolute error.
- **Primary, per role**: d = MAE_TEXT - MAE_NUM against a floor in which the five Jev columns are permuted
  jointly (rows of the block move together) across players within the same arrival year, 500 permutations.
  floor p = (1 + #permutations with difference <= d) / 501; mirror p = (1 + #permutations with
  difference >= d) / 501. Holm over the roles that get a reading is applied to both. Reading: **TEXT ADDS if
  the Holm-adjusted p < 0.05 and d < 0** (TEXT must beat NUM outright, not only beat shuffled features);
  TEXT WORSE THAN SHUFFLED if the Holm-adjusted mirror p < 0.05 and d > 0 (this can come from features that
  only repeat what NUM already has); otherwise NO GAIN. The d < 0 condition was added after the second
  pre-freeze audit showed that, because the floor sits above zero, a floor p < 0.05 alone can fire with d > 0
  (dry run c = 0.5 seed 4, pitchers: d +0.0002, p 0.026).
- The floor is not zero: with uniform-noise features the floor mean is about +0.003 MAE in both roles (SD
  0.007 batters, 0.0015 pitchers): five extra columns cost MAE at this n, and shuffled features pay that
  cost.
- Secondary: d against zero with a 5,000-draw paired bootstrap; MAE of the constant model; coefficient signs
  on the full sample against the declared directions.

## Dry runs and power (synthetic answers, no answer read)
- Features = logistic(sign x c x standardised outcome + N(0,1) noise), five features with independent noise.
- c = 1.5 (an unrealistically strong effect; it halves the batters' MAE): ADDS in both roles. Uniform noise
  and functions of a NUM column: NO GAIN. Exact numbers: `dry4.log`.
- Power (audit, 30 seeds, 200 permutations, Holm): c = 0.25 (per-feature r with the outcome 0.16 / 0.12)
  power 0.17 / 0.07; c = 0.5 (r 0.31 / 0.25) 0.87 / 0.63; c = 1.0 (r 0.55 / 0.45) 1.0 / 1.0 (batters /
  pitchers). These are optimistic: real Jev features will be correlated with each other, so five of them
  carry less than five independent ones (the 30-seed numbers were computed under the earlier rule without
  d < 0 and were not re-run). My own 5-seed check at c = 0.5 (500 permutations) under the final rule: ADDS
  in 5 of 5 seeds for batters and 4 of 5 for pitchers (seed 4: d +0.0002, p 0.026 -> NO GAIN) (`dry4.log`).
- `run_jev4.py` was checked with a fake Jev (`sim_run4.py`, outside the repo data): a failure at call 20
  exits 1 with 19 logged responses; the rerun buys no player twice (174 raw lines, 174 unique); an answer
  dropped between logging and saving is restored from `raw.jsonl`; the probe run writes only its own files.

## Memory
Jev may know these players and their NPB seasons (2016-2025 is likely inside its training data); masking
names does not stop recognition from a career description. After the main run, and only if the key still
has credit, the probe `probe_good_japan` ("This player had a strong first season in Japan") is asked in
**separate requests** with the same state (so it cannot prime the feature answers), in the same order, and is
reported as its AUC for an above-median outcome (no AUC with fewer than 10 answered rows). It is never a
model input. A high probe AUC is a warning, not proof: a good reader can also infer from the text. **A TEXT
ADDS reading here cannot by itself separate reading from remembering**; the clean check is a later
registration on arrivals after Jev's training data (2026 or later), frozen before their NPB stats are read.

## Things that will not be done
No change to questions, features, arms, alpha, the identity gate, sample or test after the first scored call.
Any deviation goes in an AMENDMENT section with its time and reason, and the registered analysis is still
reported.
