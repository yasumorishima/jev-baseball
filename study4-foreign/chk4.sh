#!/bin/bash
cd ~/claude-scratch/jev-baseball/study4-foreign || exit 1
exec 9>.chk4.lock; flock -n 9 || exit 0
python3 -u sim_run4.py > sim4.log 2>&1
mv sim_run4.py ~/claude-scratch/sim4/
bash dry4.sh > dry4.log 2>&1
echo done >> sim4.log
