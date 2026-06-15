"""GameConfig: single source of truth for scene geometry and per-game tunables.

Room dimensions, drone homes + play areas, cube position, hover height, ceiling
margin — all in one place so changing "where the game is played" only touches
this file. Drone PHYSICS (mass, max_thrust, controller gains) stays on the
Drone/CascadeController classes since those are object-intrinsic.

`world.setup(cfg)`, `Drone(home_pos=cfg.thrower_home, ...)`, planner inputs,
and marker placements all read from one `GameConfig` instance in main.py.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ArmConfig:
    """2-link arm parameters (mechanical + control). The URDF defines the
    geometry and inertia; this config covers the runtime tunables (motor
    limits, control gains, throw timing, release-trigger thresholds).
    """
    # Geometry (must match URDF — used by code that needs to know link lengths
    # for paper-math sanity checks, NOT for physics)
    upper_arm_len: float = 0.20
    forearm_len: float = 0.20

    # Joint angles for various stages. With the URDF axes:
    #   shoulder positive = forward sweep (about body -y)
    #   elbow=0 = forearm continues from upper_arm; elbow=π = forearm folded back
    #
    # NEUTRAL (folded): shoulder=0 (arm hangs straight down). Stable pendulum.
    # WOUND-UP: shoulder=-π/2 (arm points BACKWARD, opposite of throw direction).
    #   Drone starts in this pose. When spin commences, arm has 90° of pre-
    #   rotation runway before reaching the optimal release angle (~+47°),
    #   so the arm is at full ω by the time it sweeps through the release
    #   point — accel phase happens during the wound-up sweep.
    #
    # NOTE: elbow stays at 0 (extended) throughout. Folded position with
    # elbow=π puts EE above the shoulder, creating an inverted pendulum
    # that joint-motor PD can't stabilize.
    folded_shoulder: float = -1.5708   # -π/2 — wound-up at rest
    folded_elbow: float = 0.0
    extended_elbow: float = 0.0

    # Motor limits (per joint). PyBullet's setJointMotorControl2 uses `force`
    # as the torque cap when in POSITION_CONTROL or VELOCITY_CONTROL modes.
    # Bumped to 2 N·m: paper calc said 0.28 sufficient, but in practice the
    # arm needs to ramp from 0 to ~16 rad/s in ~250 ms (release window) which
    # demands α ≈ 64 rad/s² → τ = I·α = 0.014·64 ≈ 0.9 N·m. 2 N·m gives margin.
    arm_max_torque: float = 2.0

    # POSITION_CONTROL gains (used while holding folded or extended pose)
    arm_kp: float = 0.5
    arm_kd: float = 0.05

    # Throw timing
    spin_omega: float = 8.0          # arm shoulder velocity during throw (rad/s)
    spin_window_s: float = 0.6       # safety timeout — forced release after this
    min_spin_time: float = 0.15      # gate: don't release before arm has ramped
    follow_through_s: float = 0.10   # arm continues briefly after release

    # Release trigger (multi-condition — see plan section "Phase F")
    release_align_cos_min: float = 0.5   # gate: cos(v_ee, release_vel) > this (60° tolerance)
    release_mag_frac: float = 0.7        # fire when v_proj >= this · |release_vel|
    release_decline_threshold: float = 0.1   # m/s — past-peak detection

    # Drone tilt cap during throw window (raised from default 35° because brake
    # naturally pitches drone past that)
    throw_max_tilt_deg: float = 60.0

    # Effective rotational inertia of the arm about the shoulder, EXTENDED, no
    # ball. Used for feedforward arm-reaction torque compensation.
    # upper_arm rod-end (m·L²/3) + forearm parallel-axis + EE point-mass.
    # See M1 paper calc in plan.
    I_arm_extended: float = 0.004    # kg·m², no ball
    I_arm_with_ball: float = 0.014   # kg·m² (for reference; held-mass aware FF could use this)

    # ---- Caging gripper (quadrotor_gripper.urdf only) ----
    # Finger joint targets. Angle 0 = segment straight down; positive curls
    # inward (fingertips converge); negative splays outward (open mouth).
    finger_open_prox: float = -0.5   # rad — splayed to receive the ball
    finger_open_dist: float = -0.2
    finger_close_prox: float = 1.3   # rad — proximal wraps around
    finger_close_dist: float = 1.6   # rad — distal curls MORE, gets under the ball
    finger_close_torque: float = 0.5   # N·m motor force while closing/holding
    # Finger servo PD gains. Kept GENTLE on purpose: stiff finger motors
    # (high gain, or a velocity-drive branch) inject a dynamic disturbance
    # that — with the arm extended horizontally — excites the attitude
    # controller's yaw singularity and flips the drone. Soft position control
    # holds the pose without flapping. See docs/iteration_findings.md §13.
    finger_pos_gain: float = 0.6
    finger_vel_gain: float = 0.8


@dataclass(frozen=True)
class GameConfig:
    # Room — tighter than before so the drones use most of it during the
    # bowling throw (visible in the video instead of looking miniature).
    room_size: float = 8.0           # m, square footprint (x and y)
    wall_height: float = 3.0         # m, also = ceiling_z
    hover_z: float = 1.5             # default hover/catch altitude
    ceiling_margin: float = 0.4      # safety gap below ceiling for ball apex
    floor_margin: float = 0.8        # min backup z above floor — needs ~40 cm
                                     # for the extended arm, plus margin for
                                     # PD overshoot during descent.

    # Thrower (home + asymmetric play area + start position)
    thrower_home: tuple = (-2.0, 0.0, 1.5)
    thrower_start: tuple = (-2.0, 0.0, 1.5)
    thrower_play_min_offset: tuple = (-1.5, -1.0, -0.7)  # 1.5m back (less than before)
    thrower_play_max_offset: tuple = (+2.0, +1.0, +1.1)  # to centerline

    # Catcher (home + play area + start)
    catcher_home: tuple = (+2.0, 0.0, 1.5)
    catcher_start: tuple = (+2.0, 0.4, 1.1)
    catcher_play_min_offset: tuple = (-2.0, -1.0, -0.7)  # to centerline
    catcher_play_max_offset: tuple = (+1.5, +1.0, +1.1)

    # The cube the catcher picks up
    cube_pos: tuple = (1.5, -0.7, 0.05)

    # Planner brake_decel (m/s²) — empirically observed average during evade,
    # NOT the theoretical max. See docs/iteration_findings.md.
    brake_decel: float = 10.0

    # Arm sub-config
    arm: ArmConfig = field(default_factory=ArmConfig)

    @property
    def ceiling_z(self) -> float:
        return self.wall_height

    @property
    def max_apex(self) -> float:
        return self.ceiling_z - self.ceiling_margin

    def thrower_play_lo(self):
        import numpy as np
        return tuple(np.array(self.thrower_home) + np.array(self.thrower_play_min_offset))

    def thrower_play_hi(self):
        import numpy as np
        return tuple(np.array(self.thrower_home) + np.array(self.thrower_play_max_offset))


# Default game — tweak this single instance to change geometry.
DEFAULT = GameConfig()
