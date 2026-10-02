"""Simulate run_jev4.py without OpenRouter: fake call_raw, temp data dir. Checks logging-before-parse,
stop on exception (exit 1), rebuild from raw.jsonl, no re-buy, probe separation."""
import json, os, shutil, subprocess, sys

SRC = os.path.expanduser("~/claude-scratch/jev-baseball/study4-foreign/")
T = os.path.expanduser("~/claude-scratch/sim4/")
shutil.rmtree(T, ignore_errors=True)
os.makedirs(T + "data")
shutil.copy(os.path.expanduser("~/claude-scratch/jev/foreign/states.json"), T + "data/states.json")
src = open(SRC + "run_jev4.py").read().replace('os.path.expanduser("~/claude-scratch/jev/foreign/")', repr(T + "data/"))
open(T + "run_jev4.py", "w").write(src)
fake = '''
import json, os
from jevq4_real import *
import jevq4_real as R
N = int(os.environ.get("SIM_FAIL_AT", "-1")); C = [0]
def call_raw(st, key, questions=QUESTIONS, timeout=90):
    C[0] += 1
    if C[0] == N: raise ConnectionResetError("sim")
    if C[0] % 7 == 0: return b"garbage"
    a = {}
    for k, q in questions.items():
        a[k] = {"choice": "pitcher"} if q["type"] == "choice" else {"noul": 0.5}
    return json.dumps({"answers": a}).encode()
def key(): return "x"
'''
shutil.copy(SRC + "jevq4.py", T + "jevq4_real.py")
open(T + "jevq4.py", "w").write(fake)

def run(env, *a):
    r = subprocess.run([sys.executable, T + "run_jev4.py", *a], env=dict(os.environ, **env), capture_output=True, text=True)
    return r.returncode, r.stdout.strip().splitlines()[-1]

print("run1 fail at 20:", run({"SIM_FAIL_AT": "20"}))
raw = [json.loads(l) for l in open(T + "data/raw.jsonl")]
print("raw lines", len(raw), "answers", len(json.load(open(T + "data/answers.json"))))
# simulate crash after logging but before save: drop the last answer from answers.json
A = json.load(open(T + "data/answers.json")); last = raw[-1]["pid"]
if last in A:
    del A[last]; json.dump(A, open(T + "data/answers.json", "w"))
print("run2 full:", run({}))
raw2 = [json.loads(l)["pid"] for l in open(T + "data/raw.jsonl")]
A2 = json.load(open(T + "data/answers.json"))
print("raw lines", len(raw2), "unique", len(set(raw2)), "answers", len(A2), "dropped-before-save restored", last in A2)
print("probe:", run({}, "--probe"))
P = json.load(open(T + "data/probe.json"))
print("probe answers", len(P), "keys", set(k for a in P.values() for k in a), "main raw unchanged", len(open(T + "data/raw.jsonl").readlines()) == len(raw2))
