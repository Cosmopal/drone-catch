"""M-A task 1/2 (critic follow-up): regenerate the static-harness solver-
iterations sweep from committed code. Mirrors cage_fk_driver.py's pattern
-- sets a module global on cage_harness_ablate before calling run_cell."""
import sys, argparse
sys.path.insert(0, r"C:\Users\Palash\Projects\robots\drone-catch\.claude\worktrees\grasp-iter2\tests")
sys.path.insert(0, r"C:\Users\Palash\Projects\robots\drone-catch\.claude\worktrees\grasp-iter2\src")
sys.path.insert(0, r"C:\Users\Palash\Projects\robots\drone-catch\.claude\worktrees\grasp-iter2\assets")
import cage_harness_ablate as ch

ap = argparse.ArgumentParser()
ap.add_argument("--label", required=True)
ap.add_argument("--offset", type=float, required=True)
ap.add_argument("--dir", required=True)
ap.add_argument("--n", type=int, default=4)
ap.add_argument("--strategy", default="prb")
ap.add_argument("--solver-iters", type=int, default=150)
args = ap.parse_args()

ch.SOLVER_ITERS = args.solver_iters
r = ch.run_cell(args.strategy, args.n, args.offset, args.dir, quality=True, verbose=False)
print(f"LABEL={args.label} solver_iters={args.solver_iters} score={r['score']:.2f} "
      f"EM={r['escape_margin_g']:.2f}g PI={r['pull_in']*100:+.2f}cm CF={r['n_contact_fingers']} "
      f"SY={r['symmetry']:.2f} seat_off={r['seat_off']*100:.2f}cm seated_nf={r['seated_nf']}")
