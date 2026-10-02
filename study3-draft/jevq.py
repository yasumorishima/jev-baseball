"""Study 3 shared pieces: name masking and the Jev question set (one request per player)."""
import difflib
import json
import os
import re
import unicodedata
import time
import urllib.error
import urllib.request

MODEL = "typesafe/jev-1.13"
URL = "https://openrouter.ai/api/alpha/decisions"


GENERIC = {"high", "school", "hs", "university", "college", "state", "of", "the", "at", "community",
           "academy", "prep", "jc", "junior", "christian", "catholic", "central", "north", "south",
           "east", "west", "saint", "st", "a&m", "tech", "institute", "county"}


def fold(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def mask(row):
    """Mask the player's own names (accent-folded, fuzzy for misspellings), initials such as "MJ",
    and the distinctive words of the school name. Family names of relatives and teammates stay; the
    memory probe in the prereg reports on recognition."""
    t = fold(row["blurb"])
    for n in sorted({fold(n) for n in row["names"]}, key=len, reverse=True):
        if " " in n and len(n) >= 5:
            t = re.sub(r"\b%s\b" % re.escape(n), "the player", t)
    surname = fold(row["names"][0]).split()
    if len(surname) >= 3:      # e.g. "De La Torre": mask the multi-word surname as a phrase
        t = re.sub(r"\b%s\b" % re.escape(" ".join(surname[1:])), "the player", t)
    names = set()
    for n in row["names"]:
        for part in fold(n).replace("-", " ").split():
            part = part.strip(".,")
            if len(part) >= 3:
                names.add(part.lower())
    full = fold(row["names"][0]).split()
    initials = (full[0][0] + full[-1][0]).upper() if len(full) >= 2 else None
    school = set()
    if row.get("school_name"):
        for w in re.findall(r"[A-Za-z&'.]+", fold(row["school_name"])):
            w = w.strip(".'").lower()
            if len(w) >= 3 and w not in GENERIC:
                school.add(w)

    def sub(m):
        w = m.group(0)
        base = re.sub(r"'s$", "", w)
        lw = base.lower()
        tail = "'s" if w.endswith("'s") else ""
        if not base[0].isupper():
            return w
        if len(lw) >= 3 and (lw in names or any(
                len(lw) >= 4 and difflib.SequenceMatcher(None, lw, n).ratio() >= 0.80 for n in names)):
            return "the player" + tail
        if lw in school:
            return "school" + tail
        if initials and base == initials:
            return "the player" + tail
        return w

    return re.sub(r"[A-Za-z][A-Za-z']*[A-Za-z]|[A-Za-z]", sub, t)


def N(what):
    return {"type": "noul", "instructions": what, "criteria": {"true": "yes", "false": "no"}}


# Features (used by the model). Role is shared by both arms; the six yes/no judgments are the
# text arm. "reached" is the memory probe: it is never a model input.
QUESTIONS = {
    "role": {"type": "choice", "instructions": "Player role",
             "criteria": {"pitcher": "pitcher", "hitter": "position player", "two_way": "both"}},
    "hit_concern": N("Doubts are raised about his hitting: contact, swing-and-miss or approach (no if he is a pitcher only)"),
    "cmd_concern": N("Doubts are raised about his control, command or delivery (no if he is a hitter only)"),
    "injury": N("An injury, surgery or health concern is mentioned"),
    "raw": N("Described as raw, unrefined or far from the majors"),
    "upside": N("Projectable physical upside or a high ceiling is described"),
    "makeup": N("Makeup, work ethic or baseball intelligence is praised"),
    "reached": N("This player went on to play in the major leagues"),
}
FEATURES = ["hit_concern", "cmd_concern", "injury", "raw", "upside", "makeup"]


def call(text, key, questions=QUESTIONS, timeout=60):
    """One request. Retries only on 429 (not billed); any other failure is raised to the caller."""
    body = json.dumps({"model": MODEL, "state": {"scouting_report": text},
                       "questions": questions}).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Authorization": "Bearer " + key, "Content-Type": "application/json"})
    for k in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or k == 2:
                raise
            time.sleep(10 * (k + 1))


def key():
    return os.environ["OPENROUTER_API_KEY"]
