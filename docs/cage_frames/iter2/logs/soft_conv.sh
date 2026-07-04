#!/bin/bash
# Lead steer #4: is SOFT's pull-in SIGN convergent across the FINGER direction
# (even where EM magnitude is a knife-edge)? Extra soft convergence cells +
# re-run the boundary scans that got killed.
set -e
cd /mnt/c/Users/Palash/Projects/robots/drone-catch/.claude/worktrees/grasp-iter2
L=docs/cage_frames/iter2/logs
source ~/miniconda3/etc/profile.d/conda.sh; conda activate robots

: > $L/soft_conv.txt
echo "===== SOFT pull-in SIGN convergence (finger dir + n6/n8) =====" | tee -a $L/soft_conv.txt
for cell in "soft 4 0.015 finger" "soft 4 0.035 finger" "soft 6 0.025 finger" "soft 8 0.025 finger" "soft 4 0.025 gap"; do
  set -- $cell
  echo "########## $cell ##########" | tee -a $L/soft_conv.txt
  python tests/cage_harness.py --converge --strategy $1 --n $2 --offset $3 --dir $4 2>&1 | grep -v "pybullet build" | tee -a $L/soft_conv.txt
done
echo "SOFTCONV_DONE" | tee -a $L/soft_conv.txt

: > $L/boundary.txt
echo "===== BOUNDARY scans =====" | tee -a $L/boundary.txt
for cell in "fixed 4 gap" "fixed 4 finger" "soft 4 gap" "soft 4 finger" "yale 4 finger"; do
  set -- $cell
  echo "########## $cell ##########" | tee -a $L/boundary.txt
  python tests/cage_harness.py --boundary --strategy $1 --n $2 --dir $3 2>&1 | grep -v "pybullet build" | tee -a $L/boundary.txt
done
echo "BOUNDARY_DONE" | tee -a $L/boundary.txt
echo "SOFTCONV_ALL_DONE"
