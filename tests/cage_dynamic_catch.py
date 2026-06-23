"""DYNAMIC catch — the FAIR test of the Yale underactuated hand vs the rigid close.

The static fixed-base harness (cage_harness) is gravity-OFF, so an aggressive
adaptive under-tuck EJECTS a free off-center ball upward (nothing seats it) — it
is biased against underactuation. The fair test (flagged in §26) is the DYNAMIC
catch: the ball arrives with downward momentum that SEATS it into the cup while
the hand closes around it.

To get the validated catch DYNAMICS exactly, this reuses the committed scoop
catch `tests/elbow_catch_solo.py` unchanged and only swaps the CLOSE:
  --close fixed : the rigid position close (`Drone.close_gripper`, the baseline).
  --close yale  : the faithful underactuated hand (`src/yale_hand.py`), injected
                  at the close trigger via the additive `Drone.external_gripper`
                  hook (monkeypatched onto the catcher; the elbow test itself is
                  untouched).
Off-center seating arises NATURALLY from the imperfect tracking, and grows at
off-nominal ball velocities (the velocity grid), so comparing held-rate across
the grid IS the off-center-retention comparison.

    python tests/cage_dynamic_catch.py --headless --close yale
    python tests/cage_dynamic_catch.py --headless --table
"""
from __future__ import annotations
import argparse
import os
import sys

import pybullet as p

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from drone import Drone
import yale_hand
import elbow_catch_solo as ecs

# Yale close tuned to RETAIN the dynamic catch. NOTE: it needs a FIRMER tendon
# tension (soft_force 0.7) than the rigid close (0.5) to hold the ball through the
# lift — a gentle compliant close captures but the ball works loose. So the
# underactuated hand MATCHES the rigid close here, it does not beat it, and it
# needs MORE grip force + more tuning to do so.
YALE_RAMP_TICKS = 50       # ~0.21 s actuator ramp once closing
YALE_FORCE = 0.7
YALE_DMAX = 4.0


class YaleCloser:
    """External-gripper controller: ramps the underactuated hand's one actuator
    and drives src/yale_hand each drone step. Reads live contact with `ball`."""
    def __init__(self, ball, cfg):
        self.ball, self.cfg, self.n = ball, cfg, 0

    def __call__(self, drone):
        prog = min(1.0, self.n / (YALE_RAMP_TICKS * 0.6))
        yale_hand.actuate(drone.body_id, drone.finger_joints, self.ball,
                          prog * self.cfg.d_max, self.cfg)
        self.n += 1


_BALL = {}
_orig_spawn = ecs.spawn_ball


def _spy_spawn(*a, **k):
    b = _orig_spawn(*a, **k)
    _BALL["id"] = b
    return b


def run(close="fixed", ball_vx=ecs.BALL_VX_DEFAULT, ball_vz=ecs.BALL_VZ_DEFAULT,
        gui=False, runs_dir=None, verbose=True):
    """Run the validated elbow scoop with the chosen close. Owns the connection."""
    p.connect(p.GUI if gui else p.DIRECT)
    patched = False
    try:
        if close == "yale":
            ecs.spawn_ball = _spy_spawn
            orig_close = Drone.close_gripper

            def yale_close(self, compliant=False):
                cfg = yale_hand.YaleConfig(soft_force=YALE_FORCE, d_max=YALE_DMAX)
                self.external_gripper = YaleCloser(_BALL["id"], cfg)

            Drone.close_gripper = yale_close
            patched = True
        r = ecs.run(gui=gui, runs_dir=runs_dir, ball_vx=ball_vx, ball_vz=ball_vz,
                    verbose=verbose)
    finally:
        if patched:
            Drone.close_gripper = orig_close
            ecs.spawn_ball = _orig_spawn
        p.disconnect()
    if verbose:
        print(f"  -> close={close} caught={r['caught']} held={r['held']} "
              f"min_cup={r['min_cup_d']*100:.1f}cm maxF={r['max_fingers']}")
    return r


def table():
    cells = [(2.5, -3.2), (3.3, -2.0), (3.3, -3.2), (3.3, -4.5), (4.5, -3.2)]
    print("=== dynamic scoop catch: rigid close vs Yale underactuated hand ===")
    print("(held? across the ball-velocity grid; off-nominal => more off-center seating)")
    res = {}
    for close in ("fixed", "yale"):
        res[close] = [run(close=close, ball_vx=vx, ball_vz=vz, verbose=False)
                      for vx, vz in cells]
    print(f"\n{'vx,vz':>10} | " + " ".join(f"{vx:.1f},{vz:+.1f}" for vx, vz in cells))
    for close in ("fixed", "yale"):
        print(f"{close:>10} | " + " ".join(
            f"{'HELD ' if r['held'] else ('caught' if r['caught'] else '  -  '):>8}"
            for r in res[close]))
    for close in ("fixed", "yale"):
        held = sum(r["held"] for r in res[close])
        print(f"  {close}: held {held}/{len(cells)}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--close", default="fixed", choices=["fixed", "yale"])
    ap.add_argument("--vx", type=float, default=ecs.BALL_VX_DEFAULT)
    ap.add_argument("--vz", type=float, default=ecs.BALL_VZ_DEFAULT)
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--runs-dir", default=None)
    args = ap.parse_args()
    if args.table:
        return table()
    r = run(close=args.close, ball_vx=args.vx, ball_vz=args.vz,
            gui=not args.headless, runs_dir=args.runs_dir)
    return 0 if r["held"] else 1


if __name__ == "__main__":
    sys.exit(main())
