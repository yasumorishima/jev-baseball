"""Study 3 calls: one Jev request per sampled player on the masked report. Resumable; stops on a
402/403 (credit limit) and analyses whatever was answered, as registered."""
import json
import os
import sys
import time
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jevq  # noqa: E402

D = os.path.expanduser("~/claude-scratch/jev/draft/")
S = json.load(open(D + "sample.json"))
P = D + "answers.json"
A = json.load(open(P)) if os.path.exists(P) else {}
RAW = D + "raw.jsonl"          # every paid response, before validation
REJ = D + "rejected.json"      # paid but invalid: counted as unanswered, never re-bought
J = set(json.load(open(REJ))) if os.path.exists(REJ) else set()
key = jevq.key()


def save(obj, path):
    tmp = path + ".tmp"
    json.dump(obj, open(tmp, "w"))
    os.replace(tmp, path)


def valid(a):
    if set(a) != set(jevq.QUESTIONS):
        return False
    if a["role"].get("choice") not in jevq.QUESTIONS["role"]["criteria"]:
        return False
    for k, q in jevq.QUESTIONS.items():
        if q["type"] == "noul":
            v = a[k].get("noul")
            if not isinstance(v, (int, float)) or not 0 <= v <= 1:
                return False
    return True


for i, r in enumerate(S):
    pid = str(r["pid"])
    if pid in A or pid in J:
        continue
    try:
        o = jevq.call(jevq.mask(r), key)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        print("stopped at", i, repr(e))
        break
    with open(RAW, "a") as f:
        f.write(json.dumps({"pid": r["pid"], "response": o}) + "\n")
    if not valid(o.get("answers", {})):
        J.add(pid)
        save(sorted(J), REJ)
        print("rejected", pid)
        continue
    A[pid] = o["answers"]
    save(A, P)
    time.sleep(0.3)
print("answered", len(A), "rejected", len(J), "of", len(S))
