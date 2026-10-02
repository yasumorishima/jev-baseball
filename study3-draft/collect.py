"""Study 3 collection: MLB StatsAPI Rule 4 draft picks that carry a pre-draft scouting blurb, 2017-2021.

Writes ~/claude-scratch/jev/draft/picks.json (outside the repo: the blurbs are MLB text and are not
redistributed). Only draft-time fields are kept; person fields that the API returns as *current*
values (primaryPosition, height, weight) are deliberately not read. The outcome is mlbDebutDate as
of the collection date.
"""
import datetime
import json
import os
import time
import urllib.request

OUT = os.path.expanduser("~/claude-scratch/jev/draft/picks.json")
YEARS = range(2017, 2022)
# first day of each Rule 4 draft (MLB.com); age is measured at this date
DRAFT_DAY = {2017: "2017-06-12", 2018: "2018-06-04", 2019: "2019-06-03", 2020: "2020-06-10",
             2021: "2021-07-11"}


def get(url):
    for k in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception:
            if k == 3:
                raise
            time.sleep(5 * (k + 1))


def age(birth, day):
    b = datetime.date.fromisoformat(birth)
    d = datetime.date.fromisoformat(day)
    return (d - b).days / 365.25


rows = []
for y in YEARS:
    d = get("https://statsapi.mlb.com/api/v1/draft/%d" % y)
    picks = [p for r in d["drafts"]["rounds"] for p in r["picks"]]
    picks = [p for p in picks if p.get("blurb") and p.get("person")
             and p.get("draftType", {}).get("code") == "JR"]
    ids = [p["person"]["id"] for p in picks]
    debut = {}
    for i in range(0, len(ids), 100):
        pp = get("https://statsapi.mlb.com/api/v1/people?personIds=" + ",".join(map(str, ids[i:i + 100])))
        for q in pp["people"]:
            debut[q["id"]] = q.get("mlbDebutDate")
        time.sleep(1)
    for p in picks:
        pe = p["person"]
        sc = p.get("school") or {}
        rows.append({
            "year": y,
            "pid": pe["id"],
            "pick": p.get("pickNumber"),
            "round": p.get("pickRound"),
            "rank": p.get("rank"),
            "bonus": float(p["signingBonus"]) if p.get("signingBonus") else None,
            "pick_value": float(p["pickValue"]) if p.get("pickValue") else None,
            "school_class": sc.get("schoolClass"),
            "school_name": sc.get("name"),
            "school_country": sc.get("country"),
            "age": age(pe["birthDate"], DRAFT_DAY[y]) if pe.get("birthDate") else None,
            "bats": (pe.get("batSide") or {}).get("code"),
            "throws": (pe.get("pitchHand") or {}).get("code"),
            "names": [pe.get(k) for k in ("fullName", "firstName", "lastName", "useName", "middleName",
                                           "useLastName", "nameFirstLast") if pe.get(k)],
            "blurb": p["blurb"],
            "debut": debut.get(pe["id"]),
        })
    print(y, "picks with blurb", len(picks), "debuted", sum(1 for p in picks if debut.get(p["person"]["id"])))
    time.sleep(1)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"collected": datetime.date.today().isoformat(), "rows": rows}, open(OUT, "w"))
print("rows", len(rows), "->", OUT)
