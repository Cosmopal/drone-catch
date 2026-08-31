"""2-DOF (shoulder + elbow) tracking catch — M7.

The 1-DOF sweep (arm_catch_solo / finger_catch_solo) had to land a swept arc
ON the ball at one instant — a knife-edge that left the finger catch ~7-10 cm
short. With the elbow unlocked, the end-effector has 2 planar DOF: instead of
sweeping through the ball, the arm SERVOS the cup onto the ball's predicted
position and TRACKS it for a window. Body stations above the intercept so the
arm hangs into the ball's path; IK (src/arm_kinematics.py) maps the desired
cup position to (shoulder, elbow) every tick.

Catch: fingers close when the ball is in the cup; capture = ≥2 fingers
touching (caging + friction, no constraint — same as finger_catch_solo).

Usage:
    python tests/elbow_catch_solo.py --headless --runs-dir runs/elbow
    python tests/elbow_catch_solo.py --headless --grid
    python tests/elbow_catch_solo.py --headless --vx 4.5 --vz -3.2
"""
from __future__ import annotations
import argparse
import sys
import os
import math
import dataclasses
import numpy as np
import pybullet as p

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sim_setup import (Logger, MarkerSet, Marker, VideoRecorder, Sim,
                       make_world, make_solo_drone, auto_run_paths,
                       rotate_runs, DT)
from config import DEFAULT as DEFAULT_GAME
from drone import ASSETS
from ball import spawn_ball, state as ball_state, predict_landing
from perception import BallPerception, BallEstimator
import arm_kinematics as ak
from arm_catch_solo import (G, EE_INTERCEPT_X, EE_INTERCEPT_Z,
                            launch_state_for_intercept, CATCH_KP, CATCH_KD)

GRIPPER_URDF = os.path.join(ASSETS, "quadrotor_gripper.urdf")

BALL_VX_DEFAULT = 3.3
BALL_VZ_DEFAULT = -3.2

STATION_H = 0.32        # shoulder height above the intercept (arm hangs down)
READY_TH1, READY_TH2 = 0.0, 0.9   # ready pose while waiting (mid-elbow)
TRACK_RANGE = 0.45      # start IK-tracking when ball within this of shoulder
LEAD_S = 0.03           # aim where the ball will be this far ahead
CUP_DEPTH = 0.045       # enclosure center beyond the EE link (4-finger,
                        # 3-segment caging hand wraps a ball ~4.5 cm out)
CLOSE_DIST = 0.06       # close fingers when cup-to-ball within this
BALL_RESTITUTION = 0.10
BALL_FRICTION = 1.4
PAD_FRICTION = 1.4
HOLD_DIST = 0.10
HOLD_REL_VEL = 0.6
SETTLE_S = 2.5


def run(gui, runs_dir, ball_vx=BALL_VX_DEFAULT, ball_vz=BALL_VZ_DEFAULT,
        noise=False, seed=0, verbose=True):
    log_path, video_path = auto_run_paths(runs_dir)
    make_world(DEFAULT_GAME, gui=gui)
    # The caging gripper adds 12 finger joints; the default solver iteration
    # count can't hold that many PD joints on a floating base (body diverges
    # ~80 cm). Bumping iterations fixes it (local to this test so it doesn't
    # perturb the constraint-based arm_catch_solo). See iteration_findings §15.
    p.setPhysicsEngineParameter(numSolverIterations=150)

    intercept = np.array([EE_INTERCEPT_X, 0.0, EE_INTERCEPT_Z])
    # Body so the shoulder sits STATION_H above the intercept.
    catcher_home = np.array([EE_INTERCEPT_X, 0.0,
                             EE_INTERCEPT_Z + STATION_H - ak.SHOULDER_Z])

    catcher = make_solo_drone(tuple(catcher_home), play_extent=(4.0, 4.0, 1.2),
                              urdf_path=GRIPPER_URDF)
    catcher.set_target(catcher_home)
    catcher.arm_reaction_ff = True
    catcher.attitude_gain_schedule = True
    catcher.arm_translational_ff_z = True
    catcher.controller.max_tilt_deg = 60.0
    catcher.controller.kp = CATCH_KP.copy()
    catcher.controller.kd = CATCH_KD.copy()
    catcher.controller.kI_pos = np.array([20.0, 20.0, 20.0])
    catcher.controller.kI = catcher.controller.kI.copy()
    catcher.controller.kI[2] = 0.3
    # Pre-position the arm so the cup sits at the nominal intercept from the
    # start (cup is CUP_DEPTH below the EE; arm hangs ~straight down). Holding
    # here through settle means no last-moment slew when the ball arrives.
    ee0 = intercept + np.array([0, 0, CUP_DEPTH]) - catcher_home  # EE target, body frame (arm down)
    sol0 = ak.ik(ee0[0] - ak.SHOULDER_X, ee0[2] - ak.SHOULDER_Z)
    catcher.hold_arm(*(sol0 if sol0 else (READY_TH1, READY_TH2)))
    catcher.open_gripper()
    catcher.set_finger_dynamics(lateral_friction=PAD_FRICTION,
                                restitution=BALL_RESTITUTION)

    markers = MarkerSet()
    markers.intent.set(intercept.tolist())   # cyan: TRUE intercept
    m_cup = Marker([1.0, 0.5, 0.1, 0.9], radius=0.03)
    # YELLOW: the catcher's ESTIMATED landing point (predict_landing on the
    # filtered estimate). Under noise it jitters early and converges as the
    # alpha-beta filter sharpens — the gap to the cyan truth marker IS the
    # estimation error the catch has to absorb.
    m_est = Marker([1.0, 0.95, 0.1, 0.95], radius=0.045)
    logger = Logger(log_path, decimate=2)
    video = VideoRecorder(video_path, every=8, eye=(0.5, -3.0, 1.8),
                          target=(0.5, 0.0, 1.4), fov=70)
    sim = Sim([catcher], markers, logger, video, gui=gui)

    for _ in range(int(SETTLE_S / DT)):
        sim.tick("settle")

    launch_pos, launch_vel, t_flight = launch_state_for_intercept(
        intercept, (ball_vx, 0.0, ball_vz))
    if verbose:
        print(f"intercept={intercept.tolist()} station_H={STATION_H} "
              f"t_flight={t_flight:.3f}s")
    ball = spawn_ball(launch_pos)
    # Bright green — distinct from the red/orange/magenta MarkerSet palette
    # (target [1,.2,.2], actual [1,.5,0], intent [1,.2,.8]) and the orange
    # m_cup / yellow m_est markers below. The old near-red [1,.3,.3] was
    # visually indistinguishable from the target marker at render scale
    # (M-A reviewer finding: legibility bug, blocked finger-state frame review).
    p.changeVisualShape(ball, -1, rgbaColor=[0.15, 0.85, 0.25, 1])
    p.changeDynamics(ball, -1, linearDamping=0.0, angularDamping=0.0,
                     restitution=BALL_RESTITUTION, lateralFriction=BALL_FRICTION)
    p.resetBaseVelocity(ball, linearVelocity=launch_vel.tolist())

    # Perception: catcher decides on the latency-compensated ESTIMATE, not
    # truth, when noise is on. Truth is only used for physics + scoring.
    perception = BallPerception(ball, seed=seed) if noise else None
    estimator = BallEstimator(latency_s=12 * DT, dt=DT) if noise else None

    closing = False
    captured = False
    result = {"vx": ball_vx, "vz": ball_vz, "speed": math.hypot(ball_vx, ball_vz),
              "closed": False, "caught": False, "held": False,
              "close_t": None, "close_rel": None, "max_fingers": 0,
              "min_cup_d": 1e9, "_dbg": None}
    trace = []
    timeout_s = t_flight + 2.5
    lift_started = None

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

    for i in range(int(timeout_s / DT)):
        t = i * DT
        bp, bv = ball_state(ball)          # truth: physics + scoring
        if noise:
            perception.step_record()
            mp, mv = perception.observe(catcher.position())
            estimator.update(mp, mv)
            est_p, est_v = estimator.estimate()
        else:
            est_p, est_v = bp, bv
        ee = catcher.gripper_world_position()
        ee_v = catcher.gripper_world_velocity()
        cup, fdir = cup_world()
        cup_d = float(np.linalg.norm(cup - bp))
        rel = float(np.linalg.norm(bv - ee_v))
        nf = catcher.fingers_touching(ball)
        result["max_fingers"] = max(result["max_fingers"], nf)
        if cup_d < result["min_cup_d"]:
            result["min_cup_d"] = cup_d
            result["_dbg"] = (f"cup={np.round(cup,3).tolist()} "
                              f"ball={np.round(bp,3).tolist()} "
                              f"th=({math.degrees(catcher.joint_states()[0]):.0f},"
                              f"{math.degrees(catcher.joint_states()[2]):.0f})deg")

        if nf >= 3:
            captured = True   # ≥3 wrapping fingers = a real cage (not a rim brush)

        sh = shoulder_world()
        ball_dist = float(np.linalg.norm(bp - sh))

        if captured:
            phase = "hold"
            if lift_started is None:
                lift_started = t
                result["close_t"] = result["close_t"] or t
            elapsed = t - lift_started
            # The form-closure cage already retains the ball with the gentle
            # close torque — do NOT firm the grip (over-squeezing a rigid ball
            # produces 100+ N contacts that eject it). Hold position to let the
            # ball settle, then lift VERY gently to prove retention.
            if elapsed > 1.0:
                phase = "lift"
                catcher.set_target(catcher_home + np.array([0, 0, min(0.2, (elapsed-1.0)*0.12)]),
                                   vel=(0, 0, 0))
            else:
                catcher.set_target(catcher.position(), vel=(0, 0, 0))
        else:
            # --- Pre-position, then track the descending ball (slew-limited) ---
            # Far: hold the cup at the predicted landing point (intercept
            # plane). Near: track the ball's actual 3-D position so the cup
            # descends WITH it (an aligned approach — a stationary cup lets the
            # ball graze the open fingers and deflect). The transition would
            # snap the arm UP to the high ball; a per-tick joint SLEW LIMIT
            # spreads that into a smooth fast move. See §16–17.
            pred_xy, _ = predict_landing(est_p, est_v, EE_INTERCEPT_Z)
            if pred_xy is not None:
                m_est.set([pred_xy[0], pred_xy[1], EE_INTERCEPT_Z])  # estimated landing
            near = est_v[2] < 0 and ball_dist < TRACK_RANGE
            if near:
                phase = "track"
                # Track the ball's actual 3-D position: the cup rises to MEET
                # the ball and descends WITH it, presenting the cup mouth so the
                # ball enters cleanly (a stationary cup lets the ball fall onto
                # the splayed finger tips and deflect). The rise is the "snap"
                # the user sees — it's how this gripper receives the ball; a
                # truly smooth version needs velocity-matched tracking from
                # apex (open problem, §17).
                tgt_cup = est_p + est_v * LEAD_S + 0.5 * np.array([0, 0, -G]) * LEAD_S**2
                body_y = est_p[1]
            elif pred_xy is not None:
                phase = "prepos"
                tgt_cup = np.array([pred_xy[0], pred_xy[1], EE_INTERCEPT_Z])
                body_y = pred_xy[1]
            else:
                phase = "prepos"
                tgt_cup = intercept
                body_y = 0.0
            ee_tgt = tgt_cup - CUP_DEPTH * fdir
            R = np.array(p.getMatrixFromQuaternion(catcher.orientation())).reshape(3, 3)
            tgt_body = R.T @ (ee_tgt - catcher.position())   # EE target, body frame
            rx, rz = tgt_body[0] - ak.SHOULDER_X, tgt_body[2] - ak.SHOULDER_Z
            r = math.hypot(rx, rz)
            if r > ak.REACH * 0.98:
                s = ak.REACH * 0.98 / r
                rx, rz = rx * s, rz * s
            sol = ak.ik(rx, rz)
            if sol is not None:
                catcher.hold_arm(sol[0], sol[1])
            catcher.set_target([catcher_home[0], body_y, catcher_home[2]], vel=(0, 0, 0))
            m_cup.set(cup.tolist())
            if not closing and near and cup_d < CLOSE_DIST:
                catcher.close_gripper()
                closing = True
                result.update(closed=True, close_rel=rel)
                if verbose:
                    print(f"[t={t:.3f}s] CLOSE  cup_d={cup_d*100:.1f}cm rel={rel:.2f}")

        trace.append({"t": t, "phase": phase, "cup_d": cup_d, "rel": rel,
                      "nf": nf, "ball_z": bp[2]})
        sim.tick(phase, extra_payload={"cup_to_ball": cup_d, "rel_vel": rel,
                                       "fingers": nf, "ball_pos": bp.tolist()})

        if captured and result["close_t"] is not None and t - result["close_t"] > 1.6:
            break
        if not captured and bp[2] < 0.05:
            break
        if closing and not captured and bp[2] < EE_INTERCEPT_Z - 0.4:
            break

    bp, bv = ball_state(ball)
    ee = catcher.gripper_world_position()
    ee_v = catcher.gripper_world_velocity()
    cup, _ = cup_world()
    end_d = float(np.linalg.norm(cup - bp))
    end_rel = float(np.linalg.norm(bv - ee_v))
    nf = catcher.fingers_touching(ball)
    result["captured"] = captured
    result["caught"] = bool(captured and end_d < HOLD_DIST and nf >= 2)
    result["held"] = bool(result["caught"] and end_rel < HOLD_REL_VEL)
    result["end_d"] = end_d
    result["end_fingers"] = nf

    sim.logger.close()
    sim.video.close()

    if verbose:
        print("\n=== RESULT ===")
        print(f"closed={result['closed']} captured={captured} caught={result['caught']} held={result['held']}")
        print(f"min cup-to-ball: {result['min_cup_d']*100:.1f}cm   at: {result['_dbg']}")
        print(f"end: cup_d={end_d*100:.1f}cm fingers={nf} max_fingers={result['max_fingers']}")
        last = None
        for r in trace:
            if r["phase"] != last:
                print(f"  t={r['t']:.3f} -> {r['phase']:6s} cup_d={r['cup_d']*100:.1f}cm "
                      f"rel={r['rel']:.2f} nf={r['nf']} ball_z={r['ball_z']:.3f}")
                last = r["phase"]

    if runs_dir:
        rotate_runs(__import__("pathlib").Path(runs_dir), keep=5)
    return result


def run_grid(noise=False, seeds=1):
    cells = [(vx, vz) for vx in [2.5, 3.3, 4.5, 5.5] for vz in [-2.0, -3.2, -4.5]]
    results = []
    print(f"{'vx':>5} {'vz':>5} {'spd':>5} {'seed':>4} | {'caught':>6} {'held':>5} "
          f"{'mincup':>7} {'maxF':>4}")
    for vx, vz in cells:
        for s in range(seeds):
            p.connect(p.DIRECT)
            try:
                r = run(gui=False, runs_dir=None, ball_vx=vx, ball_vz=vz,
                        noise=noise, seed=s, verbose=False)
            finally:
                p.disconnect()
            results.append(r)
            print(f"{vx:5.1f} {vz:5.1f} {r['speed']:5.2f} {s:4d} | "
                  f"{str(r['caught']):>6} {str(r['held']):>5} "
                  f"{r['min_cup_d']*100:6.1f}cm {r['max_fingers']:>4}")
    held = sum(1 for r in results if r["held"])
    print(f"\nheld {held}/{len(results)}")
    return 0 if held == len(results) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--runs-dir", default=None)
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--noise", action="store_true",
                    help="sensing noise + 50 ms latency + estimation")
    ap.add_argument("--seeds", type=int, default=None, help="seeds/cell in --grid")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--vx", type=float, default=BALL_VX_DEFAULT)
    ap.add_argument("--vz", type=float, default=BALL_VZ_DEFAULT)
    args = ap.parse_args()
    if args.grid:
        n = args.seeds if args.seeds is not None else (3 if args.noise else 1)
        return run_grid(noise=args.noise, seeds=n)
    gui = not args.headless
    p.connect(p.GUI if gui else p.DIRECT)
    try:
        r = run(gui=gui, runs_dir=args.runs_dir, ball_vx=args.vx, ball_vz=args.vz,
                noise=args.noise, seed=args.seed)
        return 0 if r["held"] else 1
    finally:
        p.disconnect()


if __name__ == "__main__":
    sys.exit(main())
