#!/bin/bash
# Study 4 run chain: main calls -> analysis -> memory probe (separate requests) -> analysis with probe.
cd ~/claude-scratch/jev-baseball/study4-foreign || exit 1
exec 9>.run4.lock; flock -n 9 || exit 0
set -a; . ~/.openrouter_jev.env; set +a
python3 -u run_jev4.py > run_jev4.log 2>&1; echo "main exit $?" >> run_jev4.log
python3 -u analyze4.py > analyze4.out 2>&1
python3 -u run_jev4.py --probe > run_probe4.log 2>&1; echo "probe exit $?" >> run_probe4.log
python3 -u analyze4.py > analyze4_probe.out 2>&1
echo done > run4.done
