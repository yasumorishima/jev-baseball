# jev-baseball

Testing [TypeSafe Jev](https://docs.typesafe.ai) — a "decision-only" model that answers typed
questions with probabilities instead of text — on MLB data, with every study pre-registered
before the first Jev call.

Write-up with charts: [Japanese (Qiita)](https://qiita.com/ussu_ussu_ussu/items/cc28f711396515c1fb31) / [English (DEV.to)](https://dev.to/yasumorishima/asking-a-decision-only-ai-typesafe-jev-to-forecast-next-seasons-hitting-worth-about-20-to-50-360k)

| Study | Question | Pre-declared reading | Post-hoc diagnosis |
|---|---|---|---|
| **2. [Next-season wOBA](study2-projection/)** (main) | Given an anonymised 2025 batting line, how will the hitter's wOBA move in 2026? How many past examples does a fitted model need to match zero-shot Jev? | **Jev has skill but is worse than a textbook rule (Marcel-lite).** | It gets the direction nearly right but puts far too little probability on big moves. |
| 4. [Foreign players in NPB](study4-foreign/) | Jev reads the player's Wikipedia articles (ja + en) as they stood before he moved to Japan and returns five yes/no features. Does a model with them predict his first NPB season better than his MLB numbers alone? | **NO GAIN** for batters (OPS_rel, p 0.41) and pitchers (K-BB%, p 0.62) against a shuffled-feature floor. | Jev did read the text: "hard fastball" scores 0.89 when the article gives 95+ mph and 0.34 otherwise. The readings still add nothing out of sample at n 51 / 69. |
| 3. [Pre-draft reports + numbers](study3-draft/) | Jev reads the masked MLB.com pre-draft report and returns six yes/no features; does a model with them predict reaching the majors better than draft-time numbers alone? | **NO GAIN** (log-loss difference against a shuffled-feature floor, p 0.46). | Praise of makeup separates players within pick tiers (AUC 0.60), but it moves with report length and prospect rank. Exploratory only. |
| 1. ABS challenges (control) | Will an ABS pitch challenge be overturned? | Baseline better — as it had to be: the outcome is a fixed-zone rule, not a judgement. | Too timid on clear cases. |

## Study 4 — foreign players in NPB: pre-arrival Wikipedia text blended with MLB numbers

The case behind Study 3. MLB numbers barely predict a foreign player's first NPB season (the
[npb-foreign-statcast](https://github.com/yasumorishima/npb-foreign-statcast) pillar-1 study). Can text
written before he arrived add something?

- **Text**: the ja.wikipedia revision before 1 March of the first NPB year and the en.wikipedia revision
  before 1 January, cleaned of markup, with the player's own names masked. An **identity gate** keeps an
  article only if its Wikidata MLB ID matches the player. A pre-freeze audit found that a name search had
  returned Randy Bass's article for Anthony Bass, a disambiguation page, a team page and a namesake. The
  text is CC BY-SA and is not committed; the scripts rebuild it from revision ids.
- **Players**: 2016-2025 arrivals with MLB pitch data; 174 called; primary rows 51 batters
  (>= 100 PA) and 69 pitchers (>= 30 IP).
- **Arms**: NUM = ridge on the pillar-1 MLB numbers plus text-length controls. TEXT = NUM plus five Jev
  probabilities: power, contact concern, discipline, injury and declining for batters; velocity, put-away
  pitch, control concern, injury and declining for pitchers. Leave-one-arrival-year-out.
- **Pre-registered** in [`PREREG.md`](study4-foreign/PREREG.md) (commit `67dce06`) after two opus audits.
  They added the identity gate and raw-response logging, moved the memory probe into separate requests,
  and changed ADDS to require that TEXT also beat NUM outright.

**Result: NO GAIN.**

| | MAE NUM | MAE TEXT | Shuffled-feature floor (mean) | p |
|---|---|---|---|---|
| Batters | 0.1308 | 0.1364 | +0.0064 | 0.41 |
| Pitchers | 0.0451 | 0.0489 | +0.0033 | 0.62 |

The real readings did no better than the same readings shuffled within arrival year. An independent
re-implementation gave the same reading.

**Jev did read the articles.** The features spread out (sd 0.14-0.39) and follow the text. Pitchers
whose article gives a fastball of 95+ mph or 150+ km/h average 0.89 on "hard fastball" and the others
0.34 (AUC 0.88). Injury, release and home-run words give AUCs of 0.91-0.95. The memory probe ("strong
first season in Japan", asked separately, never an input) showed no detectable signal (AUC 0.43 / 0.58).

**Limits.** At n 51 / 69 only a large gain is detectable, so this is not evidence that the text
carries nothing. Pitchers' signs all went the declared way. Post-hoc, in-sample correlations exist
(e.g. put-away pitch +0.30) and are not claimed. Cost: 348 calls (main + probe), 1.07M input tokens,
$0.045 on a free-tier key. Details: [`RESULTS.md`](study4-foreign/RESULTS.md).

## Study 3 — Jev as a feature extractor: pre-draft reports blended with numbers

Studies 1 and 2 asked Jev to turn numbers into a number, where a fitted model wins. Jev is built
to read text and return typed judgments that ordinary code then uses, so Study 3 gives it text with
no numeric twin: the MLB.com pre-draft report that StatsAPI carries for each pick (`blurb`, 2017 on).

- **Data**: 310 players drafted 2017-2020 (random, sized to the free credit), outcome = MLB debut by
  2026-10-02 (124 debuts). Names, initials and school words masked. The report text is MLB's and is
  not committed; `collect.py` rebuilds it.
- **Arms**: NUM = logistic regression on pick, pre-draft rank, slot value, age, bats/throws, role,
  year. TEXT = NUM + six Jev probabilities (hitting doubts, command doubts, injury, raw, upside,
  makeup praised). Out-of-fold over 20 x 10-fold CV.
- **Pre-registered** in [`PREREG.md`](study3-draft/PREREG.md) (commit `fd52851`, before any scored
  call); two opus pre-run audits changed the primary rule to a shuffled-feature floor, removed the
  signing bonus (it encodes whether the player signed) and de-duplicated re-drafted players.

**Result: NO GAIN.** Log loss NUM 0.6120 / TEXT 0.6224, AUC 0.698 / 0.687. The difference (+0.0104)
sits on the floor of the same six columns shuffled within role x pick tier (mean +0.0094, p 0.46).
An independent re-implementation gave the same reading (floor p 0.39). The memory probe ("did this
player reach the majors?", never a model input) had AUC 0.605 alone and added nothing.

**Exploratory (not pre-registered).** Of the six readings, "makeup, work ethic or baseball
intelligence is praised" separates debuts within pick tiers best (AUC 0.604, bootstrap 0.53-0.68),
but the report's length alone does almost as well (0.597), makeup correlates with having a prospect
rank (-0.44), and the effect sits in the first 30 picks and after pick 300. It is a lead for a
larger, registered test, not a finding.

**Limits.** 310 players is enough only for a large effect. Masking hides names but not relatives,
teammates or mascots (6 of 10 audited texts kept such clues). Cost: 310 calls, 253,708 input tokens,
$0.0107 on OpenRouter's free allowance.

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
  20 and on 50 past examples (descriptive; the crossover rule was not reached because the
  Marcel-lite rule fires first).
- Without the 17 extreme lines (any feature |z| > 2.5, i.e. stars that rounding cannot hide),
  Jev vs climatology is −0.009, 95% [−0.024, +0.005]: the skill is no longer distinguishable from zero.
- Recall probe (blend each of 50 hitters with a statistical neighbour to destroy identity): Jev's
  score improved more on blended lines than the fitted model's (−0.031, 95% [−0.055, −0.007]).
  Blending also narrows the outcomes (sd of Δ 0.036 → 0.029 on these 50), which favours narrow
  forecasts like Jev's. Recall would make Jev *worse* on blended lines, the narrowing makes it
  *better*, and only the sum is observed, so **this probe cannot say whether Jev recalls players**
  (an earlier version of this README said it ruled out a penalty larger than 0.024; it does not).

**Where it loses (post-hoc, not pre-registered — [`results/diagnose_output.txt`](study2-projection/results/diagnose_output.txt)).**
Jev gets the *direction* nearly as well as the rule (correlation with the real change 0.57 vs
0.62). It uses the right signals — it expects hitters far above the league mean to fall back,
and it uses the wOBA − xwOBA "luck" gap. Fitting both signals jointly
([`deepdive.py`](study2-projection/deepdive.py)), Jev's forecast gives back 0.20 of a point per point
above the league mean and 0.32 per point of luck, against 0.43 and 0.43 in the 1,620 training pairs:
**it under-uses regression to the mean most**. (An earlier version read the marginal correlations
−0.68 vs −0.43 as "leans on luck strongly"; the joint fit says luck is used a bit *less* than it should
be.) What it gets wrong, in this sample
(2025→26, hitters with ≥ 250 PA in both seasons), is the **size of the moves**: it puts 2% on a
big drop (actual 14.5%) and 9% on a big rise (actual 22.5%), and over-weights "about the same"
and "small rise" (0.33 / 0.34 vs actual 0.22 / 0.18). Real hitters moved much further than Jev
expected, and RPS punishes that.

Repairs, all post-hoc and without new Jev calls ([`results/deepdive_output.txt`](study2-projection/results/deepdive_output.txt)):
Jev's expected change with MARCEL-LITE's width gives RPS 0.1624 (vs MARCEL-LITE +0.014,
95% [+0.004, +0.023]); flattening Jev's bins with a temperature chosen by 10-fold CV gives 0.1681;
also adding the missing regression to the mean ((0.43 − 0.20) × (wOBA − league), both weights fixed
without 2026 outcomes) gives 0.1505, indistinguishable from MARCEL-LITE (+0.002, 95% [−0.005, +0.008]).

Cost: 277 calls, 189,677 input tokens, $0.0080 at list price, from OpenRouter's free allowance
(account balance $0, no card). Full output: [`results/analyze_output.txt`](study2-projection/results/analyze_output.txt).

## Study 1 — ABS pitch challenges (control)

> **Correction (2026-09-30): the extractor missed a quarter of the challenges.** When the final call of a
> challenged pitch ends the plate appearance (strikeout / walk), StatsAPI stores `reviewDetails` on the
> **play** (`allPlays[k].reviewDetails`), not on the pitch event. `extract.jq` read only the pitch event.
> Re-collecting Aug 1 – Sep 27 with both locations: 3,543 challenges, of which 893 (25%) were missed;
> their overturn rate is 0.486 vs 0.568 for the rows we had. All 250 evaluation rows come from the
> captured part, so Study 1 describes challenges on which the plate appearance went on. The
> distance-only baseline refitted on the full August set scores Brier 0.102 on the full September set
> (0.112 on the captured part). Jev was not re-asked (the key's free allowance is spent). The fixed
> extractor ([`extract2.jq`](extract2.jq)) and the check ([`s1_missing.py`](s1_missing.py),
> output [`results/s1_missing_output.txt`](results/s1_missing_output.txt)) are in this repo.

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
