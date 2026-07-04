#!/bin/bash
# §2.4 — 3-angle HUD triptychs for the best/worst/comparison cells the written
# fixed-vs-soft-vs-Yale answer rests on. Stills only (fast); the soft finger
# re-center + migration already have a slow-mo. Run after the convergence job.
set -e
cd /mnt/c/Users/Palash/Projects/robots/drone-catch/.claude/worktrees/grasp-iter2
source ~/miniconda3/etc/profile.d/conda.sh; conda activate robots
O=docs/cage_frames/iter2
# worst soft (gap, weak converged hold) + best soft (finger re-center @3.5)
for c in "soft 4 0.035 gap" "soft 4 0.035 finger" "yale 4 0.025 gap" "fixed 4 0.035 gap"; do
  set -- $c
  python tests/cage_harness.py --quality-frames --strategy $1 --n $2 --offset $3 --dir $4 --out $O --no-video 2>&1 | grep -E "escape-margin|weakest"
done
echo "RENDER_BATCH_DONE"
