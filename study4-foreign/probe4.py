"""Cost probe: one Jev call on the longest-text entrant who is OUTSIDE the study sample (no MLB pitch data),
so no scored player is seen. Prints usage and remaining key credit."""
import csv, json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jevq4

S = json.load(open(os.path.expanduser("~/claude-scratch/jev/foreign/states.json"), encoding="utf-8"))
inside = set()
for f in ("feat_bat.csv", "feat_pit.csv"):
    for r in csv.DictReader(open(os.path.expanduser("~/claude-scratch/npbmlb/" + f), encoding="utf-8")):
        if r["n"].strip():
            inside.add(str(int(float(r["key_mlbam"]))))
out = [k for k in S if k not in inside]
k = max(out, key=lambda x: len(S[x]["ja"]) + len(S[x]["en"]))
print("outside-sample players with text", len(out), "probe on", k, "chars ja", len(S[k]["ja"]), "en", len(S[k]["en"]))
key = jevq4.key()
def credit():
    req = urllib.request.Request("https://openrouter.ai/api/v1/key", headers={"Authorization": "Bearer " + key})
    d = json.load(urllib.request.urlopen(req, timeout=30))["data"]
    return d.get("limit"), d.get("limit_remaining"), d.get("usage")
print("credit before (limit, remaining, usage)", credit())
o = json.loads(jevq4.call_raw(jevq4.state(S[k]), key, dict(jevq4.QUESTIONS, **jevq4.PROBE)))  # as run on 2026-10-02 (one request incl. probe)
os.makedirs(os.path.expanduser("~/claude-scratch/jev/foreign/"), exist_ok=True)
with open(os.path.expanduser("~/claude-scratch/jev/foreign/costprobe_raw.jsonl"), "a") as f:
    f.write(json.dumps({"pid": k, "response": o}) + "\n")
print("usage", o.get("usage"))
print("answers", {q: (a.get("noul") if "noul" in a else a.get("choice")) for q, a in o.get("answers", {}).items()})
print("credit after", credit())
