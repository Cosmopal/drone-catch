#!/bin/bash
# Lead final steer: earn the VERB with the PAIRED DELTA (soft.pull_in -
# fixed.pull_in) convergence across offset + finger-count, since the single-cell
# bands overlap. Plus soft sign cells + the boundary scans that got killed.
# NO `set -e`: a single cell failing/timing out must NOT abort later stages
# (that would leave partial evidence that looks complete — lead's heads-up).
cd /mnt/c/Users/Palash/Projects/robots/drone-catch/.claude/worktrees/grasp-iter2
L=docs/cage_frames/iter2/logs
source ~/miniconda3/etc/profile.d/conda.sh; conda activate robots
run() { python tests/cage_harness.py "$@" 2>&1 | grep -v "pybullet build" || echo "CELL_FAILED: $*"; }

: > $L/paired.txt
echo "===== PAIRED delta soft-fixed (decides 're-centers MORE') =====" | tee -a $L/paired.txt
for cell in "4 0.025 finger" "4 0.035 finger" "6 0.025 finger" "8 0.025 finger" "4 0.025 gap"; do
  set -- $cell
  echo "########## soft-vs-fixed n=$1 off=$2 dir=$3 ##########" | tee -a $L/paired.txt
  run --paired --n $1 --offset $2 --dir $3 | tee -a $L/paired.txt
done
echo "PAIRED_DONE" | tee -a $L/paired.txt

: > $L/soft_conv.txt
echo "===== SOFT pull-in SIGN convergence (offset + finger-count) =====" | tee -a $L/soft_conv.txt
for cell in "soft 4 0.015 finger" "soft 4 0.035 finger" "soft 6 0.025 finger" "soft 8 0.025 finger"; do
  set -- $cell
  echo "########## $cell ##########" | tee -a $L/soft_conv.txt
  run --converge --strategy $1 --n $2 --offset $3 --dir $4 | tee -a $L/soft_conv.txt
done
echo "SOFTCONV_DONE" | tee -a $L/soft_conv.txt

: > $L/boundary.txt
echo "===== BOUNDARY scans =====" | tee -a $L/boundary.txt
for cell in "fixed 4 gap" "fixed 4 finger" "soft 4 gap" "soft 4 finger" "yale 4 finger"; do
  set -- $cell
  echo "########## $cell ##########" | tee -a $L/boundary.txt
  run --boundary --strategy $1 --n $2 --dir $3 | tee -a $L/boundary.txt
done
echo "BOUNDARY_DONE" | tee -a $L/boundary.txt
echo "ALL_FOLLOWUP_DONE"
