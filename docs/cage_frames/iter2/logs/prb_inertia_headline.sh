#!/bin/bash
# GATE ON THE VERDICT-FLIP (lead): is the faithful-Yale FREE-ball behavior
# (caged + re-centered) INVARIANT to the inertia regularization scale, or is the
# flip a ×50 artifact? Run the headline free-ball cells at inertia 30/50/100 and
# report escape-margin / pull-in / #fingers / caged. Committed log.
cd /mnt/c/Users/Palash/Projects/robots/drone-catch/.claude/worktrees/grasp-iter2
source ~/miniconda3/etc/profile.d/conda.sh; conda activate robots
# wait for the provenance run to free the CPU
until grep -q "PRB_PROVENANCE_DONE" docs/cage_frames/iter2/logs/prb_provenance.out 2>/dev/null; do sleep 15; done
L=docs/cage_frames/iter2/logs
: > $L/prb_inertia_headline.txt
echo "=== FREE-BALL headline behavior vs inertia scale (verdict-flip gate) ===" | tee -a $L/prb_inertia_headline.txt
for cell in "0.025 finger" "0.035 gap"; do
  set -- $cell
  echo "#### prb 2.5/3.5 off=$1 dir=$2 ####" | tee -a $L/prb_inertia_headline.txt
  for isc in 30 50 100; do
    line=$(python tests/cage_harness.py --strategy prb --n 4 --offset $1 --dir $2 --quality --prb-inertia $isc 2>&1 | grep -vE "pybullet build" | grep -E "QUALITY|centering")
    echo "  inertia=$isc:" | tee -a $L/prb_inertia_headline.txt
    echo "$line" | sed 's/^/    /' | tee -a $L/prb_inertia_headline.txt
  done
done
echo "PRB_INERTIA_HEADLINE_DONE" | tee -a $L/prb_inertia_headline.txt
