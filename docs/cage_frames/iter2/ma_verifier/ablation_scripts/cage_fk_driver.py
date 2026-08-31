import sys, argparse
sys.path.insert(0, r"C:\Users\Palash\Projects\robots\drone-catch\.claude\worktrees\grasp-iter2\tests")
sys.path.insert(0, r"C:\Users\Palash\Projects\robots\drone-catch\.claude\worktrees\grasp-iter2\src")
sys.path.insert(0, r"C:\Users\Palash\Projects\robots\drone-catch\.claude\worktrees\grasp-iter2\assets")
sys.path.insert(0, r"C:\Users\Palash\AppData\Local\Temp\claude\C--Users-Palash-Projects-robots-drone-catch\8e8d835f-e319-4d4e-90a5-892f4b3f5715\scratchpad")
import cage_harness_ablate as ch

ap = argparse.ArgumentParser()
ap.add_argument("--label", required=True)
ap.add_argument("--offset", type=float, required=True)
ap.add_argument("--dir", required=True)
ap.add_argument("--n", type=int, default=4)
ap.add_argument("--strategy", default="prb")
ap.add_argument("--fk-ablate", action="store_true")
args = ap.parse_args()

ch.FK_ABLATE = args.fk_ablate
r = ch.run_cell(args.strategy, args.n, args.offset, args.dir, quality=True, verbose=False)
print(f"LABEL={args.label} fk_ablate={args.fk_ablate} score={r['score']:.2f} "
      f"EM={r['escape_margin_g']:.2f}g PI={r['pull_in']*100:+.2f}cm CF={r['n_contact_fingers']} "
      f"SY={r['symmetry']:.2f} seat_off={r['seat_off']*100:.2f}cm seated_nf={r['seated_nf']}")
