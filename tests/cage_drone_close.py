"""Phase 2 — finger-close reaction on a FLOATING base, and the finger-reaction
feedforward (the user's hypothesis from CLAUDE.md parking-lot / §24).

§24 found that the active constant-torque ("tendon") close FLIPPED the
underactuated drone (~90 deg pitch): the sustained finger-joint motor torques
react on the airframe (Newton's third law) and a constant-torque tendon never
stops applying them. The hypothesis tested here: a FINGER-REACTION FEEDFORWARD
(predict the net body torque from the commanded finger torques, pre-cancel it on
the body — exactly as arm_reaction_ff does for the arm sweep) lets the close run
without upsetting attitude.

This test hovers a gripper drone (underactuated OR thrust-vectoring) in the
catch pose (arm straight down) and fires a close, measuring the body's max tilt
and pitch during the close window. `--ff` toggles `finger_reaction_ff`;
`--strategy {fixed,tendon}` selects the rigid position close (the Phase-1
winner) or the constant-torque close (the §24 flipper).

    python tests/cage_drone_close.py --headless --strategy tendon            # underactuated, no FF
    python tests/cage_drone_close.py --headless --strategy tendon --ff       # + finger-reaction FF
    python tests/cage_drone_close.py --headless --strategy tendon --tv       # TV drone
    python tests/cage_drone_close.py --headless --table                      # full comparison table
"""
from __future__ import annotations
import argparse
import math
import os
import sys

import numpy as np
import pybullet as p

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import DEFAULT as DEFAULT_GAME
from world import setup as world_setup
from drone import ASSETS, G
from sim_setup import make_solo_drone
from ball import spawn_ball

DT = 1.0 / 240.0
GRIPPER_URDF = os.path.join(ASSETS, "quadrotor_gripper.urdf")
TV_URDF = os.path.join(ASSETS, "quadrotor_tv_gripper.urdf")
HOME = np.array([0.0, 0.0, 1.5])
CATCH_KP = np.array([12.0, 12.0, 14.0])
CATCH_KD = np.array([7.0, 7.0, 7.0])


def build(tv, ff):
    d = make_solo_drone(tuple(HOME), play_extent=(4.0, 4.0, 1.4),
                        urdf_path=(TV_URDF if tv else GRIPPER_URDF),
                        thrust_vectoring=tv)
    d.set_target(HOME)
    d.controller.kp = CATCH_KP.copy()
    d.controller.kd = CATCH_KD.copy()
    if tv:
        d.attitude_mode = "level"
        d.beta_max = math.radians(60.0)
        d.arm_reaction_ff = True
    else:
        # strongest underactuated baseline: full compensation stack.
        d.arm_reaction_ff = True
        d.attitude_gain_schedule = True
        d.arm_translational_ff_z = True
        d.controller.max_tilt_deg = 60.0
        d.controller.kI_pos = np.array([20.0, 20.0, 20.0])
        d.controller.kI = d.controller.kI.copy()
        d.controller.kI[2] = 0.3
    d.finger_reaction_ff = ff
    # arm straight down (cup below the body); reset to avoid the init snap
    p.resetJointState(d.body_id, d.shoulder_joint, 0.0)
    p.resetJointState(d.body_id, d.elbow_joint, 0.0)
    d.hold_arm(0.0, 0.0)
    d.open_gripper()
    d.set_finger_dynamics(lateral_friction=1.4, restitution=0.1)
    return d


def tilt_deg(d):
    R = np.array(p.getMatrixFromQuaternion(d.orientation())).reshape(3, 3)
    return math.degrees(math.acos(np.clip(R[2, 2], -1.0, 1.0)))


def run(tv=False, ff=False, strategy="tendon", with_ball=True, gui=False,
        verbose=True):
    p.connect(p.GUI if gui else p.DIRECT)
    try:
        world_setup(gui=gui, room_size=DEFAULT_GAME.room_size,
                    wall_height=DEFAULT_GAME.wall_height)
        p.setPhysicsEngineParameter(numSolverIterations=150)
        d = build(tv, ff)
        # settle hovering in the catch pose
        for _ in range(int(2.0 / DT)):
            d.step(); p.stepSimulation()
        settle_tilt = tilt_deg(d)
        settle_z = d.position()[2]

        ball = None
        if with_ball:
            # a ball resting in the cup, lightly tethered so the close has
            # something to react against through the whole window (isolates the
            # finger-motor reaction; a free ball would fall away in ~0.1 s).
            cup = d.gripper_world_position() + np.array([0, 0, -0.045])
            ball = spawn_ball(cup)
            p.changeDynamics(ball, -1, mass=0.065, restitution=0.1,
                             lateralFriction=1.4)
            d.soft_grasp(ball, max_distance=0.12, max_force=3.0)

        # fire the close
        d.close_gripper(compliant=(strategy == "tendon"))

        max_tilt = settle_tilt
        max_z_err = 0.0
        for _ in range(int(1.2 / DT)):
            d.step(); p.stepSimulation()
            max_tilt = max(max_tilt, tilt_deg(d))
            max_z_err = max(max_z_err, abs(d.position()[2] - HOME[2]))
        end_tilt = tilt_deg(d)
        res = {"tv": tv, "ff": ff, "strategy": strategy, "with_ball": with_ball,
               "settle_tilt": settle_tilt, "max_tilt": max_tilt,
               "end_tilt": end_tilt, "max_z_err": max_z_err,
               "flipped": max_tilt > 45.0, "ok": max_tilt < 5.0}
        if verbose:
            print(f"[{'TV ' if tv else 'UND'} {strategy:6s} ff={int(ff)} "
                  f"ball={int(with_ball)}] settle_tilt={settle_tilt:.2f}deg "
                  f"max_tilt={max_tilt:.2f}deg end={end_tilt:.2f}deg "
                  f"max_z_err={max_z_err*100:.1f}cm "
                  f"{'FLIP' if res['flipped'] else ('OK<5deg' if res['ok'] else 'disturbed')}")
        return res
    finally:
        p.disconnect()


def table():
    print("=== finger-close body reaction: max body tilt during the close ===")
    rows = []
    for tv in (False, True):
        for strategy in ("fixed", "tendon"):
            for ff in (False, True):
                rows.append(run(tv=tv, ff=ff, strategy=strategy, with_ball=True,
                                verbose=True))
    # headline: the tendon close with/without FF
    print("\n--- headline (constant-torque 'tendon' close, the §24 flipper) ---")
    for tv in (False, True):
        off = next(r for r in rows if r["tv"] == tv and r["strategy"] == "tendon"
                   and not r["ff"])
        on = next(r for r in rows if r["tv"] == tv and r["strategy"] == "tendon"
                  and r["ff"])
        tag = "TV " if tv else "UND"
        print(f"  {tag}: tendon close  no-FF max_tilt={off['max_tilt']:5.1f}deg "
              f"-> FF max_tilt={on['max_tilt']:5.1f}deg")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--tv", action="store_true")
    ap.add_argument("--ff", action="store_true")
    ap.add_argument("--strategy", default="tendon", choices=["fixed", "tendon"])
    ap.add_argument("--no-ball", action="store_true")
    ap.add_argument("--table", action="store_true")
    args = ap.parse_args()
    if args.table:
        return table()
    r = run(tv=args.tv, ff=args.ff, strategy=args.strategy,
            with_ball=not args.no_ball, gui=not args.headless)
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
