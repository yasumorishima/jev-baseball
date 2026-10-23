# CLAUDE.md — jev-baseball

Working rules for Claude Code (cloud or local). This file is the source of truth for this project; the
owner's local notes and the RPi5 scratch directories are not visible to cloud sessions (and the RPi5
copies of this project's working data were deleted by its disk cleanup on 2026-10-16/17/22).

## Session protocol (cloud)
The owner starts a session with just 「続き」/「つづきから」.
1. Read this file first, then `README.md`. Work on "Next tasks" in order.
2. Before ending, record what you did and what comes next **in this file** (update "Next tasks" and add a
   dated line to "Progress log"). This file is the only memory that survives between cloud sessions.
3. Cloud can push only its session branch: open a PR to `master` and merge it yourself (own repo) so the
   next session sees the update. Report the merged commit.
4. Write replies to the owner in Japanese (です/ます). Do not claim anything you did not run in this
   session. If no task is open, say so plainly; do not invent work.

## Progress log
- 2026-09-29 .. 10-02: Studies 1-4 pre-registered, run once and published (see README). All four are
  retrospective. Study 4 (foreign players) = NO GAIN (batters floor p 0.41, pitchers 0.62).
- 2026-10-08: MIT LICENSE + requirements.txt (PR #1).
- 2026-10-23: moved to cloud. Inventory: every Jev answer used in a result is committed; the inputs that
  were only on the RPi5 (Study 4 article titles / revision ids / identity gate output / cleaned states,
  Study 3 `picks.json`/`sample.json`, Study 2 `train/test/probe.json`, all `raw.jsonl`/`jev_raw.jsonl`
  files) are gone. No result is lost, but Studies 2-4 cannot currently be re-run from the repo exactly.

## What this is
Tests of TypeSafe Jev (`typesafe/jev-1.13`, a decision-only model that returns typed probabilities) on
baseball, each pre-registered before the first scored call:
- Study 1 ABS challenges — control (the outcome is a fixed-zone rule; baseline had to win).
- Study 2 next-season wOBA change (`study2-projection/`) — Jev has skill but is worse than Marcel-lite.
- Study 3 pre-draft reports + numbers → reaching MLB (`study3-draft/`) — NO GAIN.
- Study 4 pre-arrival Wikipedia text + MLB numbers → first NPB season (`study4-foreign/`) — NO GAIN.
The owner's main interest is foreign players in NPB (text + stats blended in an ordinary model).
Jev's intended use: read text/state and return typed judgments (classification, extraction, feature
generation) — do **not** ask it to turn numbers into a number (Studies 1/2 showed a fitted model wins).

## Non-negotiable discipline
1. **Pre-register, then run once.** Definitions, sample, questions, arms, floor and reading go into a
   `PREREG.md` committed before any scored Jev call. Gaps found before the run go into an AMENDMENT
   section before the run. Never change code, questions or definitions after seeing results.
2. **Compare against a shuffled-feature floor, not against zero** (extra columns cost MAE/log loss at
   this n; noise reads as "harm" against zero). "ADDS" also requires TEXT to beat NUM outright.
3. **Paid calls:** append the raw response bytes to a raw log *before* parsing; atomic saves; never buy
   the same unit twice (rebuild answers from the raw log on restart); only HTTP 429 is retried; any
   other error stops the run with exit 1. **Commit the raw log** with the results (in Studies 2-4 it
   stayed on the RPi5 and is now lost).
4. **Memory/leak:** Jev (version dated 2026-09-17) may know players and seasons up to then. Masking
   names does not stop recognition from a career description. A clean test needs outcomes after Jev's
   training data, frozen and committed before the outcome is published or read.
5. **Identity:** articles found by name search must pass the Wikidata P3541 (MLB ID) = key_mlbam gate.
6. Text features correlate with text length / attention (Study 3 makeup ≈ report length): always
   include a length control.
7. Code that produces a result gets an independent (opus) review before it runs; review claims are
   checked against code/data before being accepted. Report nulls as facts.
8. **Money:** free tier only. Never top up, add a card, raise a key limit, or suggest paying. If a call
   returns 402 or the key limit is reached, stop and report. Do not create keys on other accounts.
   SemIf (a public Jev reproduction) is not to be used (owner's decision). Cloudflare Workers AI needs
   prepaid credit (402) — not an option.
9. Do not commit third-party text: Wikipedia (CC BY-SA) article text and MLB.com draft blurbs stay out
   of the repo; commit titles, revision ids and timestamps instead (facts, enough to rebuild exactly).

## Next tasks (in order)
No evaluation is pending: nothing in this repo forecasts an outcome that has not yet been scored
(Studies 1-4 were all scored retrospectively; no Jev forecast targets NPB 2026 or MLB 2027).
The open work is reproducibility, which needs no Jev call:

1. **Study 4 rebuild manifest (no API).** README says the text is rebuilt "from revision ids", but no
   revision ids are committed. Rebuild in a scratch dir outside the repo:
   - pillar-1 inputs `links.csv`, `feat_bat.csv`, `feat_pit.csv` with the cloud recipe in
     `yasumorishima/npb-foreign-statcast` `CLAUDE.md` (note: Chadwick grew; `link_foreign.py` now gives
     313 rows vs the original 312 — record any sample difference);
   - `cov_ja.py`, `cov_en.py` → `fetch_ja_text.py`, `fetch_en_text.py` → `idgate4.py` → `prepare4.py`.
     Do not edit these scripts (rule 1). `cov_*.py`, `fetch_*_text.py` and `chk4b.py` hard-code
     `/home/yasu/claude-scratch/...`; the others use `~/claude-scratch/...`. Make both paths exist in
     the container instead: `mkdir -p ~/claude-scratch/jev/foreign ~/claude-scratch/npbmlb`, and if
     `$HOME` is not `/home/yasu` and `/home/yasu` does not exist, `mkdir -p /home && ln -s "$HOME" /home/yasu`. Then check `[ "$(readlink -f /home/yasu)" = "$(readlink -f "$HOME")" ]`; if it fails (an existing `/home/yasu`), the two path families point to different places — stop and report.
     Put the pillar-1 inputs in `~/claude-scratch/npbmlb/`. Do not edit `PREREG.md` (frozen, md5
     `9c864ffc37e9a2ae3f2f593de85bf3a9`).
   - Check against committed facts: `idgate4.log` (ja ok 231 / mismatch 5 / no_p3541 20; en 240 / 5 /
     18), 174 called players = the keys of `results/jev_answers.json`, primary rows 51 / 69.
   - Then run `analyze4.py` with the committed answers. It reads `~/claude-scratch/jev/foreign/answers.json`
     and `probe.json` (not `results/`), so first `cp study4-foreign/results/jev_answers.json
     ~/claude-scratch/jev/foreign/answers.json` and `cp study4-foreign/results/jev_probe.json
     ~/claude-scratch/jev/foreign/probe.json` (a missing `probe.json` only prints "memory probe: not run"
     — treat that line as a failed setup, not a result). Compare
     with `results/analyze4.out` / `analyze4_probe.out`. Name search results and Wikidata drift, so an
     exact match is not guaranteed: report any difference as a fact; never edit the frozen outputs.
   - Commit `study4-foreign/manifest.csv` (key_mlbam, lang, title, revid, timestamp, identity verdict —
     no text), and correct the README sentence if the rebuild cannot match.
2. **Study 2 pinned snapshot (no API).** `prepare.py` reads `mart_batter_season.parquet` from HF
   `yasumorishima/mlb-stats`; that file has changed since the freeze (last commit 2026-10-19). Find the
   HF dataset revision whose file md5 is `bcdbddd9ffd1d2da616536833f261bc4`, record it in
   `study2-projection/README` or the main README, and check that `analyze.py` reproduces
   `results/analyze_output.txt`. Run `prepare.py` only in a scratch copy: it **overwrites
   `frozen.json`**.
3. **Study 3** (no API, optional): `collect.py` labels debut by the collection date, so a re-collection
   today changes the outcome. Note in README that the frozen sample md5 is
   `0429dc62f625cbab80a39d72f570e433` and that debuts must be cut at 2026-10-02 to reproduce.

Not a task now (record only; start only on the owner's instruction): the clean leak-free check named in
Study 4 `PREREG.md` (arrivals after Jev's training data, frozen before their NPB stats are read).
2026 arrivals no longer qualify (their NPB 2026 stats are public and were read in npb-foreign-statcast).
The earliest qualifying cohort is 2027 arrivals: ja text cutoff 1 Mar 2027, freeze before NPB 2027
opening day, score after the 2027 season. One cohort will have fewer than 30 rows per role, which the
Study 4 rule treats as "no reading", so a registration must say how cohorts are pooled. It needs Jev
credit (see below).

## Data access (cloud network allowlist)
Already allowed: `statsapi.mlb.com`, `baseballsavant.mlb.com`, `npb.jp`, `huggingface.co` (+ CDN hosts),
`baseball-data.com`, `raw.githubusercontent.com`.
Needed additionally for task 1: `ja.wikipedia.org`, `en.wikipedia.org`, `www.wikidata.org`
(set a descriptive User-Agent, as the scripts do; back off on 429).
Needed only for Jev calls: `openrouter.ai`.

## Jev API (only if the owner explicitly asks for new calls)
- `POST https://openrouter.ai/api/alpha/decisions`, body `{model, state, questions}`,
  `model: typesafe/jev-1.13`; use a timeout on every request. The scripts read the key from
  `OPENROUTER_API_KEY`. Never print the key.
- The owner's key is a free-tier key with a spending cap; as of 2026-10-02 almost nothing was left
  (about $0.005 of a $0.05 cap). Study 4 cost ~3k input tokens per call. Check remaining credit with
  `GET https://openrouter.ai/api/v1/key` before any run and stop on 402.
- In cloud the key must be registered by the owner as an API credential for host `openrouter.ai`
  under the name `OPENROUTER_API_KEY`. Whether `typesafe/jev-1.13` is still served is unverified.

## Credits (keep in README)
MLB StatsAPI game feeds and draft data (© MLB Advanced Media, non-commercial research), HF
`yasumorishima/mlb-stats` (built from Baseball Savant / StatsAPI), npb.jp, Chadwick Register
(ODC-By 1.0), Wikipedia (CC BY-SA; text not redistributed), Wikidata (CC0).
