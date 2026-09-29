"""Send the 250 evaluation rows to Jev (two arms). Resumable; stops on the first refusal.

Needs OPENROUTER_API_KEY in the environment. The key value is never printed.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"
OUT = "jev_answers.jsonl"
RAW = "jev_raw.jsonl"

QUESTION = {
    "overturned": {
        "type": "noul",
        "instructions": ("An ABS (Automated Ball-Strike) challenge was made on this pitch. "
                         "Will the ABS review overturn the original call?"),
        "criteria": {
            "true": ("The tracked pitch location contradicts the original call "
                     "(a called strike that was outside the zone, or a called ball that touched the zone)."),
            "false": "The tracked pitch location agrees with the original call, so it stands.",
        },
    }
}


def state(r, arm):
    s = {
        "original_call": r["original_call"],
        "challenged_by": r["challenged_by"],
        "count_before_pitch": f'{r["balls"]}-{r["strikes"]}',
        "outs": r["outs"],
        "inning": f'{r["half"]} {r["inning"]}',
        "pitch_type": r["pitch_type"],
        "pitch_speed_mph": r["speed"],
        "geometry": {
            "units": "feet, from the catcher's view; x = 0 is the middle of home plate",
            "pitch_x_at_plate": round(r["pX"], 3),
            "pitch_height_at_plate": round(r["pZ"], 3),
            "zone_top": r["sz_top"],
            "zone_bottom": r["sz_bot"],
            "plate_half_width": 0.708,
            "ball_radius": 0.121,
            "rule": ("It is a strike if any part of the ball touches the zone, i.e. the ball's centre is within "
                     "ball_radius of the rectangle |x| <= plate_half_width, zone_bottom <= height <= zone_top."),
        },
    }
    if arm == "JEV-DIST":
        s["distance_wrong_side_of_call_inches"] = round(r["wrong_side_in"], 2)
        s["distance_definition"] = ("How far the pitch is on the wrong side of the original call, in inches. "
                                    "Positive means the tracked location contradicts the original call; "
                                    "negative means it agrees.")
    return s


def call(body, key):
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {key}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main():
    key = os.environ["OPENROUTER_API_KEY"]
    sample = json.load(open("eval_sample.json"))
    done = set()
    if os.path.exists(OUT):
        for line in open(OUT):
            a = json.loads(line)
            done.add((a["arm"], a["idx"]))
    cost = 0.0
    with open(OUT, "a") as f:
        for arm in ("JEV-DIST", "JEV-RAW"):
            for i, r in enumerate(sample):
                if (arm, i) in done:
                    continue
                body = {"model": MODEL, "state": state(r, arm), "questions": QUESTION}
                try:
                    resp = call(body, key)
                except urllib.error.HTTPError as e:
                    print(f"STOP at {arm} {i}: HTTP {e.code} {e.read()[:200]!r}")
                    sys.exit(1)
                # Save the raw reply BEFORE parsing, so a paid call is never lost or repeated.
                with open(RAW, "a") as g:
                    g.write(json.dumps({"arm": arm, "idx": i, "resp": resp}) + "\n")
                try:
                    p = resp["answers"]["overturned"]["noul"]
                except (KeyError, TypeError):
                    print(f"STOP at {arm} {i}: unexpected reply saved to {RAW}")
                    sys.exit(1)
                cost += resp.get("usage", {}).get("cost", 0) or 0
                f.write(json.dumps({"arm": arm, "idx": i, "p": p, "model": resp.get("model"),
                                    "usage": resp.get("usage")}) + "\n")
                f.flush()
                time.sleep(0.2)
    print(f"done; cost this run {cost:.6f}")


if __name__ == "__main__":
    main()
