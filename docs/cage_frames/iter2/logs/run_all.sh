#!/bin/bash
# Full iteration-2 §2.2/§2.3 evidence run (sequential to avoid CPU contention).
set -e
cd /mnt/c/Users/Palash/Projects/robots/drone-catch/.claude/worktrees/grasp-iter2
L=docs/cage_frames/iter2/logs
source ~/miniconda3/etc/profile.d/conda.sh; conda activate robots

echo "===== QUALITY GRID ====="
python tests/cage_harness.py --quality-grid 2>&1 | grep -v "pybullet build" | tee $L/quality_grid.txt
echo "QGRID_DONE"

echo "===== CONVERGENCE =====" | tee $L/convergence.txt
for cell in "fixed 4 0.025 finger" "soft 4 0.025 finger" "soft 4 0.035 gap" "fixed 4 0.0 finger" "yale 4 0.025 finger"; do
  set -- $cell
  echo "########## $cell ##########" | tee -a $L/convergence.txt
  python tests/cage_harness.py --converge --strategy $1 --n $2 --offset $3 --dir $4 2>&1 | grep -v "pybullet build" | tee -a $L/convergence.txt
done
echo "CONV_DONE"

echo "===== BOUNDARY =====" | tee $L/boundary.txt
for cell in "fixed 4 gap" "fixed 4 finger" "soft 4 gap" "soft 4 finger"; do
  set -- $cell
  echo "########## $cell ##########" | tee -a $L/boundary.txt
  python tests/cage_harness.py --boundary --strategy $1 --n $2 --dir $3 2>&1 | grep -v "pybullet build" | tee -a $L/boundary.txt
done
echo "ALL_DONE"
