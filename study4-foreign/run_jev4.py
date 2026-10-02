"""Study 4 calls: one Jev request per sample player (pillar-1 entrant with MLB pitch data and a pre-arrival
text that passed the identity gate), in a fixed random order. The raw response bytes are appended to
raw.jsonl before anything is parsed; any exception stops the run; a player already in raw.jsonl is never
called again (even if his response was unusable). With --probe the memory probe is asked in separate
requests, after the main run.

  python3 run_jev4.py            # main run  -> answers.json
  python3 run_jev4.py --probe    # probe run -> probe.json (only after the main run finished)
"""
import csv
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jevq4  # noqa: E402

NP = os.path.expanduser("~/claude-scratch/npbmlb/")
D = os.path.expanduser("~/claude-scratch/jev/foreign/")
PROBE = "--probe" in sys.argv
QS = jevq4.PROBE if PROBE else jevq4.QUESTIONS
P = D + ("probe.json" if PROBE else "answers.json")
RAW = D + ("probe_raw.jsonl" if PROBE else "raw.jsonl")
S = json.load(open(D + "states.json", encoding="utf-8"))
A = {}
seen = set()

ids = set()
for f in ("feat_bat.csv", "feat_pit.csv"):
    for r in csv.DictReader(open(NP + f, encoding="utf-8")):
        k = str(int(float(r["key_mlbam"])))
        if r["n"].strip() and k in S:
            ids.add(k)
order = sorted(ids)
random.Random(20261002).shuffle(order)
print("sample", len(order), "probe" if PROBE else "main", flush=True)
key = jevq4.key()


def save(obj, path):
    tmp = path + ".tmp"
    json.dump(obj, open(tmp, "w"))
    os.replace(tmp, path)


def valid(a):
    if set(a) != set(QS):
        return False
    for k, q in QS.items():
        if q["type"] == "choice":
            if a[k].get("choice") not in q["criteria"]:
                return False
        else:
            v = a[k].get("noul")
            if not isinstance(v, (int, float)) or not 0 <= v <= 1:
                return False
    return True


def parse(b):
    try:
        a = json.loads(b)["answers"]
        return a if valid(a) else None
    except Exception:  # noqa: BLE001
        return None


# answers are always rebuilt from raw.jsonl (the paid record), so a crash between logging and saving
# loses nothing; answers.json is a derived copy
if os.path.exists(RAW):
    for line in open(RAW):
        try:
            rec = json.loads(line)
        except Exception:  # noqa: BLE001  a torn last line: that call is treated as unanswered
            continue
        seen.add(rec["pid"])
        a = parse(rec["raw"])
        if a is not None:
            A[rec["pid"]] = a
    save(A, P)

bad, stopped = 0, False
for i, pid in enumerate(order):
    if pid in A or pid in seen:
        continue
    try:
        b = jevq4.call_raw(jevq4.state(S[pid]), key, QS)
    except Exception as e:  # noqa: BLE001  any failure stops the run; nothing is bought twice
        print("stopped at", i, repr(e), flush=True)
        stopped = True
        break
    with open(RAW, "a") as f:
        f.write(json.dumps({"pid": pid, "raw": b.decode("utf-8", "replace")}) + "\n")
    seen.add(pid)
    a = parse(b)
    if a is None:
        bad += 1
        print("unusable", pid, flush=True)
        continue
    A[pid] = a
    save(A, P)
    time.sleep(0.3)
print("answered", len(A), "unusable (this run)", bad, "of", len(order), flush=True)
sys.exit(1 if stopped else 0)
