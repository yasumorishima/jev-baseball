"""Study 4 shared pieces: the Jev question set (one request per player) and the call."""
import json
import os
import time
import urllib.error
import urllib.request

MODEL = "typesafe/jev-1.13"
URL = "https://openrouter.ai/api/alpha/decisions"


def N(what):
    return {"type": "noul", "instructions": what, "criteria": {"true": "yes", "false": "no"}}


QUESTIONS = {
    "role": {"type": "choice", "instructions": "Player role in these texts",
             "criteria": {"pitcher": "pitcher", "hitter": "position player", "two_way": "both"}},
    # hitter features
    "power": N("The texts describe him as a power hitter or note high home-run totals (no if he is a pitcher only)"),
    "contact_concern": N("The texts mention strikeouts, swing-and-miss or a low batting average as a weakness (no if he is a pitcher only)"),
    "discipline": N("The texts praise his batting eye, walks or on-base ability (no if he is a pitcher only)"),
    # pitcher features
    "velocity": N("The texts describe a hard fastball (about 95 mph / 150 km/h or more) or call him a power pitcher (no if he is a hitter only)"),
    "put_away": N("The texts describe a strikeout pitch (a plus breaking ball, splitter or changeup) or high strikeout totals (no if he is a hitter only)"),
    "control_concern": N("The texts mention control, command or walk problems (no if he is a hitter only)"),
    # both
    "injury": N("A significant injury, surgery or long absence before his move to Japan is mentioned"),
    "declining": N("In the seasons just before his move to Japan he lost his major-league role: demoted, designated for assignment, released or mostly in the minors"),
}
# memory probe: asked in a SEPARATE request after the main run (so it cannot prime the features), never a
# model input, only if the key still has credit
PROBE = {"probe_good_japan": N("This player had a strong first season in Japan")}
BAT = ["power", "contact_concern", "discipline", "injury", "declining"]
PIT = ["velocity", "put_away", "control_concern", "injury", "declining"]


def state(s):
    return {"ja_wikipedia_before_arrival": s["ja"] or "(none)",
            "en_wikipedia_before_arrival": s["en"] or "(none)"}


def call_raw(st, key, questions=QUESTIONS, timeout=90):
    """One request; returns the raw response bytes (the caller logs them before parsing). Retries only on
    429 (not billed); any other failure is raised to the caller."""
    body = json.dumps({"model": MODEL, "state": st, "questions": questions}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json"})
    for k in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or k == 2:
                raise
            time.sleep(10 * (k + 1))


def key():
    return os.environ["OPENROUTER_API_KEY"]
