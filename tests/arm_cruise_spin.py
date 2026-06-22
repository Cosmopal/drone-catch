"""M2 — cruise-while-spinning isolation test.

Drone starts at (-2, 0, 1.5), no ball. Cruises forward at 2 m/s. Once it
has reached cruise vx, the arm sweeps forward (-π/2 → +π/2 at 8 rad/s
with 200 ms ramp). After the sweep + brake, drone decelerates to a stop
at (+2, 0, 1.5).

Validates that the drone can hold altitude and heading while combining
forward translation with the arm-reaction transient. Pre-req for the
actual throw choreography.

Acceptance (slightly tighter than the demo would tolerate):
  - Z stays in [1.42, 1.58] throughout the sweep window
  - vx stays in [1.6, 2.4] m/s during sweep (no forward-velocity loss)
  - Roll within ±5° at all times
  - Pitch within ±15° during sweep (looser than M1 — cruise itself induces
    some pitch from velocity-tracking transient)
  - Final position within 0.15 m of (+2, 0, 1.5) after deceleration

Decel constraint: brake from 2 m/s in d=1 m → F = m·v²/(2d) = 1.25 N →
tilt ≈ 11.5°. So we plan the cruise-end target ≥ 1 m before the stopping
point.

Usage:
    python tests/arm_cruise_spin.py --headless --runs-dir runs/m2          # without FF
    python tests/arm_cruise_spin.py --headless --runs-dir runs/m2 --ff     # with FF
"""
from __future__ import annotations
import argparse
import sys
import os
import numpy as np
import pybullet as p

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sim_setup import (Logger, MarkerSet, VideoRecorder, Sim,
                       make_world, make_solo_drone, auto_run_paths,
                       rotate_runs, spawn_ball_at_ee, DT)
from config import DEFAULT as DEFAULT_GAME

START_POS = np.array([-2.0, 0.0, 1.5])
END_POS = np.array([+2.0, 0.0, 1.5])
CRUISE_VX = 2.0           # m/s
SPIN_OMEGA = 8.0          # rad/s arm sweep
RAMP_DURATION = 0.20      # arm-velocity ramp-up
SWEEP_END_ANGLE = +np.pi / 2

SETTLE_S = 1.0
CRUISE_TIMEOUT_S = 4.0    # outer cap on cruise-and-spin loop
DECEL_S = 2.0
SPIN_TRIGGER_VX = 1.5     # start arm sweep once drone has accelerated this far

# Tolerance bands per (with_ball, tight) combination. Tight (no settle gate)
# starts the sweep mid-accel, so accel pitch + sweep pitch overlap and we
# need looser pitch bounds. Ball multiplies arm reaction torque ~3.5×, so
# also looser bounds. Roll stays at 5° everywhere — sweep is purely in pitch.
TOLERANCES = {
    # (ball, tight): {pitch, roll, z_lo, z_hi, vx_lo, vx_hi, final}
    (False, False): dict(pitch=15.0, roll=5.0, z=(1.42, 1.58), vx=(1.6, 2.4), final=0.15),
    (True,  False): dict(pitch=18.0, roll=5.0, z=(1.40, 1.60), vx=(1.6, 2.4), final=0.20),
    (False, True):  dict(pitch=28.0, roll=5.0, z=(1.42, 1.58), vx=(1.5, 99.0), final=0.15),
    (True,  True):  dict(pitch=32.0, roll=5.0, z=(1.40, 1.60), vx=(1.5, 99.0), final=0.20),
}


def run(gui: bool, runs_dir: str | None, use_ff: bool,
        with_ball: bool, tight: bool, gain_sched: bool = False):
    tol = TOLERANCES[(with_ball, tight)]
    log_path, video_path = auto_run_paths(runs_dir)
    make_world(DEFAULT_GAME, gui=gui)
    drone = make_solo_drone(tuple(START_POS))
    drone.set_target(START_POS)
    drone.arm_reaction_ff = use_ff
    drone.attitude_gain_schedule = gain_sched

    if with_ball:
        p.stepSimulation()  # populate getLinkState for EE
        spawn_ball_at_ee(drone)

    markers = MarkerSet()
    markers.intent.set(END_POS)   # magenta = where we WANT to end up

    logger = Logger(log_path, decimate=4)
    video = VideoRecorder(video_path, every=8,
                          eye=(0.0, -4.0, 1.8), target=(0.0, 0.0, 1.5))
    sim = Sim([drone], markers, logger, video, gui=gui)

    worst = {
        "pitch_max_deg_sweep": 0.0,
        "roll_max_deg": 0.0,
        "z_min_sweep": +1e9,
        "z_max_sweep": -1e9,
        "vx_min_sweep": +1e9,
        "vx_max_sweep": -1e9,
    }
    full_trace = []

    def sample(phase):
        pos = drone.position()
        vel = drone.velocity()
        _, orn = p.getBasePositionAndOrientation(drone.body_id)
        roll, pitch, _ = p.getEulerFromQuaternion(orn)
        worst["roll_max_deg"] = max(worst["roll_max_deg"], abs(np.degrees(roll)))
        if phase == "sweep":
            worst["pitch_max_deg_sweep"] = max(worst["pitch_max_deg_sweep"],
                                               abs(np.degrees(pitch)))
            worst["z_min_sweep"] = min(worst["z_min_sweep"], pos[2])
            worst["z_max_sweep"] = max(worst["z_max_sweep"], pos[2])
            worst["vx_min_sweep"] = min(worst["vx_min_sweep"], vel[0])
            worst["vx_max_sweep"] = max(worst["vx_max_sweep"], vel[0])
        full_trace.append((sim.t, phase, pos.copy(), vel.copy(),
                           np.degrees(pitch), np.degrees(roll)))

    # Phase 1 — settle at start
    for _ in range(int(SETTLE_S / DT)):
        sim.tick("settle")
        sample("settle")

    # Phase 2+3 — cruise forward at CRUISE_VX with a *moving (carrot) target*:
    # each tick we set target = (start_x + cruise_vx · t_elapsed, 0, hover_z)
    # so the position controller sees a small steady-state error and the
    # vel feedforward dominates. Without this, a static target generates a
    # huge position error → drone accelerates past cruise_vx and oscillates.
    # The carrot is bounded so it never advances past END_POS - 1 m (we want
    # 1 m of decel runway at end of cruise — see paper calc on brake tilt).
    cruise_x_max = END_POS[0] - 1.0
    cruise_start_t = sim.t

    # Sweep starts once cruise has settled: pitch low + vx near target. We
    # also require a minimum time so the cruise has actually built up.
    sweep_started = False
    sweep_done = False
    sweep_start_t = None

    VEL_RAMP_S = 0.8           # ramp vel_target 0 → CRUISE_VX over this
    while (sim.t - cruise_start_t) < CRUISE_TIMEOUT_S:
        # Carrot target with ramped vel_target. Without the vel ramp, asking
        # for vx=2 m/s the moment cruise starts (drone at rest) gives a huge
        # vel error → kd term commands ~5 N → 39° tilt. Ramp lets the cascade
        # accelerate smoothly. Position carrot uses the integral of the same
        # ramp so target advances exactly as far as a real cruise at v(t).
        elapsed = sim.t - cruise_start_t
        if elapsed < VEL_RAMP_S:
            cur_vx = CRUISE_VX * (elapsed / VEL_RAMP_S)
            # ∫₀^t cur_vx dt = ½ CRUISE_VX·elapsed²/VEL_RAMP_S during ramp
            traveled = 0.5 * CRUISE_VX * elapsed * elapsed / VEL_RAMP_S
        else:
            cur_vx = CRUISE_VX
            traveled = (0.5 * CRUISE_VX * VEL_RAMP_S
                        + CRUISE_VX * (elapsed - VEL_RAMP_S))
        target_x = min(START_POS[0] + traveled, cruise_x_max)
        drone.set_target((target_x, 0.0, START_POS[2]),
                         vel=(cur_vx, 0.0, 0.0))

        # Trigger sweep:
        #   tight=False: wait for cruise to settle (pitch low + vx near target).
        #     Clean separation between accel transient and sweep transient.
        #   tight=True:  fire as soon as drone vx ≥ SPIN_TRIGGER_VX. Drone is
        #     still in its accel transient when sweep starts — closer to a
        #     real-world throw without aero drag to cap forward speed.
        vx = drone.velocity()[0]
        _, orn = p.getBasePositionAndOrientation(drone.body_id)
        _, pitch_now, _ = p.getEulerFromQuaternion(orn)
        if not sweep_started:
            if tight and vx >= SPIN_TRIGGER_VX:
                sweep_started = True
                sweep_start_t = sim.t
            elif (not tight and elapsed > 1.0
                  and abs(np.degrees(pitch_now)) < 5.0
                  and abs(vx - CRUISE_VX) < 0.3):
                sweep_started = True
                sweep_start_t = sim.t

        if sweep_started and not sweep_done:
            t_since = sim.t - sweep_start_t
            ramp = min(1.0, t_since / RAMP_DURATION)
            drone.spin_arm(shoulder_vel=SPIN_OMEGA * ramp, elbow_vel=0.0)
            phase = "sweep"
            s_pos, _, _, _ = drone.joint_states()
            if s_pos >= SWEEP_END_ANGLE:
                # Brake to ω=0 in velocity mode — STAY in velocity mode
                # afterward (do NOT switch to position-mode extend_arm,
                # which would yank the arm back with an FF-invisible
                # ~2 N·m torque kick → visible drone jerk especially with
                # ball). Velocity-mode hold at 0 keeps FF in sync.
                drone.spin_arm(shoulder_vel=0.0, elbow_vel=0.0)
                sweep_done = True
        else:
            phase = "cruise" if not sweep_done else "post_sweep"

        sim.tick(phase)
        sample(phase)

        # Exit when sweep has completed AND we've reached the carrot cap
        if sweep_done and target_x >= cruise_x_max - 1e-6 and \
                drone.position()[0] >= cruise_x_max - 0.2:
            break

    # Phase 4 — decelerate to END_POS, hold
    drone.set_target(END_POS, vel=(0.0, 0.0, 0.0))
    for _ in range(int(DECEL_S / DT)):
        sim.tick("decel")
        sample("decel")

    final_pos = drone.position()
    logger.close()
    video.close()
    p.disconnect()
    if runs_dir:
        from pathlib import Path
        rotate_runs(Path(runs_dir), keep=5)

    # ---- Report ----
    parts = ["WITH FF" if use_ff else "WITHOUT FF"]
    if with_ball: parts.append("BALL")
    if tight:    parts.append("TIGHT")
    label = " + ".join(parts)
    z_lo, z_hi = tol["z"]; vx_lo, vx_hi = tol["vx"]
    print(f"\n=== M2 cruise-while-spinning ({label}) ===")
    print(f"  sweep started:      {'yes' if sweep_started else 'no (drone never reached cruise vx)'}")
    print(f"  sweep completed:    {'yes' if sweep_done else 'no (timed out)'}")
    print(f"  pitch max (sweep):  {worst['pitch_max_deg_sweep']:.1f}°    (tol ≤ {tol['pitch']:.0f}°)")
    print(f"  roll max:           {worst['roll_max_deg']:.1f}°    (tol ≤ {tol['roll']:.0f}°)")
    print(f"  z range (sweep):    [{worst['z_min_sweep']:.3f}, {worst['z_max_sweep']:.3f}]   (tol [{z_lo}, {z_hi}])")
    print(f"  vx range (sweep):   [{worst['vx_min_sweep']:.2f}, {worst['vx_max_sweep']:.2f}]   (tol [{vx_lo}, {vx_hi}])")
    print(f"  final pos:          {final_pos.round(3).tolist()}    (tol ≤ {tol['final']} m from {END_POS.tolist()})")

    fails = []
    if not sweep_done:
        fails.append("sweep did not complete")
    if worst["pitch_max_deg_sweep"] > tol["pitch"]:
        fails.append(f"sweep pitch {worst['pitch_max_deg_sweep']:.1f}° > {tol['pitch']:.0f}°")
    if worst["roll_max_deg"] > tol["roll"]:
        fails.append(f"roll {worst['roll_max_deg']:.1f}° > {tol['roll']:.0f}°")
    if worst["z_min_sweep"] < z_lo or worst["z_max_sweep"] > z_hi:
        fails.append(f"z range [{worst['z_min_sweep']:.3f}, {worst['z_max_sweep']:.3f}] outside [{z_lo}, {z_hi}]")
    if worst["vx_min_sweep"] < vx_lo or worst["vx_max_sweep"] > vx_hi:
        fails.append(f"vx range [{worst['vx_min_sweep']:.2f}, {worst['vx_max_sweep']:.2f}] outside [{vx_lo}, {vx_hi}]")
    final_err = float(np.linalg.norm(final_pos - END_POS))
    if final_err > tol["final"]:
        fails.append(f"final pos error {final_err:.3f} m > {tol['final']} m")

    if fails:
        print("\nFAIL:")
        for f in fails:
            print(f"  - {f}")
    else:
        print("\nPASS")

    print("\nFull trace (every Nth sample):")
    stride = max(1, len(full_trace)//20)
    for s in full_trace[::stride]:
        t, ph, pos, vel, pitch, roll = s
        print(f"  t={t:5.2f} {ph:<10s} x={pos[0]:+.2f} z={pos[2]:.2f} vx={vel[0]:+.2f}"
              f" pitch={pitch:+5.1f}° roll={roll:+4.1f}°")

    return 0 if not fails else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--runs-dir", type=str, default=None)
    ap.add_argument("--ff", action="store_true",
                    help="Enable arm-reaction torque feedforward")
    ap.add_argument("--ball", action="store_true",
                    help="Spawn a ball at the EE and grasp before cruise")
    ap.add_argument("--tight", action="store_true",
                    help="Drop the cruise-settled gate; sweep fires as soon as "
                         "drone vx ≥ trigger threshold")
    ap.add_argument("--gain-sched", action="store_true",
                    help="Adapt kR_y, kw_y to current arm-pose pitch inertia")
    args = ap.parse_args()
    sys.exit(run(gui=not args.headless, runs_dir=args.runs_dir,
                 use_ff=args.ff, with_ball=args.ball, tight=args.tight,
                 gain_sched=args.gain_sched))


if __name__ == "__main__":
    main()
