"""Throw choreography: decompose a target release velocity into (drone
velocity at release, arm angular velocity, release arm angle).

The drone provides forward velocity `v_drone` along the throw direction;
the arm provides the rest via its tangent velocity at the EE. At release,
arm is at angle α from straight-down (in body frame), spinning at ω.

Ball velocity at release (in world frame, drone level) =
    drone_vel + arm_tip_vel_world
where arm_tip_vel_world = ω · L · (cos(α), 0, sin(α)) along throw direction.

So:
    ω · L · sin(α) = vz_target
    v_drone + ω · L · cos(α) = vx_target

Two unknowns (ω, α) are free but coupled. We pick α from config (default
π/3 — gives both vx and vz contributions; less timing-critical than π/2).
That fixes ω = vz_target / (L · sin(α)) and v_drone = vx_target − vz_target / tan(α).
"""
from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class ThrowDecomp:
    v_drone_horiz: float        # m/s, drone speed along throw direction at release
    v_drone_vec: np.ndarray     # 3-vec, full drone velocity at release
    omega: float                # rad/s, arm angular velocity at release
    release_alpha: float        # rad, arm angle from straight-down at release
    throw_dir: np.ndarray       # 3-vec, unit vector along throw direction (xy plane)
    expected_dvx_during_sweep: float  # m/s, predicted drone vx change during sweep


def decompose_throw(release_vel: np.ndarray, L_arm: float,
                    release_alpha: float = math.pi / 3,
                    expected_pitch_rad: float = 0.0) -> ThrowDecomp:
    """Given target release velocity (world-frame 3-vec) and arm length, compute
    the (v_drone, ω, α) that delivers the throw.

    `expected_pitch_rad`: predicted drone pitch at release (positive = nose
    down). Drone tilt rotates the body-frame arm tip velocity in world
    frame: an arm sweep that produces (vx_b, vz_b) in body frame becomes
    (cos(p)·vx_b + sin(p)·vz_b, ..., −sin(p)·vx_b + cos(p)·vz_b) in world.
    So if we want a specific world-frame v_ee, we need to plan the
    body-frame output anti-rotated. Empirically the M3 throw drone pitches
    +8° forward at release with cruise vx ~2.4 m/s — without this
    correction the throw lands ~30 cm short.

    Constraints checked:
      - vz_target > 0 (upward throw)
      - release_alpha ∈ (0, π/2] (arm at or before "forward" position)
      - resulting v_drone_horiz ≥ 0 (drone moves forward)
      - resulting ω feasible (≤ URDF cap of 18 rad/s)

    Raises ValueError if the throw isn't feasible at the given α.
    """
    release_vel = np.asarray(release_vel, dtype=float)
    # Anti-rotate the world-frame target velocity by -expected_pitch to get
    # the body-frame target the arm + drone should deliver. After drone tilt
    # rotates everything by +pitch in world, ball ends up at the right v.
    p = expected_pitch_rad
    if p != 0.0:
        cos_p = math.cos(p); sin_p = math.sin(p)
        vx_world = float(release_vel[0])
        vz_world = float(release_vel[2])
        # Anti-rotate: body = R_y(-p) · world
        vx_body = cos_p * vx_world - sin_p * vz_world
        vz_body = sin_p * vx_world + cos_p * vz_world
        # The y component is left unchanged (no roll/yaw correction here)
        release_vel = np.array([vx_body, release_vel[1], vz_body])
    vx_horiz = float(np.linalg.norm(release_vel[:2]))
    vz = float(release_vel[2])
    if vz <= 0:
        raise ValueError(f"vz must be positive (upward throw), got {vz:.2f}")
    if not (0 < release_alpha <= math.pi / 2):
        raise ValueError(f"release_alpha must be in (0, π/2], got {release_alpha:.3f}")

    omega = vz / (L_arm * math.sin(release_alpha))
    v_drone_horiz = vx_horiz - vz / math.tan(release_alpha)
    if v_drone_horiz < 0:
        raise ValueError(
            f"v_drone < 0 ({v_drone_horiz:.2f} m/s) — picked α too small for "
            f"this throw. Try a larger release_alpha."
        )
    if omega > 18.0:
        raise ValueError(
            f"omega {omega:.1f} rad/s exceeds URDF velocity cap (18). "
            f"Try larger release_alpha (closer to π/2) or smaller vz_target."
        )

    if vx_horiz > 1e-6:
        throw_dir = np.array([release_vel[0], release_vel[1], 0.0]) / vx_horiz
    else:
        throw_dir = np.array([1.0, 0.0, 0.0])
    v_drone_vec = throw_dir * v_drone_horiz

    # Predicted drone vx change during the sweep from -π/2 to release_alpha,
    # from the centripetal+tangential body-x force at constant ω. See
    # discussion of "sweep coupling": F_body_x = m_eff·ω²·sin(θ), integrated
    # over θ from -π/2 to α, divided by drone mass.
    # ∫ ω·sin(θ) dθ = ω·(-cos(α) + cos(-π/2)) = -ω·cos(α)
    # So Δvx = -m_eff·ω·cos(α) / m_drone.
    # m_eff = m_arm·r_arm_com + m_ball·L (point-mass approximation)
    M_ARM = 0.075
    M_BALL = 0.065
    M_DRONE = 0.625
    r_arm_com = L_arm / 2
    m_eff = M_ARM * r_arm_com + M_BALL * L_arm
    expected_dvx = -m_eff * omega * math.cos(release_alpha) / M_DRONE

    return ThrowDecomp(
        v_drone_horiz=v_drone_horiz,
        v_drone_vec=v_drone_vec,
        omega=omega,
        release_alpha=release_alpha,
        throw_dir=throw_dir,
        expected_dvx_during_sweep=expected_dvx,
    )


def cruise_speed_for_release(decomp: ThrowDecomp) -> float:
    """Cruise speed needed pre-sweep so that, after the sweep's natural
    translational push/pull, the drone arrives at release with the desired
    v_drone_horiz. We reduce the cascade's job by *anticipating* the sweep's
    effect rather than fighting it.

    For α = π/3, the sweep nets a slight backward push (the −π/2→0 backward
    half is bigger than the 0→π/3 forward half), so cruise speed is slightly
    higher than v_drone_horiz at release. For α = π/2, sweep is symmetric
    and cruise = release speed.
    """
    return decomp.v_drone_horiz - decomp.expected_dvx_during_sweep
