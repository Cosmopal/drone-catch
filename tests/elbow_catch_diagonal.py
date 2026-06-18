"""DIAGONAL velocity-matched catch — M9 (WORK IN PROGRESS, does not catch yet).

The human-inspired redesign (user direction): station the body up-and-forward
of the intercept so the arm reaches FOLDED, back-and-down, and SWEEPS ALONG
the ball's path (arm tangent to the ball velocity), with the joints giving to
absorb — instead of stationing overhead and SCOOPING (which forces ~90% arm
extension, near the Jacobian singularity). Geometry: shoulder R_FOLD from the
intercept, perpendicular to the ball's arrival velocity; track the predicted
landing (tangent point) and let the Jacobian velocity feedforward
(arm_kinematics.ik_velocity) sweep the cup along the ball.

STATUS: the arm is folded at the tangent (geometry right) and the violent
arm<->body coupling oscillation is FIXED by "eventual positioning" (§21): the
arm IK targets the NOMINAL on-station, level body pose, not the actual
wobbling one, so the arm holds steady and stops driving the body's pitch.
Pitch swing dropped ~±20deg -> ~±3deg; cup-to-ball 9.3 -> 4.3 cm, 3 fingers
grab. Still does NOT retain: the body has a SLOW underdamped settle at the
diagonal station (z-sag ~0.35 m from the offset COM), so the catch depends on
the settle phase (fragile). Remaining: damp the body's diagonal-station hold
(COM-offset feedforward / position-loop retune). Working catch is the SCOOP
(elbow_catch_solo.py). See §20-21.

Base: the M7 2-DOF IK tracking catch — the arm servos the cup onto the ball's
predicted position via arm_kinematics; fingers cage. This variant changes the
body station + arm to the folded/diagonal/velocity-matched strategy above.

    python tests/elbow_catch_diagonal.py --headless --runs-dir runs/elbow
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

# Diagonal velocity-matched geometry (§20): instead of stationing straight
# above the intercept and SCOOPING up to the ball (which forces ~90% arm
# extension, near the Jacobian singularity), station the shoulder R_FOLD from
# the intercept, PERPENDICULAR to the ball's arrival velocity (up-and-forward).
# Then the arm reaches diagonally back-and-down, FOLDED (~74% reach), and its
# swing is tangent to the ball's path — it sweeps ALONG the ball, not into it.
R_FOLD = 0.355          # shoulder-to-cup distance at the catch (elbow ~1.3 rad,
                        # folded, away from the full-extension singularity)
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
KIPOS = 8.0            # position-integral gain (gains barely matter once the
KD_SCALE = 1.0         # startup launch is removed; steady COM sag dominates, §21)


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
    # Diagonal velocity-matched station: shoulder R_FOLD from the intercept,
    # perpendicular to the ball's arrival velocity (up-and-forward), so the arm
    # reaches back-and-down folded and sweeps ALONG the ball's path. (§20)
    vdir = np.array([ball_vx, ball_vz]) / math.hypot(ball_vx, ball_vz)
    perp = np.array([-vdir[1], vdir[0]])          # +90°: up-and-forward
    sh_xz = np.array([EE_INTERCEPT_X, EE_INTERCEPT_Z]) + R_FOLD * perp
    shoulder_target = np.array([sh_xz[0], 0.0, sh_xz[1]])
    catcher_home = shoulder_target - np.array([ak.SHOULDER_X, 0.0, ak.SHOULDER_Z])

    catcher = make_solo_drone(tuple(catcher_home), play_extent=(4.0, 4.0, 1.2),
                              urdf_path=GRIPPER_URDF)
    catcher.set_target(catcher_home)
    catcher.arm_reaction_ff = True
    catcher.attitude_gain_schedule = True
    catcher.arm_translational_ff_z = True
    catcher.controller.max_tilt_deg = 60.0
    catcher.controller.kp = CATCH_KP.copy()
    catcher.controller.kd = CATCH_KD.copy() * KD_SCALE
    catcher.controller.kI_pos = np.array([KIPOS, KIPOS, KIPOS])
    catcher.controller.kI = catcher.controller.kI.copy()
    catcher.controller.kI[2] = 0.3
    # Pre-position the arm folded so the cup sits at the intercept, forearm
    # pointing back-and-down toward the incoming ball.
    fdir0 = intercept - shoulder_target
    fdir0 = fdir0 / np.linalg.norm(fdir0)
    ee0 = (intercept - CUP_DEPTH * fdir0) - catcher_home   # EE target, body frame
    sol0 = ak.ik(ee0[0] - ak.SHOULDER_X, ee0[2] - ak.SHOULDER_Z)
    catcher.hold_arm(*(sol0 if sol0 else (READY_TH1, READY_TH2)))
    # Start the arm AT the pre-pose (the Drone inits it folded at -π/2). Else
    # hold_arm snaps it ~85° in one tick, and arm_translational_ff_z reads that
    # violent transient as a huge disturbance and slams in upward thrust — the
    # drone launches ~1 m into the ceiling at t=0. (§21)
    if sol0:
        p.resetJointState(catcher.body_id, catcher.shoulder_joint, sol0[0])
        p.resetJointState(catcher.body_id, catcher.elbow_joint, sol0[1])
    catcher.open_gripper()
    catcher.set_finger_dynamics(lateral_friction=PAD_FRICTION,
                                restitution=BALL_RESTITUTION)

    markers = MarkerSet()
    markers.intent.set(intercept.tolist())
    m_cup = Marker([1.0, 0.5, 0.1, 0.9], radius=0.03)
    logger = Logger(log_path, decimate=2)
    video = VideoRecorder(video_path, every=8, eye=(0.5, -3.0, 1.8),
                          target=(0.5, 0.0, 1.4), fov=70)
    sim = Sim([catcher], markers, logger, video, gui=gui)

    for _ in range(int(SETTLE_S / DT)):
        sim.tick("settle")

    launch_pos, launch_vel, t_flight = launch_state_for_intercept(
        intercept, (ball_vx, 0.0, ball_vz))
    if verbose:
        print(f"intercept={intercept.tolist()} station={np.round(catcher_home,2).tolist()} "
              f"t_flight={t_flight:.3f}s")
    ball = spawn_ball(launch_pos)
    p.changeVisualShape(ball, -1, rgbaColor=[1.0, 0.3, 0.3, 1])
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
            # --- Diagonal velocity-matched track (§20) ---
            # Far: hold the cup at the intercept (tangent point), folded. Near:
            # track the ball's position AND match its velocity, so from the
            # folded pose the cup SWEEPS ALONG the ball's path (the arm is
            # tangent to it) — co-moving contact, no scoop, no graze. The arm
            # stays folded (good Jacobian) so the velocity feedforward isn't
            # swamped (cf. §18, where the extended pose was singular).
            pred_xy, _ = predict_landing(est_p, est_v, EE_INTERCEPT_Z)
            near = est_v[2] < 0 and ball_dist < TRACK_RANGE
            R = np.array(p.getMatrixFromQuaternion(catcher.orientation())).reshape(3, 3)
            cup_v_arm = None
            if near and pred_xy is not None:
                phase = "track"
                # Keep the cup at the tangent (predicted landing, folded) and
                # let the velocity FF SWEEP it along the ball's path — don't
                # chase the ball's actual position back/up (that extends the arm
                # and is the scoop). Position stays folded; velocity co-moves.
                tgt_cup = np.array([pred_xy[0], pred_xy[1], EE_INTERCEPT_Z])
                body_y = pred_xy[1]
                cup_v_arm = (est_v[0], est_v[2])   # nominal (level) body frame
            elif pred_xy is not None:
                phase = "prepos"
                tgt_cup = np.array([pred_xy[0], pred_xy[1], EE_INTERCEPT_Z])
                body_y = pred_xy[1]
            else:
                phase = "prepos"
                tgt_cup = intercept
                body_y = 0.0
            ee_tgt = tgt_cup - CUP_DEPTH * fdir
            # Split the labor (user idea, §21): the fast precise arm covers the
            # body's SLOW POSITION error (so the cup stays on the ball even when
            # the body sags off-station), but IGNORES the body's fast PITCH
            # wobble — chasing the pitch was the destabilizing arm↔body coupling.
            # So: actual body POSITION, but NOMINAL (level) ORIENTATION.
            tgt_body = ee_tgt - catcher.position()
            rx, rz = tgt_body[0] - ak.SHOULDER_X, tgt_body[2] - ak.SHOULDER_Z
            r = math.hypot(rx, rz)
            if r > ak.REACH * 0.98:
                s = ak.REACH * 0.98 / r
                rx, rz = rx * s, rz * s
            sol = ak.ik(rx, rz)
            if sol is not None and cup_v_arm is not None:
                th1d, th2d = ak.ik_velocity(sol[0], sol[1], cup_v_arm[0],
                                            cup_v_arm[1], le=ak.L2 + CUP_DEPTH)
                catcher.hold_arm(sol[0], sol[1], th1d, th2d)
            elif sol is not None:
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
