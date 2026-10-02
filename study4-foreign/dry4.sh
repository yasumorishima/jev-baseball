#!/bin/bash
# Study 4 dry runs (synthetic answers only; no Jev call, no answer read).
cd ~/claude-scratch/jev-baseball/study4-foreign || exit 1
exec 9>.dry4.lock; flock -n 9 || exit 0
S='import sys,json
for l in sys.stdin:
  d=json.loads(l); print(d["kind"],d["n"],"d",round(d["d"],4),"floor",round(d["floor_mean"],4),round(d["floor_sd"],4),"p",round(d["p"],3),"holm",round(d["p_holm"],3),"mirror_holm",round(d["p_mirror_holm"],3),d["reading"])'
for m in informative noise numonly; do echo "== $m"; python3 analyze4.py --synthetic $m | python3 -c "$S"; done
for s in 1 2 3 4 5; do echo "== informative c=0.5 seed $s"; SYN_C=0.5 SYN_SEED=$s python3 analyze4.py --synthetic informative | python3 -c "$S"; done
echo done
