#!/usr/bin/env bash
# §2.3 PAIRED-delta: does the faithful PRB hand re-center MORE than fixed, and
# how vs soft? Per-perturbation delta (same substep/contact/seed for both -> fair
# pairing). Earns 'A re-centers MORE than B' only if the delta stays >0.3 across
# ALL perturbations (task 7 stage 3). Same method as the committed soft paired.
set -u
cd "$(git rev-parse --show-toplevel)"
pair() {  # A B n offset dir
  echo "########## paired $1-$2 n=$3 off=$4 dir=$5 ##########"
  conda run --no-capture-output -n robots python -u tests/cage_harness.py --paired \
    --paired-a "$1" --paired-b "$2" --n "$3" --offset "$4" --dir "$5"
}
# prb vs fixed (does faithful-Yale re-center MORE than the rigid close?)
pair prb fixed 4 0.025 finger
pair prb fixed 4 0.035 finger
pair prb fixed 4 0.035 gap
pair prb fixed 6 0.025 finger
pair prb fixed 8 0.025 finger
# prb vs soft (how does faithful-Yale compare to the passive flexure?)
pair prb soft 4 0.025 finger
pair prb soft 4 0.035 finger
pair prb soft 4 0.035 gap
echo "PRB_PAIRED_DONE"
