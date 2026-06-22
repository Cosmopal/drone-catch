"""Phase 2 — full catch on the (level-holding) thrust-vectoring drone with the
WINNING close (the rigid fixed-pose close from the Phase-1 study) and a CONTROLLED
off-center seating bias, to test retention under cm-scale uncertainty.

Built on the validated scoop catch (tests/elbow_catch_solo.py): body stations
above the intercept, the 2-DOF arm IK-tracks the ball into the cup, the 4-finger
hand closes (the fixed-pose close, Phase-1 winner). Here the cup target is biased
by `--bias` cm along the body sagittal (x) axis so the ball seats OFF-CENTER in
the cup by a known amount — the dynamic analogue of the fixed-base offset study.

    python tests/cage_drone_catch.py --headless --tv --bias 0.0
    python tests/cage_drone_catch.py --headless --tv --table
"""
from __future__ import annotations
import argparse
import math
import os
import sys

import numpy as np
import pybullet as p

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sim_setup import (Logger, MarkerSet, Marker, VideoRecorder, Sim,
                       make_world, make_solo_drone, auto_run_paths, DT)
from config import DEFAULT as DEFAULT_GAME
from drone import ASSETS
from ball import spawn_ball, state as ball_state, predict_landing
import arm_kinematics as ak
from arm_catch_solo import (G, EE_INTERCEPT_X, EE_INTERCEPT_Z,
                            launch_state_for_intercept, CATCH_KP, CATCH_KD)

GRIPPER_URDF = os.path.join(ASSETS, "quadrotor_gripper.urdf")
TV_URDF = os.path.join(ASSETS, "quadrotor_tv_gripper.urdf")

STATION_H = 0.32
READY_TH1, READY_TH2 = 0.0, 0.9
TRACK_RANGE = 0.45
LEAD_S = 0.03
CUP_DEPTH = 0.045
CLOSE_DIST = 0.06
HOLD_DIST = 0.10
HOLD_REL_VEL = 0.6
SETTLE_S = 2.5
PAD_FRICTION = 1.4
BALL_RESTITUTION = 0.10
BALL_FRICTION = 1.4
BALL_VX, BALL_VZ = 3.3, -3.2


def run(tv=True, bias=0.0, ff=False, gui=False, runs_dir=None, verbose=True):
    log_path, video_path = auto_run_paths(runs_dir)
    make_world(DEFAULT_GAME, gui=gui)
    p.setPhysicsEngineParameter(numSolverIterations=150)

    intercept = np.array([EE_INTERCEPT_X, 0.0, EE_INTERCEPT_Z])
    catcher_home = np.array([EE_INTERCEPT_X, 0.0,
                             EE_INTERCEPT_Z + STATION_H - ak.SHOULDER_Z])
    catcher = make_solo_drone(tuple(catcher_home), play_extent=(4.0, 4.0, 1.2),
                              urdf_path=(TV_URDF if tv else GRIPPER_URDF),
                              thrust_vectoring=tv)
    catcher.set_target(catcher_home)
    catcher.controller.kp = CATCH_KP.copy()
    catcher.controller.kd = CATCH_KD.copy()
    catcher.finger_reaction_ff = ff
    if tv:
        catcher.attitude_mode = "level"
        catcher.beta_max = math.radians(60.0)
        catcher.arm_reaction_ff = True
    else:
        catcher.arm_reaction_ff = True
        catcher.attitude_gain_schedule = True
        catcher.arm_translational_ff_z = True
        catcher.controller.max_tilt_deg = 60.0
        catcher.controller.kI_pos = np.array([20.0, 20.0, 20.0])
        catcher.controller.kI = catcher.controller.kI.copy()
        catcher.controller.kI[2] = 0.3
    # bias the cup target along body sagittal +x so the ball seats off-center
    bias_v = np.array([bias, 0.0, 0.0])
    ee0 = intercept + np.array([0, 0, CUP_DEPTH]) - catcher_home
    sol0 = ak.ik(ee0[0] - ak.SHOULDER_X, ee0[2] - ak.SHOULDER_Z)
    catcher.hold_arm(*(sol0 if sol0 else (READY_TH1, READY_TH2)))
    if sol0:
        p.resetJointState(catcher.body_id, catcher.shoulder_joint, sol0[0])
        p.resetJointState(catcher.body_id, catcher.elbow_joint, sol0[1])
    catcher.open_gripper()
    catcher.set_finger_dynamics(lateral_friction=PAD_FRICTION,
                                restitution=BALL_RESTITUTION)

    markers = MarkerSet(); markers.intent.set(intercept.tolist())
    m_cup = Marker([1.0, 0.5, 0.1, 0.9], radius=0.03)
    logger = Logger(log_path, decimate=2)
    video = VideoRecorder(video_path, every=8, eye=(0.5, -3.0, 1.8),
                          target=(0.5, 0.0, 1.4), fov=70)
    sim = Sim([catcher], markers, logger, video, gui=gui)

    for _ in range(int(SETTLE_S / DT)):
        sim.tick("settle")

    launch_pos, launch_vel, t_flight = launch_state_for_intercept(
        intercept, (BALL_VX, 0.0, BALL_VZ))
    ball = spawn_ball(launch_pos)
    p.changeVisualShape(ball, -1, rgbaColor=[1.0, 0.3, 0.3, 1])
    p.changeDynamics(ball, -1, linearDamping=0.0, angularDamping=0.0,
                     restitution=BALL_RESTITUTION, lateralFriction=BALL_FRICTION)
    p.resetBaseVelocity(ball, linearVelocity=launch_vel.tolist())

    closing = captured = False
    result = {"tv": tv, "bias": bias, "ff": ff, "closed": False,
              "caught": False, "held": False, "max_tilt": 0.0,
              "min_cup_d": 1e9, "close_t": None, "max_fingers": 0}
    lift_started = None
    timeout_s = t_flight + 2.5

    def shoulder_world():
        bp = catcher.position()
        R = np.array(p.getMatrixFromQuaternion(catcher.orientation())).reshape(3, 3)
        return bp + R @ np.array([ak.SHOULDER_X, 0.0, ak.SHOULDER_Z])

    def cup_world():
        ee = catcher.gripper_world_position()
        th1, _, th2, _ = catcher.joint_states()
        R = np.array(p.getMatrixFromQuaternion(catcher.orientation())).reshape(3, 3)
        fdir = R @ np.array([math.sin(th1 - th2), 0.0, -math.cos(th1 - th2)])
        return ee + CUP_DEPTH * fdir, fdir

    def tilt_deg():
        R = np.array(p.getMatrixFromQuaternion(catcher.orientation())).reshape(3, 3)
        return math.degrees(math.acos(np.clip(R[2, 2], -1.0, 1.0)))

    for i in range(int(timeout_s / DT)):
        t = i * DT
        bp, bv = ball_state(ball)
        cup, fdir = cup_world()
        cup_d = float(np.linalg.norm(cup - bp))
        nf = catcher.fingers_touching(ball)
        result["max_fingers"] = max(result["max_fingers"], nf)
        result["min_cup_d"] = min(result["min_cup_d"], cup_d)
        if closing:
            result["max_tilt"] = max(result["max_tilt"], tilt_deg())
        if nf >= 3:
            captured = True
        sh = shoulder_world()
        ball_dist = float(np.linalg.norm(bp - sh))

        if captured:
            phase = "hold"
            if lift_started is None:
                lift_started = t; result["close_t"] = result["close_t"] or t
            elapsed = t - lift_started
            if elapsed > 1.0:
                phase = "lift"
                catcher.set_target(catcher_home + np.array([0, 0, min(0.2, (elapsed-1.0)*0.12)]),
                                   vel=(0, 0, 0))
            else:
                catcher.set_target(catcher.position(), vel=(0, 0, 0))
        else:
            pred_xy, _ = predict_landing(bp, bv, EE_INTERCEPT_Z)
            near = bv[2] < 0 and ball_dist < TRACK_RANGE
            if near:
                phase = "track"
                tgt_cup = bp + bv * LEAD_S + 0.5 * np.array([0, 0, -G]) * LEAD_S**2 + bias_v
                body_y = bp[1]
            elif pred_xy is not None:
                phase = "prepos"
                tgt_cup = np.array([pred_xy[0], pred_xy[1], EE_INTERCEPT_Z]) + bias_v
                body_y = pred_xy[1]
            else:
                phase = "prepos"; tgt_cup = intercept + bias_v; body_y = 0.0
            ee_tgt = tgt_cup - CUP_DEPTH * fdir
            R = np.array(p.getMatrixFromQuaternion(catcher.orientation())).reshape(3, 3)
            tgt_body = R.T @ (ee_tgt - catcher.position())
            rx, rz = tgt_body[0] - ak.SHOULDER_X, tgt_body[2] - ak.SHOULDER_Z
            r = math.hypot(rx, rz)
            if r > ak.REACH * 0.98:
                s = ak.REACH * 0.98 / r; rx, rz = rx * s, rz * s
            sol = ak.ik(rx, rz)
            if sol is not None:
                catcher.hold_arm(sol[0], sol[1])
            catcher.set_target([catcher_home[0], body_y, catcher_home[2]], vel=(0, 0, 0))
            m_cup.set(cup.tolist())
            if not closing and near and cup_d < CLOSE_DIST:
                catcher.close_gripper()    # WINNER: rigid fixed-pose close
                closing = True; result["closed"] = True

        sim.tick(phase, extra_payload={"cup_to_ball": cup_d, "fingers": nf})
        if captured and result["close_t"] is not None and t - result["close_t"] > 1.6:
            break
        if not captured and bp[2] < 0.05:
            break
        if closing and not captured and bp[2] < EE_INTERCEPT_Z - 0.4:
            break

    bp, bv = ball_state(ball)
    ee_v = catcher.gripper_world_velocity()
    cup, _ = cup_world()
    end_d = float(np.linalg.norm(cup - bp))
    end_rel = float(np.linalg.norm(bv - ee_v))
    nf = catcher.fingers_touching(ball)
    result["caught"] = bool(captured and end_d < HOLD_DIST and nf >= 2)
    result["held"] = bool(result["caught"] and end_rel < HOLD_REL_VEL)
    sim.logger.close(); sim.video.close()
    if verbose:
        print(f"[{'TV' if tv else 'UND'} bias={bias*100:.1f}cm ff={int(ff)}] "
              f"closed={result['closed']} caught={result['caught']} "
              f"held={result['held']} min_cup={result['min_cup_d']*100:.1f}cm "
              f"maxF={result['max_fingers']} close-tilt={result['max_tilt']:.1f}deg")
    return result


def table(tv=True):
    print(f"=== full catch on {'TV' if tv else 'underactuated'} drone, "
          f"winning fixed-pose close, vs seating bias ===")
    rows = [run(tv=tv, bias=b, verbose=True) for b in (0.0, 0.015, 0.025)]
    held = sum(r["held"] for r in rows)
    print(f"\nheld {held}/{len(rows)}; max close-tilt "
          f"{max(r['max_tilt'] for r in rows):.1f}deg "
          f"(<5deg gate: {'PASS' if max(r['max_tilt'] for r in rows) < 5 else 'FAIL'})")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--tv", action="store_true")
    ap.add_argument("--ff", action="store_true")
    ap.add_argument("--bias", type=float, default=0.0)
    ap.add_argument("--table", action="store_true")
    ap.add_argument("--runs-dir", default=None)
    args = ap.parse_args()
    if args.table:
        return table(tv=args.tv)
    r = run(tv=args.tv, bias=args.bias, ff=args.ff, gui=not args.headless,
            runs_dir=args.runs_dir)
    return 0 if r["held"] else 1


if __name__ == "__main__":
    sys.exit(main())
