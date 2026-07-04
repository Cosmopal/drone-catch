#!/bin/bash
# Boundary stage ONLY (the previous run's timeout fired mid-boundary; hibernation
# ate the wall-clock budget). No tight outer timeout — rely on per-cell tolerance.
# Fresh log; canonical output is THIS stdout (boundary_rerun.out), not the tee.
cd /mnt/c/Users/Palash/Projects/robots/drone-catch/.claude/worktrees/grasp-iter2
source ~/miniconda3/etc/profile.d/conda.sh; conda activate robots
run() { python tests/cage_harness.py "$@" 2>&1 | grep -v "pybullet build" || echo "CELL_FAILED: $*"; }

echo "===== BOUNDARY scans (rerun) ====="
for cell in "fixed 4 gap" "fixed 4 finger" "soft 4 gap" "soft 4 finger" "yale 4 finger"; do
  set -- $cell
  echo "########## $cell ##########"
  run --boundary --strategy $1 --n $2 --dir $3
done
echo "BOUNDARY_DONE"
