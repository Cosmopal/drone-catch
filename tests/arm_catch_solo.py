"""Compliant-capture catch isolation test (Z2 architecture + soft constraint).

Single catcher at fixed location with arm at shoulder=-π/2 (catch pose,
EE behind body). Ball launched with known initial state so it arrives at
the catcher's EE with a chosen velocity. Two mechanisms compose:

1. Absorption sweep (reduces rel-vel at contact):
   - Shoulder forward sweep via spin_arm(+OMEGA_S * progress) timed so the
     EE tangential velocity is parallel to ball velocity at intercept.
2. Compliant capture (absorbs the residual):
   - Geometric trigger only (d < CATCH_DIST) — no rel-vel gate.
   - soft_grasp: point-to-point constraint capped at SOFT_MAX_FORCE, so the
     ball decelerates over ~m·Δv/F_max instead of one rigid solver step.
   - Shoulder goes back-drivable (low torque cap) so the arm yields under
     the ball's momentum — most of the stroke happens here.
   - Once rel_vel < LOCK_REL_VEL: firm_grasp (stiff carry) + brake shoulder
     to ω=0 in velocity mode (the documented-safe transition).

Acceptance: ball captured AND retained (still within hold radius, low rel
vel) at end of run. Peak constraint force + impulse are logged — the
impulse should match m_ball · Δv, and peak force should stay well below
the rigid-snap regime.

Usage:
    python tests/arm_catch_solo.py --headless --runs-dir runs/catch
    python tests/arm_catch_solo.py --headless --grid     # adversarial envelope
"""
from __future__ import annotations
import argparse
import sys
import os
import math
import numpy as np
import pybullet as p

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sim_setup import (Logger, MarkerSet, Marker, VideoRecorder, Sim,
                       make_world, make_solo_drone, auto_run_paths,
                       rotate_runs, DT)
from config import DEFAULT as DEFAULT_GAME
from ball import spawn_ball, state as ball_state, predict_landing

G = 9.81
L_ARM = 0.4

# Nominal ball state at intercept (single-run default; --grid sweeps these)
BALL_VX_DEFAULT = 3.3
BALL_VZ_DEFAULT = -3.2
EE_INTERCEPT_X = 1.1     # where ball passes through catcher's catch plane
EE_INTERCEPT_Z = 1.5     # at this height

SHOULDER_CATCH = -math.pi / 2   # arm start pose: EE behind body

# Absorption sweep
T_ABSORB_MIN = 0.10     # lower bound on the sweep window before intercept
OMEGA_S = 8.0           # rad/s shoulder forward sweep
# Ramp-integral factor: 1.0 → shoulder reaches the matched angle exactly at
# intercept. >1 makes the EE sweep through the catch point early and be past
# it when the ball arrives (cost us the steep-ball grid points); <1 leaves
# the shoulder late (cost us the fast/shallow ones).
SWEEP_MARGIN = 1.0

# Compliant capture
CATCH_DIST = 0.15       # m — geometric trigger (no rel-vel gate)
SOFT_MAX_FORCE = 8.0    # N — constraint cap during absorption.
                        # m·Δv at worst grid corner ≈ 0.065·5 ≈ 0.33 N·s
                        # → ~40 ms absorb, ~10 cm stroke at this cap.
FIRM_MAX_FORCE = 200.0  # N — carry stiffness after lock
LOCK_REL_VEL = 0.3      # m/s — firm up + brake below this
BACKDRIVE_TORQUE = 0.3  # N·m — shoulder cap while absorbing (max is 2.0)
HOLD_DIST = 0.25        # acceptance: ball within this of EE at end
HOLD_REL_VEL = 0.5      # acceptance: rel vel below this at end

SETTLE_S = 1.0
FLOOR_MARGIN = 0.15     # launch point must be above this z
LAUNCH_X_MIN = -3.7     # and inside the west wall (room is 8 m → wall at -4)


def launch_state_for_intercept(ee_pos, vx_at_intercept, vz_at_intercept):
    """Compute (launch_pos, launch_vel, t_flight) so the ball arrives at
    ee_pos with the given velocity (gravity only, no drag).

    Flight time is chosen as long as possible subject to the launch point
    staying inside the room (z ≥ FLOOR_MARGIN, x ≥ LAUNCH_X_MIN), so grid
    points with slow/steep arrivals don't ask for a launch below the floor.
    """
    ee_x, ee_z = ee_pos[0], ee_pos[2]
    vz = vz_at_intercept
    # z_launch(t) = ee_z - vz·t - ½g·t² is decreasing in t; later root of
    # z_launch = FLOOR_MARGIN gives the max flight time the floor allows.
    t_floor = (-vz + math.sqrt(vz * vz + 2 * G * (ee_z - FLOOR_MARGIN))) / G
    t_wall = (ee_x - LAUNCH_X_MIN) / vx_at_intercept
    t = min(t_floor, t_wall)
    vz_launch = vz + G * t
    z_launch = ee_z - vz * t - 0.5 * G * t * t
    x_launch = ee_x - vx_at_intercept * t
    return (np.array([x_launch, 0.0, z_launch]),
            np.array([vx_at_intercept, 0.0, vz_launch]),
            t)


def run(gui: bool, runs_dir: str | None,
        ball_vx: float = BALL_VX_DEFAULT, ball_vz: float = BALL_VZ_DEFAULT,
        verbose: bool = True) -> dict:
    log_path, video_path = auto_run_paths(runs_dir)
    make_world(DEFAULT_GAME, gui=gui)

    # Velocity-matched shoulder angle: arm tip tangential velocity direction
    # parallel to ball velocity at intercept.
    shoulder_at_catch = -math.atan2(-ball_vz, ball_vx)
    # Sweep window sized so the ramped sweep (∫ω = OMEGA_S·T/2) covers the
    # rotation from catch pose to the matched angle by intercept time. A
    # fixed 100 ms window made the shoulder arrive late for fast/shallow
    # balls (Δθ up to ~1.2 rad) — the EE was still pointing back-down when
    # the ball flew past.
    sweep_dtheta = shoulder_at_catch - SHOULDER_CATCH
    t_absorb = max(T_ABSORB_MIN,
                   SWEEP_MARGIN * 2.0 * sweep_dtheta / OMEGA_S)
    # Catcher body position so EE meets ball at shoulder_at_catch.
    # ee_body(θ) = (L·sin(θ), 0, -L·cos(θ)). Body = ball - ee_body.
    catcher_home = np.array([
        EE_INTERCEPT_X - L_ARM * math.sin(shoulder_at_catch),
        0.0,
        EE_INTERCEPT_Z + L_ARM * math.cos(shoulder_at_catch),
    ])

    catcher = make_solo_drone(tuple(catcher_home),
                              play_extent=(4.0, 4.0, 1.2))
    catcher.set_target(catcher_home)
    catcher.arm_reaction_ff = True
    catcher.attitude_gain_schedule = True
    catcher.arm_translational_ff_z = True
    catcher.controller.max_tilt_deg = 60.0
    catcher.hold_arm(SHOULDER_CATCH, 0.0)

    markers = MarkerSet()
    markers.intent.set([EE_INTERCEPT_X, 0.0, EE_INTERCEPT_Z])
    m_pred = Marker([0.1, 0.9, 1.0, 0.9], radius=0.05)

    logger = Logger(log_path, decimate=2)
    video = VideoRecorder(video_path, every=8,
                          eye=(0.5, -3.0, 1.8),
                          target=(0.5, 0.0, 1.3),
                          fov=70)
    sim = Sim([catcher], markers, logger, video, gui=gui)

    for _ in range(int(SETTLE_S / DT)):
        sim.tick("settle")

    ee_intercept = np.array([EE_INTERCEPT_X, 0.0, EE_INTERCEPT_Z])
    launch_pos, launch_vel, t_flight = launch_state_for_intercept(
        ee_intercept, ball_vx, ball_vz)
    if verbose:
        print(f"EE catch target: {ee_intercept.tolist()}  "
              f"shoulder@catch={math.degrees(shoulder_at_catch):.1f}°")
        print(f"Launch: pos={np.round(launch_pos, 3).tolist()} "
              f"vel={np.round(launch_vel, 3).tolist()} t_flight={t_flight:.3f}s")
    ball = spawn_ball(launch_pos)
    p.changeVisualShape(ball, -1, rgbaColor=[1.0, 0.3, 0.3, 1])
    # Disable damping for clean ballistic so the analytical launch math
    # (and the catcher's fixed pre-position) holds exactly.
    p.changeDynamics(ball, -1, linearDamping=0.0, angularDamping=0.0)
    p.resetBaseVelocity(ball, linearVelocity=launch_vel.tolist())

    # State machine: absorbing (sweep engaged) → caught (soft constraint on)
    # → locked (firm constraint, shoulder braked).
    absorbing = False
    caught = False
    locked = False
    result = {
        "vx": ball_vx, "vz": ball_vz, "speed": math.hypot(ball_vx, ball_vz),
        "caught": False, "held": False,
        "contact_rel": None, "contact_d": None, "catch_t": None,
        "lock_t": None, "peak_force": 0.0, "impulse": 0.0,
        "min_d": 1e9, "min_t": 0.0, "min_rel_vel": 1e9,
    }
    catch_trace = []
    timeout_s = t_flight + 1.5

    for i in range(int(timeout_s / DT)):
        bp, bv = ball_state(ball)
        ee_pos = catcher.gripper_world_position()
        ee_vel = catcher.gripper_world_velocity()
        d = float(np.linalg.norm(ee_pos - bp))
        rel = float(np.linalg.norm(bv - ee_vel))

        # Time-to-intercept (later root, ball descending to EE_z)
        a, b, c = -0.5 * G, bv[2], bp[2] - EE_INTERCEPT_Z
        disc = b * b - 4 * a * c
        t_intercept = None
        if disc >= 0:
            sq = math.sqrt(disc)
            roots = [r for r in [(-b + sq) / (2 * a),
                                 (-b - sq) / (2 * a)] if r > 1e-3]
            if roots:
                t_intercept = max(roots)

        # --- Compliant capture trigger: geometric only ---
        if not caught and d < CATCH_DIST:
            if catcher.soft_grasp(ball, max_distance=CATCH_DIST,
                                  max_force=SOFT_MAX_FORCE):
                caught = True
                result.update(caught=True, contact_rel=rel, contact_d=d,
                              catch_t=i * DT)
                if verbose:
                    print(f"[t={i*DT:.3f}s] CONTACT  d={d*100:.1f}cm  "
                          f"rel_vel={rel:.2f}m/s  (soft, F≤{SOFT_MAX_FORCE}N)")

        if caught:
            F = catcher.grasp_force()
            if not locked:
                # Absorption metrics only — after lock the constraint force
                # is just statically holding the ball (gravity + carry).
                result["peak_force"] = max(result["peak_force"], F)
                result["impulse"] += F * DT
                phase = "absorb_contact"
                # Back-drivable shoulder: keep commanding the sweep but let
                # the ball's load dominate. Body holds station; the gain
                # schedule now sees the held mass.
                catcher.spin_arm(OMEGA_S, 0.0, torque_cap=BACKDRIVE_TORQUE)
                if rel < LOCK_REL_VEL:
                    locked = True
                    result["lock_t"] = i * DT
                    catcher.firm_grasp(FIRM_MAX_FORCE)
                    catcher.spin_arm(0.0, 0.0)  # brake at full torque
                    catcher.set_target(catcher.position(), vel=(0, 0, 0))
                    if verbose:
                        absorb_ms = (result["lock_t"] - result["catch_t"]) * 1e3
                        print(f"[t={i*DT:.3f}s] LOCKED  rel_vel={rel:.2f}  "
                              f"absorb={absorb_ms:.0f}ms  "
                              f"peak_F={result['peak_force']:.1f}N  "
                              f"impulse={result['impulse']:.3f}N·s")
            else:
                phase = "carry"
        elif absorbing:
            # Sweep engaged, ball still inbound — keep the ramp tied to
            # time-to-intercept so ∫ω dt = Ω·T/2 lands the shoulder on the
            # matched angle exactly at intercept. Fall back to full ω only
            # when t_intercept is gone (ball below EE plane); never snap the
            # shoulder back to catch-pose mid-flight.
            if t_intercept is not None:
                progress = max(0.0, min(1.0, 1.0 - t_intercept / t_absorb))
                catcher.spin_arm(OMEGA_S * progress, 0.0)
            else:
                catcher.spin_arm(OMEGA_S, 0.0)
            phase = "absorb"
        else:
            # In the full game, a perception-driven commitment gate
            # (descending + past midline) lives in main.py. Here the launch
            # is ground truth — the ball is committed from the moment it
            # exists, and gating engagement on it truncated the sweep window
            # for fast/shallow arrivals.
            predicted_xy, _ = predict_landing(bp, bv, EE_INTERCEPT_Z)
            if predicted_xy is not None:
                m_pred.set([predicted_xy[0], predicted_xy[1], EE_INTERCEPT_Z])
                # Body sits offset from the EE catch point so that EE meets
                # ball when shoulder is at shoulder_at_catch.
                body_x_offset = -L_ARM * math.sin(shoulder_at_catch)
                body_target = np.array([predicted_xy[0] + body_x_offset,
                                        predicted_xy[1], catcher_home[2]])
                if t_intercept is not None and t_intercept <= t_absorb:
                    absorbing = True
                    progress = max(0.0, min(1.0, 1.0 - t_intercept / t_absorb))
                    catcher.set_target(body_target, vel=(0.0, 0.0, 0.0))
                    catcher.spin_arm(OMEGA_S * progress, 0.0)
                    phase = "absorb"
                else:
                    catcher.set_target(body_target, vel=(0.0, 0.0, 0.0))
                    catcher.hold_arm(SHOULDER_CATCH, 0.0)
                    phase = "track"
            else:
                catcher.set_target(catcher_home, vel=(0.0, 0.0, 0.0))
                catcher.hold_arm(SHOULDER_CATCH, 0.0)
                phase = "wait"

        _, orn = p.getBasePositionAndOrientation(catcher.body_id)
        _, pitch_now, _ = p.getEulerFromQuaternion(orn)
        catch_trace.append({
            "t": i * DT, "phase": phase,
            "t_intercept": t_intercept if t_intercept is not None else -1,
            "pitch_deg": math.degrees(pitch_now),
            "ee_pos": ee_pos.tolist(), "ee_vel": ee_vel.tolist(),
            "ball_pos": bp.tolist(), "ball_vel": bv.tolist(),
            "shoulder_pos": catcher.joint_states()[0],
            "shoulder_vel": catcher.joint_states()[1],
            "dist": d, "rel_vel": rel,
            "grasp_force": catcher.grasp_force() if caught else 0.0,
        })

        if d < result["min_d"]:
            result.update(min_d=d, min_t=i * DT, min_rel_vel=rel)

        sim.tick(phase, extra_payload={
            "ball_pos": bp.tolist(), "ball_vel": bv.tolist(),
            "ee_pos": ee_pos.tolist(), "ee_vel": ee_vel.tolist(),
            "ee_to_ball": d, "rel_vel": rel,
            "grasp_force": catch_trace[-1]["grasp_force"],
            "t_intercept": t_intercept if t_intercept is not None else -1,
        })

        # Stop after lock settles, or ball drops past floor uncaught
        if locked and i * DT > result["lock_t"] + 0.5:
            break
        if bp[2] < 0.05 and not caught:
            break

    # Retention check: caught is only a catch if the ball is still with us.
    bp, bv = ball_state(ball)
    ee_pos = catcher.gripper_world_position()
    ee_vel = catcher.gripper_world_velocity()
    end_d = float(np.linalg.norm(ee_pos - bp))
    end_rel = float(np.linalg.norm(bv - ee_vel))
    result["held"] = bool(result["caught"] and end_d < HOLD_DIST
                          and end_rel < HOLD_REL_VEL)
    result["end_d"] = end_d
    result["end_rel"] = end_rel

    sim.logger.close()
    sim.video.close()

    if verbose:
        print("\n=== RESULT ===")
        print(f"caught: {result['caught']}  held: {result['held']}  "
              f"(end d={end_d*100:.1f}cm rel={end_rel:.2f}m/s)")
        if result["caught"]:
            print(f"contact: d={result['contact_d']*100:.1f}cm  "
                  f"rel_vel={result['contact_rel']:.2f}m/s")
            print(f"absorption: peak_F={result['peak_force']:.1f}N  "
                  f"impulse={result['impulse']:.3f}N·s  "
                  f"(m·Δv ≈ {0.065 * result['contact_rel']:.3f}N·s)")
        print(f"closest approach: {result['min_d']*100:.1f} cm "
              f"@ t={result['min_t']:.3f}s  rel_vel={result['min_rel_vel']:.2f} m/s")

        last_ph = None
        print("Phase transitions:")
        for r in catch_trace:
            if r["phase"] != last_ph:
                print(f"  t={r['t']:.3f}  -> {r['phase']:14s}  "
                      f"ball_z={r['ball_pos'][2]:.3f}  "
                      f"ball_vz={r['ball_vel'][2]:+.2f}  d={r['dist']*100:.1f}cm")
                last_ph = r["phase"]

        # Dump catch-window trace (last 400 ms around contact/closest approach)
        t_close = result["catch_t"] if result["catch_t"] else result["min_t"]
        print("\n--- Catch-window trace ---")
        for rec in catch_trace:
            if not (-0.15 < rec["t"] - t_close < 0.40): continue
            if int(rec["t"] * 240) % 3 != 0: continue  # decimate
            print(f"  t={rec['t']:.3f}  ph={rec['phase']:14s}  "
                  f"shldr={rec['shoulder_pos']:+.2f}@{rec['shoulder_vel']:+5.1f}  "
                  f"d={rec['dist']*100:5.1f}cm  rel={rec['rel_vel']:5.2f}  "
                  f"F={rec['grasp_force']:5.2f}N  "
                  f"pitch={rec['pitch_deg']:+6.1f}°")

    if runs_dir:
        rotate_runs(__import__("pathlib").Path(runs_dir), keep=5)

    return result


def run_grid(headless: bool) -> int:
    """Sweep the adversarial incoming-velocity envelope. Arrival speeds
    3.2–7.1 m/s, descent angles ~20–61° — roughly what the room geometry +
    thrower physics permit."""
    vxs = [2.5, 3.3, 4.5, 5.5]
    vzs = [-2.0, -3.2, -4.5]
    results = []
    print(f"{'vx':>5} {'vz':>5} {'spd':>5} | {'caught':>6} {'held':>5} "
          f"{'rel@hit':>7} {'peakF':>6} {'impulse':>7} {'absorb':>7}")
    for vx in vxs:
        for vz in vzs:
            p.connect(p.DIRECT)
            try:
                r = run(gui=False, runs_dir=None,
                        ball_vx=vx, ball_vz=vz, verbose=False)
            finally:
                p.disconnect()
            results.append(r)
            absorb = ((r["lock_t"] - r["catch_t"]) * 1e3
                      if r["lock_t"] is not None and r["catch_t"] is not None
                      else None)
            rel_s = (f"{r['contact_rel']:7.2f}"
                     if r["contact_rel"] is not None else "   miss")
            absorb_s = f"{absorb:5.0f}ms" if absorb is not None else "      —"
            print(f"{vx:5.1f} {vz:5.1f} {r['speed']:5.2f} | "
                  f"{str(r['caught']):>6} {str(r['held']):>5} "
                  f"{rel_s} {r['peak_force']:6.2f} {r['impulse']:7.3f} "
                  f"{absorb_s}")
    held = sum(1 for r in results if r["held"])
    print(f"\nheld {held}/{len(results)}  "
          f"max peak force {max(r['peak_force'] for r in results):.1f}N")
    return 0 if held == len(results) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--runs-dir", default=None)
    ap.add_argument("--grid", action="store_true",
                    help="sweep incoming-velocity envelope (forces headless)")
    ap.add_argument("--vx", type=float, default=BALL_VX_DEFAULT)
    ap.add_argument("--vz", type=float, default=BALL_VZ_DEFAULT)
    args = ap.parse_args()

    if args.grid:
        return run_grid(headless=True)

    gui = not args.headless
    p.connect(p.GUI if gui else p.DIRECT)
    try:
        r = run(gui=gui, runs_dir=args.runs_dir,
                ball_vx=args.vx, ball_vz=args.vz)
        return 0 if r["held"] else 1
    finally:
        p.disconnect()


if __name__ == "__main__":
    sys.exit(main())
