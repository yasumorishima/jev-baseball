"""Ask Jev about each test batter (227) and each blended probe line (50). Resumable; stops on refusal.

Needs OPENROUTER_API_KEY in the environment; the key is never printed.
"""
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"
OUT = "jev_answers.jsonl"
RAW = "jev_raw.jsonl"


def r5(x):
    return round(round(x / 0.005) * 0.005, 3)


def age_band(a):
    return "25 or younger" if a <= 25 else "26-29" if a <= 29 else "30-33" if a <= 33 else "34 or older"


POS = {"C": "catcher", "1B": "infielder", "2B": "infielder", "3B": "infielder", "SS": "infielder",
       "LF": "outfielder", "CF": "outfielder", "RF": "outfielder", "DH": "designated hitter"}


def state(u, lg):
    s = {
        "context": ("An anonymous MLB hitter's 2025 regular season. Predict how his wOBA changes "
                    "in 2026. League-average wOBA in 2025 was %.3f." % lg),
        "age_band": age_band(u["age"]),
        "position": POS[u["primary_position"]],
        "plate_appearances": int(round(u["pa"] / 25) * 25),
        "wOBA": r5(u["woba"]),
        "xwOBA": r5(u["xwoba"]),
        "strikeout_rate_pct": round(u["k_rate"] * 100),
        "walk_rate_pct": round(u["bb_rate"] * 100),
        "ISO": r5(u["iso"]),
        "BABIP": r5(u["babip"]),
    }
    for k, name in (("gb_rate", "ground_ball_rate_pct"), ("fb_rate", "fly_ball_rate_pct"),
                    ("pull_air_rate", "pulled_air_ball_rate_pct")):
        if u.get(k) is not None:
            s[name] = round(u[k] * 100)
    if u.get("sprint_speed") is not None:
        s["sprint_speed_ft_per_s"] = round(u["sprint_speed"] * 2) / 2
    return s


def questions(cuts):
    c = [round(x * 1000) for x in cuts]   # in wOBA points (thousandths)
    labels = [f"Big drop: wOBA falls by more than {-c[0]} points",
              f"Small drop: falls by {-c[1]} to {-c[0]} points",
              f"About the same: changes by {c[1]:+d} to {c[2]:+d} points",
              f"Small rise: rises by {c[2]} to {c[3]} points",
              f"Big rise: rises by more than {c[3]} points"]
    return {
        "delta_bin": {"type": "score",
                      "instructions": ("How will this hitter's wOBA in 2026 compare with his 2025 wOBA? "
                                       "(1 point = 0.001 of wOBA)"),
                      "criteria": labels},
        "wOBA_up": {"type": "noul",
                    "instructions": "Will this hitter's 2026 wOBA be higher than his 2025 wOBA?",
                    "criteria": {"true": "2026 wOBA is higher than 2025 wOBA.",
                                 "false": "2026 wOBA is equal to or lower than 2025 wOBA."}},
    }


def call(body, key):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main(limit=None):
    key = os.environ["OPENROUTER_API_KEY"]
    fz = json.load(open("frozen.json"))
    qs = questions(fz["cuts"])
    jobs = [("test", i, u) for i, u in enumerate(json.load(open("test.json")))]
    jobs += [("probe", i, u) for i, u in enumerate(json.load(open("probe.json")))]
    # Fixed shuffled order, so a run that stops early is not biased toward low player ids,
    # and probe lines are interleaved rather than all left for the end.
    random.Random(20260929).shuffle(jobs)
    done = set()
    if os.path.exists(OUT):
        done = {(a["set"], a["idx"]) for a in map(json.loads, open(OUT))}
    cost, sent = 0.0, 0
    with open(OUT, "a") as f:
        for kind, i, u in jobs:
            if (kind, i) in done:
                continue
            if limit is not None and sent >= limit:
                break
            sent += 1
            body = {"model": MODEL, "state": state(u, fz["lg2025"]), "questions": qs}
            try:
                resp = call(body, key)
            except urllib.error.HTTPError as e:
                print(f"STOP at {kind} {i}: HTTP {e.code} {e.read()[:200]!r}")
                sys.exit(1)
            with open(RAW, "a") as g:          # save before parsing: a paid call is never lost
                g.write(json.dumps({"set": kind, "idx": i, "resp": resp}) + "\n")
            try:
                a = resp["answers"]
                probs = [a["delta_bin"]["probabilities"][str(k)] for k in range(5)]
                p_up = a["wOBA_up"]["noul"]
            except (KeyError, TypeError):
                print(f"STOP at {kind} {i}: unexpected reply saved to {RAW}")
                sys.exit(1)
            cost += resp.get("usage", {}).get("cost", 0) or 0
            f.write(json.dumps({"set": kind, "idx": i, "bin_probs": probs, "p_up": p_up,
                                "model": resp.get("model"), "usage": resp.get("usage")}) + "\n")
            f.flush()
            time.sleep(0.2)
    print(f"done; cost this run {cost:.6f}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        fz = json.load(open("frozen.json"))
        print(json.dumps({"state": state(json.load(open("test.json"))[0], fz["lg2025"]),
                          "questions": questions(fz["cuts"])}, indent=1))
    elif len(sys.argv) > 2 and sys.argv[1] == "--limit":
        main(int(sys.argv[2]))
    else:
        main()
