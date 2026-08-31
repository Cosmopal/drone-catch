import sys, os, argparse
sys.path.insert(0, r"C:\Users\Palash\Projects\robots\drone-catch\.claude\worktrees\grasp-iter2\src")
sys.path.insert(0, r"C:\Users\Palash\Projects\robots\drone-catch\.claude\worktrees\grasp-iter2\tests")
sys.path.insert(0, r"C:\Users\Palash\AppData\Local\Temp\claude\C--Users-Palash-Projects-robots-drone-catch\8e8d835f-e319-4d4e-90a5-892f4b3f5715\scratchpad")
import pybullet as p
import elbow_ablate as ec

ap = argparse.ArgumentParser()
ap.add_argument("--label", required=True)
ap.add_argument("--runs-dir", default=None)
ap.add_argument("--inert-query", default=None)
ap.add_argument("--force-log-only", action="store_true")
ap.add_argument("--force-video-only", action="store_true")
ap.add_argument("--solver-iters", type=int, default=150)
ap.add_argument("--log-decimate", type=int, default=2)
ap.add_argument("--vx", type=float, default=ec.BALL_VX_DEFAULT)
ap.add_argument("--vz", type=float, default=ec.BALL_VZ_DEFAULT)
ap.add_argument("--vx-eps", type=float, default=0.0)
args = ap.parse_args()

p.connect(p.DIRECT)
try:
    r = ec.run(gui=False, runs_dir=args.runs_dir, ball_vx=args.vx + args.vx_eps,
               ball_vz=args.vz, verbose=False,
               inert_query=args.inert_query,
               force_log_only=args.force_log_only,
               force_video_only=args.force_video_only,
               solver_iters=args.solver_iters,
               log_decimate=args.log_decimate)
finally:
    p.disconnect()

print(f"LABEL={args.label} closed={r['closed']} captured={r['captured']} "
      f"caught={r['caught']} held={r['held']} min_cup_d={r['min_cup_d']*100:.2f}cm "
      f"end_d={r['end_d']*100:.2f}cm end_fingers={r['end_fingers']} max_fingers={r['max_fingers']}")
