#!/bin/bash
# Re-render every frame cited in §28 so the HUD shows one-decimal offsets
# (reviewer minor 3), and capture migration stdout to a COMMITTED log this time
# (reviewer concern 1 provenance). Canonical output = this stdout.
cd /mnt/c/Users/Palash/Projects/robots/drone-catch/.claude/worktrees/grasp-iter2
source ~/miniconda3/etc/profile.d/conda.sh; conda activate robots
O=docs/cage_frames/iter2
qf() { python tests/cage_harness.py --quality-frames "$@" --no-video 2>&1 | grep -E "escape-margin|weakest"; }

echo "===== quality-frame re-renders (one-decimal HUD) ====="
qf --strategy soft  --n 4 --offset 0.025 --dir finger --out $O
qf --strategy fixed --n 4 --offset 0.025 --dir finger --out $O
qf --strategy fixed --n 4 --offset 0.0   --dir finger --out $O
qf --strategy fixed --n 4 --offset 0.035 --dir gap    --out $O
qf --strategy fixed --n 4 --offset 0.045 --dir gap    --out $O
qf --strategy yale  --n 4 --offset 0.025 --dir finger --out $O
echo "===== boundary substep-flip pair ====="
python tests/cage_harness.py --quality-frames --strategy fixed --n 4 --offset 0.040 --dir gap --substep 2 --out $O/boundary_ss2 --no-video 2>&1 | grep -E "escape-margin"
python tests/cage_harness.py --quality-frames --strategy fixed --n 4 --offset 0.040 --dir gap --substep 8 --out $O/boundary_ss8 --no-video 2>&1 | grep -E "escape-margin"
echo "===== migration re-renders (committed stdout) ====="
python tests/cage_harness.py --migration --n 4 --offset 0.025 --dir finger --out $O 2>&1 | grep -E "CAUSAL|CE:|DENSE|fixed:|soft:"
python tests/cage_harness.py --migration --n 4 --offset 0.025 --dir gap    --out $O 2>&1 | grep -E "CAUSAL|CE:|DENSE|fixed:|soft:"
echo "RERENDER_DONE"
