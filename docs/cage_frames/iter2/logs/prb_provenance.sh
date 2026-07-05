#!/bin/bash
# Provenance capture for the faithful PRB Yale hand (D9 + provenance ratchet):
# the mechanism proof, the self-distribution convergence (timestep + inertia-scale
# invariance + seed), and the FREE-BALL harness convergence — all to COMMITTED
# logs, not transient stdout. Reproducible.
cd /mnt/c/Users/Palash/Projects/robots/drone-catch/.claude/worktrees/grasp-iter2
L=docs/cage_frames/iter2/logs
source ~/miniconda3/etc/profile.d/conda.sh; conda activate robots
sc() { grep -v "pybullet build"; }

echo "########## D9 mechanism proof (pinned ball) ##########" | tee $L/prb_proof.out
python tests/yale_prb_proof.py --headless 2>&1 | sc | tee -a $L/prb_proof.out

echo "########## self-distribution convergence (D3) ##########" | tee $L/prb_convergence.txt
python tests/yale_prb_proof.py --converge 2>&1 | sc | tee -a $L/prb_convergence.txt

echo "########## FREE-BALL harness convergence (prb, 2.5cm-finger) ##########" | tee -a $L/prb_convergence.txt
python tests/cage_harness.py --converge --strategy prb --n 4 --offset 0.025 --dir finger 2>&1 | sc | tee -a $L/prb_convergence.txt
echo "########## FREE-BALL harness convergence (prb, 3.5cm-gap) ##########" | tee -a $L/prb_convergence.txt
python tests/cage_harness.py --converge --strategy prb --n 4 --offset 0.035 --dir gap 2>&1 | sc | tee -a $L/prb_convergence.txt

echo "PRB_PROVENANCE_DONE"
