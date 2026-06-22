"""M3 — solo throw test.

Drone cruises forward, arm sweeps from -π/2 (wound up) toward release_alpha,
ball releases at the target arm angle. No catcher; we measure ball's world
trajectory after release and compare to the planned ballistic.

Pipeline:
1. Plan a simple ballistic: pick vz that uses half the available ceiling
   clearance, pick release_x at 70% of the way between start and target.
2. Decompose release_vel into (v_drone_horiz, ω, release_alpha) via throw.py.
3. Compute cruise speed accounting for the sweep's natural translational push
   (so cruise + sweep delivers v_drone at release).
4. Choreography:
   - Settle (1 s, drone holds at start).
   - Cruise: vel-ramp 0 → cruise_vx over VEL_RAMP_S, position carrot follows.
   - Spin trigger: when drone's x position is within `predicted sweep distance`
     of release_x, start arm sweep at ω with 200 ms ramp.
   - Release: when shoulder angle ≥ release_alpha, fire release.
   - Recovery: brake arm to 0 in velocity mode, drone decels to home.
5. Measure: actual ball world velocity at release, integrate forward
   (PyBullet handles), record landing position, compare to plan.

Usage:
    python tests/throw_solo.py --headless --runs-dir runs/m3
"""
from __future__ import annotations
import argparse
import sys
import os
import math
from dataclasses import replace
import numpy as np
import pybullet as p

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from sim_setup import (Logger, MarkerSet, Marker, VideoRecorder, Sim,
                       make_world, make_solo_drone, auto_run_paths,
                       rotate_runs, spawn_ball_at_ee, DT)
from config import DEFAULT as DEFAULT_GAME
from throw import decompose_throw, cruise_speed_for_release

G = 9.81

# Geometry
TARGET_LANDING_X = +3.5         # default, can override on CLI
HOVER_Z = 1.5
L_ARM = 0.4

# Choreography
SETTLE_S = 0.6
VEL_RAMP_S = 0.5              # ramp drone vel target 0 → cruise_vx
RAMP_DURATION = 0.20          # arm spin ramp 0 → ω_target
RUNWAY_MARGIN = 0.4           # extra cruise space before spin trigger
RECOVER_S = 2.5
TIMEOUT_S = 6.0


def plan_ballistic(start_x, target_x, target_z, hover_z,
                   ceiling_z, ceiling_margin,
                   release_alpha, L_arm):
    """Plan: pick vz at half ceiling clearance, pick drone_release_x at 60%
    of the way between start and target. EE at release is forward+below
    drone by L·sin(α), L·cos(α). Solve for vx that lands at (target_x, target_z).

    Returns:
      drone_release_x — drone body x position at release moment
      release_pos     — EE world position at release (where ball is released)
      release_vel     — ball velocity at release
    """
    max_apex = ceiling_z - ceiling_margin
    apex_target = (hover_z + max_apex) / 2
    drone_release_x = start_x + 0.60 * (target_x - start_x)
    # EE position relative to drone (body frame, for level drone)
    ee_dx = L_arm * math.sin(release_alpha)
    ee_dz = -L_arm * math.cos(release_alpha)
    release_x = drone_release_x + ee_dx
    release_z = hover_z + ee_dz
    # Pick vz so apex is at apex_target (above release_z)
    vz = math.sqrt(2 * G * max(0.1, apex_target - release_z))
    # Time to fall from apex to target_z
    t_up = vz / G
    apex_z = release_z + vz * vz / (2 * G)
    t_down = math.sqrt(2 * max(0, apex_z - target_z) / G)
    t_flight = t_up + t_down
    vx = (target_x - release_x) / t_flight
    return drone_release_x, np.array([release_x, 0.0, release_z]), \
           np.array([vx, 0.0, vz])


def run(gui: bool, runs_dir: str | None,
        use_ff: bool = True, gain_sched: bool = True,
        release_alpha_deg: float = 70.0,
        target_landing_x: float = TARGET_LANDING_X,
        target_landing_z: float = 0.025):
    log_path, video_path = auto_run_paths(runs_dir)
    # Use a wider room than the demo default so longer throws fit without
    # ball hitting the wall. Walls were at ±4 m for the 8 m default; for
    # throws past x≈3.5 the ball would bounce back. 14 m gives walls at ±7.
    cfg = replace(DEFAULT_GAME, room_size=14.0)
    make_world(cfg, gui=gui)

    target_landing = np.array([target_landing_x, 0.0, target_landing_z])

    # First, plan/decompose with a placeholder start position to learn the
    # cruise speed and spin-trigger geometry. We then pick the drone's
    # actual start position to be just upstream of the spin trigger,
    # eliminating dead "constant cruise" time.
    release_alpha = math.radians(release_alpha_deg)
    placeholder_start_x = -3.0
    # Aim ~30 cm past the desired target. After all our other corrections,
    # the throw lands ~30 cm short consistently — likely PyBullet's linear
    # damping (5%/s, ~3% over 0.7s flight) plus a few cm of release-point
    # lag (drone undershoots its planned release_x by ~5 cm because vx
    # dips during sweep). Empirical offset, easy to retune if drag or
    # arm geometry changes.
    AIM_OFFSET = 0.30
    drone_release_x, release_pos, release_vel = plan_ballistic(
        start_x=placeholder_start_x, target_x=target_landing[0] + AIM_OFFSET,
        target_z=target_landing[2], hover_z=HOVER_Z,
        ceiling_z=cfg.ceiling_z, ceiling_margin=cfg.ceiling_margin,
        release_alpha=release_alpha, L_arm=L_ARM)
    # Empirical pitch correction: drone is observed to pitch +5–10° forward
    # at release (cascade fighting recoil + vel-tracking). That tilt rotates
    # arm tip velocity in world frame, causing throws to land ~30 cm short.
    # Pre-rotate the target by an estimated pitch so the body-frame arm
    # output ends up world-frame-aligned with the desired throw.
    EXPECTED_PITCH_RAD = math.radians(7.0)
    decomp = decompose_throw(release_vel, L_arm=L_ARM,
                             release_alpha=release_alpha,
                             expected_pitch_rad=EXPECTED_PITCH_RAD)
    cruise_vx = cruise_speed_for_release(decomp)
    sweep_angle = decomp.release_alpha + math.pi / 2
    sweep_time = sweep_angle / decomp.omega + RAMP_DURATION * 0.5
    drone_dx_during_sweep = cruise_vx * sweep_time
    spin_trigger_x = drone_release_x - drone_dx_during_sweep
    vel_ramp_distance = 0.5 * cruise_vx * VEL_RAMP_S
    drone_start_x = spin_trigger_x - vel_ramp_distance - RUNWAY_MARGIN
    start_pos = np.array([drone_start_x, 0.0, HOVER_Z])

    drone = make_solo_drone(tuple(start_pos), play_extent=(5.0, 5.0, 1.2))
    drone.set_target(start_pos)
    drone.arm_reaction_ff = use_ff
    drone.attitude_gain_schedule = gain_sched
    drone.arm_translational_ff_z = use_ff
    release_x = drone_release_x
    # Predicted ballistic landing from the plan: ball arcs up, then falls
    # back to target_landing_z (could be floor or hover height).
    t_up = release_vel[2] / G
    apex_z = release_pos[2] + release_vel[2]**2 / (2*G)
    t_down = math.sqrt(2 * max(0, apex_z - target_landing_z) / G)
    t_flight = t_up + t_down
    plan_landing = (release_pos[0] + release_vel[0] * t_flight,
                    0.0, target_landing_z)
    plan_apex = apex_z

    print(f"[plan] release_x={release_x:.2f}  release_vel="
          f"({release_vel[0]:.2f}, 0, {release_vel[2]:.2f})  "
          f"|v|={np.linalg.norm(release_vel):.2f}  apex={plan_apex:.2f}")
    print(f"[decomp] α={math.degrees(release_alpha):.0f}°  ω={decomp.omega:.1f}  "
          f"v_drone={decomp.v_drone_horiz:.2f}  cruise={cruise_vx:.2f}  "
          f"Δvx_sweep={decomp.expected_dvx_during_sweep:+.2f}")
    print(f"[choreo] sweep angle={math.degrees(sweep_angle):.0f}°  "
          f"sweep time≈{sweep_time*1000:.0f}ms  "
          f"spin trigger x={spin_trigger_x:.2f}  drone start x={drone_start_x:.2f}  "
          f"runway={spin_trigger_x - drone_start_x:.2f}m")
    print(f"[plan] expected landing≈{plan_landing}  target={target_landing.tolist()}")

    # Spawn ball at EE, grasp
    p.stepSimulation()
    ball = spawn_ball_at_ee(drone)

    markers = MarkerSet()
    markers.intent.set([release_x, 0.0, HOVER_Z])  # magenta = planned release
    extra = Marker([0.2, 0.9, 0.4, 1.0], radius=0.10)  # green = planned landing
    extra.set(plan_landing)

    logger = Logger(log_path, decimate=4)
    # Camera framing: center the view between drone start and target,
    # then back the camera off just far enough to fit the action span at
    # a moderate FOV (65° feels natural — 90° was wide-angle and made
    # everything look small). Camera y must stay > -7 m (room walls).
    midpoint_x = 0.5 * (drone_start_x + target_landing[0])
    action_span = target_landing[0] - drone_start_x + 1.5  # m, with margin
    cam_fov = 65.0
    cam_y = -min(6.5, max(3.5, action_span / (2 * math.tan(math.radians(cam_fov / 2)))))
    video = VideoRecorder(video_path, every=8,
                          eye=(midpoint_x, cam_y, 1.9),
                          target=(midpoint_x, 0.0, 1.2),
                          fov=cam_fov)
    sim = Sim([drone], markers, logger, video, gui=gui)

    full_trace = []
    ball_trace = []
    release_info = {"fired": False, "v_ee": None, "ee_pos": None,
                    "drone_pos": None, "drone_vel": None,
                    "shoulder": None, "t": None}
    ball_track = {"target_z_crossing": None, "floor_contact": None,
                  "prev_pos": None}

    def sample(phase):
        pos = drone.position()
        vel = drone.velocity()
        s_pos, s_vel, _, _ = drone.joint_states()
        ee_pos = drone.gripper_world_position()
        ee_vel = drone.gripper_world_velocity()
        _, orn = p.getBasePositionAndOrientation(drone.body_id)
        _, pitch, _ = p.getEulerFromQuaternion(orn)
        full_trace.append((sim.t, phase, pos.copy(), vel.copy(),
                           s_pos, s_vel, ee_pos.copy(), ee_vel.copy(),
                           float(np.degrees(pitch))))
        # Ball tracking: only meaningful after release
        if release_info["fired"]:
            bp, _ = p.getBasePositionAndOrientation(ball)
            bv, _ = p.getBaseVelocity(ball)
            bp = np.array(bp); bv = np.array(bv)
            ball_trace.append((sim.t, bp.copy(), bv.copy()))
            if (ball_track["target_z_crossing"] is None
                    and ball_track["prev_pos"] is not None):
                pp = ball_track["prev_pos"]
                if pp[2] >= target_landing_z and bp[2] < target_landing_z:
                    f = ((pp[2] - target_landing_z)
                         / max(1e-6, pp[2] - bp[2]))
                    ball_track["target_z_crossing"] = pp + f * (bp - pp)
            if ball_track["floor_contact"] is None and bp[2] < 0.05:
                ball_track["floor_contact"] = bp.copy()
            ball_track["prev_pos"] = bp.copy()

    # --- Phase 1: settle ---
    for _ in range(int(SETTLE_S / DT)):
        sim.tick("settle")
        sample("settle")

    # --- Phase 2-4: cruise + spin + release ---
    cruise_start_t = sim.t
    spin_started = False
    spin_start_t = None
    released = False

    while (sim.t - cruise_start_t) < TIMEOUT_S:
        elapsed = sim.t - cruise_start_t
        if not released:
            # Closed-loop cruise: position target = drone's current x position
            # (zero position error), vel target = ramped cruise_vx. The
            # cascade is then driven only by vel error → tracks cruise_vx
            # without the overshoot caused by an open-loop position carrot.
            cur_vx = (cruise_vx * min(1.0, elapsed / VEL_RAMP_S))
            cur_x = drone.position()[0]
            drone.set_target((cur_x, 0.0, HOVER_Z),
                             vel=(cur_vx, 0.0, 0.0))
        else:
            # Post-release: brake home. Position target = start_pos pulls
            # the drone back; vel target = 0 stops forward motion.
            drone.set_target(start_pos, vel=(0.0, 0.0, 0.0))

        # Adaptive spin trigger: predict where drone will be after sweep_time
        # using its CURRENT vx, fire when that prediction reaches release_x.
        # Self-adjusts whether drone is faster or slower than planned.
        cur_vx_meas = drone.velocity()[0]
        predicted_x_at_release = (drone.position()[0]
                                  + cur_vx_meas * sweep_time)
        if not spin_started and predicted_x_at_release >= drone_release_x:
            spin_started = True
            spin_start_t = sim.t

        # Spin: ramp ω 0 → decomp.omega over RAMP_DURATION, then hold
        if spin_started and not released:
            t_spin = sim.t - spin_start_t
            ramp = min(1.0, t_spin / RAMP_DURATION)
            drone.spin_arm(shoulder_vel=decomp.omega * ramp, elbow_vel=0.0)

        # Release: shoulder angle ≥ release_alpha
        if spin_started and not released:
            s_pos, _, _, _ = drone.joint_states()
            if s_pos >= release_alpha:
                # Capture state BEFORE releasing (release modifies the ball)
                release_info["v_ee"] = drone.gripper_world_velocity().copy()
                release_info["ee_pos"] = drone.gripper_world_position().copy()
                release_info["drone_pos"] = drone.position().copy()
                release_info["drone_vel"] = drone.velocity().copy()
                release_info["shoulder"] = s_pos
                release_info["t"] = sim.t
                drone.release()
                # Brake the arm immediately so it doesn't whip around and
                # collide with the just-released ball. Stay in velocity mode
                # so the FF brake transient stays in sync.
                drone.spin_arm(shoulder_vel=0.0, elbow_vel=0.0)
                release_info["fired"] = True
                released = True
                marker_actual = Marker([1.0, 0.5, 0.0, 1.0], radius=0.08)
                marker_actual.set(release_info["ee_pos"])
                markers.actual = marker_actual

        phase = ("release" if released else
                 "spin" if spin_started else "cruise")
        sim.tick(phase)
        sample(phase)

        # Done once ball has been in flight long enough to land
        if released and (sim.t - release_info["t"]) > 2.5:
            break

    # --- Phase 5: brake arm + drone returns toward start. Also keep
    # tracking the ball: capture its position when it crosses target_z
    # going DOWN (interpolated for accuracy) — that's where a catcher at
    # that altitude would intercept it. Also capture floor first-contact
    # for ground-target throws.
    drone.spin_arm(0.0, 0.0)
    drone.set_target(start_pos, vel=(0.0, 0.0, 0.0))
    for _ in range(int(RECOVER_S / DT)):
        sim.tick("recover")
        sample("recover")

    target_z_crossing = ball_track["target_z_crossing"]
    floor_contact_pos = ball_track["floor_contact"]
    final_ball_pos = np.array(p.getBasePositionAndOrientation(ball)[0])

    logger.close()
    video.close()
    p.disconnect()
    if runs_dir:
        from pathlib import Path
        rotate_runs(Path(runs_dir), keep=5)

    # ---- Report ----
    print("\n=== M3 throw_solo result ===")
    if not release_info["fired"]:
        print("  FAIL: release never fired (timeout)")
        return 1

    v_ee = release_info["v_ee"]
    print(f"  release fired at t={release_info['t']:.2f}s, "
          f"shoulder={math.degrees(release_info['shoulder']):.1f}° "
          f"(target {release_alpha_deg:.0f}°)")
    print(f"  drone state: pos={release_info['drone_pos'].round(2).tolist()} "
          f"vel={release_info['drone_vel'].round(2).tolist()}")
    print(f"  EE state:    pos={release_info['ee_pos'].round(2).tolist()} "
          f"vel={v_ee.round(2).tolist()}")
    print(f"  planned release_vel: {release_vel.round(2).tolist()}")
    print(f"  achieved/planned ratio:  vx={v_ee[0]/release_vel[0]:.2f}  "
          f"vz={v_ee[2]/release_vel[2]:.2f}")

    # Ball trajectory — error vs user target (not the aim-offset plan_landing)
    print(f"\n  user target:                 {target_landing.round(2).tolist()}")
    print(f"  aim-adjusted plan landing:   {[round(x, 2) for x in plan_landing]}")
    if target_z_crossing is not None:
        err_xy = float(np.linalg.norm(target_z_crossing[:2]
                                      - target_landing[:2]))
        print(f"  ball at z={target_landing_z:.2f} actual:    {target_z_crossing.round(2).tolist()}    err vs target={err_xy*100:.0f} cm")
    else:
        print(f"  ball never reached z={target_landing_z:.2f} (target above apex?)")
    if floor_contact_pos is not None:
        print(f"  ball floor contact:          {floor_contact_pos.round(2).tolist()}")
    print(f"  ball final (after bounces):  {final_ball_pos.round(2).tolist()}")

    # Trace excerpts
    print("\nBall trajectory (every Nth sample after release):")
    if ball_trace:
        stride = max(1, len(ball_trace) // 14)
        for s in ball_trace[::stride]:
            t, bp, bv = s
            print(f"  t={t:5.2f}  ball pos=({bp[0]:+.2f},{bp[1]:+.2f},{bp[2]:.2f})  "
                  f"vel=({bv[0]:+.2f},{bv[1]:+.2f},{bv[2]:+.2f})")

    print("\nTrace (release window ±0.4s):")
    if release_info["t"] is not None:
        t_rel = release_info["t"]
        rel_window = [s for s in full_trace if abs(s[0] - t_rel) < 0.4]
        stride = max(1, len(rel_window) // 12)
        for s in rel_window[::stride]:
            t, ph, pos, vel, sp, sv, _, ee_v, pitch_deg = s
            print(f"  t={t:5.2f} {ph:<8s}  x={pos[0]:+.2f} vx={vel[0]:+.2f} z={pos[2]:.2f}  "
                  f"pitch={pitch_deg:+5.1f}°  "
                  f"shoulder={math.degrees(sp):+.0f}° ω={sv:+.1f}  "
                  f"v_ee=({ee_v[0]:+.2f},{ee_v[1]:+.2f},{ee_v[2]:+.2f})")

    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--runs-dir", type=str, default=None)
    ap.add_argument("--no-ff", action="store_true",
                    help="Disable arm-reaction torque feedforward")
    ap.add_argument("--no-gain-sched", action="store_true",
                    help="Disable adaptive attitude gains")
    ap.add_argument("--alpha", type=float, default=70.0,
                    help="Release arm angle in degrees (default 70)")
    ap.add_argument("--target-x", type=float, default=TARGET_LANDING_X,
                    help=f"Target landing x (default {TARGET_LANDING_X})")
    ap.add_argument("--target-z", type=float, default=0.025,
                    help="Target landing z (default 0.025 = floor; use 1.5 "
                         "for symmetric same-altitude throw)")
    args = ap.parse_args()
    sys.exit(run(gui=not args.headless, runs_dir=args.runs_dir,
                 use_ff=not args.no_ff, gain_sched=not args.no_gain_sched,
                 release_alpha_deg=args.alpha,
                 target_landing_x=args.target_x,
                 target_landing_z=args.target_z))


if __name__ == "__main__":
    main()
