"""M-A task 3 (critic follow-up): regenerate the finger-torque-vs-cap log
from committed code. Mirrors driver.py's pattern."""
import sys, argparse
sys.path.insert(0, r"C:\Users\Palash\Projects\robots\drone-catch\.claude\worktrees\grasp-iter2\src")
sys.path.insert(0, r"C:\Users\Palash\Projects\robots\drone-catch\.claude\worktrees\grasp-iter2\tests")
import pybullet as p
import elbow_ablate as ec

ap = argparse.ArgumentParser()
ap.add_argument("--label", required=True)
ap.add_argument("--t0", type=float, required=True, help="torque-log window start (Sim.t)")
ap.add_argument("--t1", type=float, required=True, help="torque-log window end (Sim.t)")
ap.add_argument("--trace-out", required=True)
ap.add_argument("--solver-iters", type=int, default=150)
ap.add_argument("--vx", type=float, default=ec.BALL_VX_DEFAULT)
ap.add_argument("--vz", type=float, default=ec.BALL_VZ_DEFAULT)
args = ap.parse_args()

p.connect(p.DIRECT)
try:
    r = ec.run(gui=False, runs_dir=None, ball_vx=args.vx, ball_vz=args.vz,
              verbose=True, solver_iters=args.solver_iters,
              torque_log_window=(args.t0, args.t1), trace_out=args.trace_out)
finally:
    p.disconnect()

print(f"LABEL={args.label} closed={r['closed']} captured={r['captured']} "
      f"caught={r['caught']} held={r['held']} min_cup_d={r['min_cup_d']*100:.2f}cm")
