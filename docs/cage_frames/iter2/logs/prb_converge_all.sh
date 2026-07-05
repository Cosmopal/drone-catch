#!/usr/bin/env bash
# §2.3 convergence tables for the faithful PRB hand across every contact-rich
# verdict-bearing cell (task 7 stage 2). Each cell varies substep {2,4,8},
# contact model {x0.33,x3}, seed {1,2,3}; prints EM/PI/RT/CF/SY + a CONVERGED
# verdict + a pull-in SIGN verdict. Unbuffered so the committed log fills
# incrementally (shutdown-safety).
set -u
cd "$(git rev-parse --show-toplevel)"
run() {  # strat n offset dir
  echo "########## converge $1 n=$2 off=$3 dir=$4 ##########"
  conda run --no-capture-output -n robots python -u tests/cage_harness.py --converge \
    --strategy "$1" --n "$2" --offset "$3" --dir "$4"
}
run prb 4 0.015 finger
run prb 4 0.025 finger
run prb 4 0.035 finger
run prb 4 0.025 gap
run prb 4 0.035 gap
run prb 6 0.025 finger
run prb 8 0.025 finger
echo "PRB_CONVERGE_ALL_DONE"
