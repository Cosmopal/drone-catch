"""Throw planning: ballistic + drone-trajectory feasibility under hard
constraints, with multi-objective Pareto selection from feasible candidates.

Pipeline:
    1. Grid search over (release_x, vz)  →  candidate set
    2. Per candidate: derive vx (ballistic), backup_pos + t_ramp (matched-t
       single ramp), thrust, tilt, apex, arrival KE.
    3. Hard-constraint filter: ballistic, apex, thrust, tilt, backup-in-area.
    4. Pareto frontier over (arrival_KE↓, min_margin↑).
    5. Default policy: random pick from frontier.

Symmetric throw assumption (release_z == catcher_z): ball returns to release
height with same |v|, so arrival_KE = ½·m_ball·|release_vel|².
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import numpy as np

G = 9.81


@dataclass(frozen=True)
class PlannerInputs:
    catcher_xy: tuple              # (x, y) — where the ball should land
    hover_z: float                 # release/land z (symmetric throw)
    ceiling_z: float
    ceiling_margin: float          # safety gap below ceiling for apex
    backup_x_min: float            # back wall x (or thrower-area lo.x)
    play_x_max: float              # forward boundary of thrower's play area
                                   # (drone must brake to a stop within this)
    floor_margin: float            # min z for backup (above floor)
    release_x_range: tuple         # (lo, hi) for release_x within play area
    m_drone: float
    m_ball: float
    max_thrust: float              # N
    max_tilt_deg: float            # body-tilt cap (controller setting)

    @property
    def max_apex(self) -> float:
        return self.ceiling_z - self.ceiling_margin

    @property
    def m_total(self) -> float:
        return self.m_drone + self.m_ball

    # Empirically-observed average deceleration during evade. Theoretical
    # max at 90° tilt is max_thrust/m_drone ≈ 21.8 m/s², but the controller
    # spends ~120 ms rotating to the brake pose and during that transient
    # the brake is much weaker. Empirically the average over the brake
    # period is ~3-5 m/s². Using 5 keeps drone safely on its half — bumping
    # higher means overshoot. Tune higher when the controller gets a proper
    # trajectory tracker that pre-flips before release.
    brake_decel: float = 10.0


@dataclass(frozen=True)
class ThrowPlan:
    release_pos: tuple
    release_vel: tuple
    backup_pos: tuple
    t_ramp: float
    flight_time: float
    apex: float
    thrust_required: float         # N
    tilt_deg: float
    arrival_speed: float           # m/s, ball |v| at catcher
    arrival_ke: float              # J
    # Margins (positive = headroom, larger = more comfortable)
    thrust_margin: float           # 0..1 fraction
    tilt_margin: float             # 0..1 fraction
    apex_margin: float             # absolute m
    min_margin: float              # min of normalized margins (0..1)


def _evaluate(release_x: float, vz: float, inp: PlannerInputs) -> Optional[ThrowPlan]:
    """Compute the full plan for one (release_x, vz) sample.
    Returns None if any HARD constraint is violated."""
    release_z = inp.hover_z
    R = inp.catcher_xy[0] - release_x          # horizontal range
    if R <= 0 or vz <= 0:
        return None

    # Apex must be below max_apex
    apex = release_z + vz * vz / (2 * G)
    if apex > inp.max_apex:
        return None

    # Symmetric throw: ball returns to release_z after t_flight = 2*vz/g
    t_flight = 2 * vz / G
    vx = R / t_flight                          # ballistic for ball to land at catcher

    # Matched-t backup: largest t_ramp that fits backup in play area
    t_x_max = 2 * (release_x - inp.backup_x_min) / vx
    t_z_max = 2 * (release_z - inp.floor_margin) / vz
    t_ramp = min(t_x_max, t_z_max)
    if t_ramp <= 0:
        return None

    # Required acceleration during ramp
    ax = vx / t_ramp
    az = vz / t_ramp                           # additional accel above gravity
    # Total thrust per unit mass in world frame
    accel_total = float(np.hypot(ax, az + G))
    thrust = inp.m_total * accel_total
    if thrust > inp.max_thrust:
        return None

    tilt_deg = float(np.degrees(np.arctan2(ax, az + G)))
    if tilt_deg > inp.max_tilt_deg:
        return None

    # Evade brake constraint: after release the drone has horizontal velocity
    # vx and must brake to a stop within its play area (don't poach into
    # opponent territory). With max_tilt holding altitude:
    #   d_brake = vx² / (2·a_brake)
    # Constraint: release_x + d_brake ≤ play_x_max
    brake_distance = vx * vx / (2 * inp.brake_decel)
    if release_x + brake_distance > inp.play_x_max:
        return None

    # Arrival KE (symmetric throw): |v_at_catch| == |v_at_release|
    arrival_speed = float(np.hypot(vx, vz))
    arrival_ke = 0.5 * inp.m_ball * arrival_speed ** 2

    # Margins (normalized 0..1 where applicable; apex is absolute m)
    thrust_margin = (inp.max_thrust - thrust) / inp.max_thrust
    tilt_margin = (inp.max_tilt_deg - tilt_deg) / inp.max_tilt_deg
    apex_margin = inp.max_apex - apex
    apex_margin_norm = apex_margin / max(0.01, inp.max_apex - inp.hover_z)
    min_margin = min(thrust_margin, tilt_margin, apex_margin_norm)

    backup_pos = (
        release_x - 0.5 * vx * t_ramp,
        0.0,
        release_z - 0.5 * vz * t_ramp,
    )

    return ThrowPlan(
        release_pos=(release_x, 0.0, release_z),
        release_vel=(vx, 0.0, vz),
        backup_pos=backup_pos,
        t_ramp=t_ramp,
        flight_time=t_flight,
        apex=apex,
        thrust_required=thrust,
        tilt_deg=tilt_deg,
        arrival_speed=arrival_speed,
        arrival_ke=arrival_ke,
        thrust_margin=thrust_margin,
        tilt_margin=tilt_margin,
        apex_margin=apex_margin,
        min_margin=min_margin,
    )


def grid_search(inp: PlannerInputs, n_release: int = 30, n_vz: int = 30) -> list[ThrowPlan]:
    """Sweep (release_x, vz) over their feasible bounds and return all
    candidates that pass the hard-constraint filter."""
    rx_lo, rx_hi = inp.release_x_range
    vz_max = np.sqrt(2 * G * max(0.0, inp.max_apex - inp.hover_z))
    plans: list[ThrowPlan] = []
    for rx in np.linspace(rx_lo, rx_hi, n_release):
        for vz in np.linspace(0.5, vz_max, n_vz):
            p = _evaluate(float(rx), float(vz), inp)
            if p is not None:
                plans.append(p)
    return plans


def pareto_frontier(plans: list[ThrowPlan]) -> list[ThrowPlan]:
    """Return plans not dominated on (arrival_ke ↓, min_margin ↑).

    A dominates B iff A is at least as good as B on both objectives and
    strictly better on at least one.
    """
    nd: list[ThrowPlan] = []
    for p in plans:
        dominated = False
        for q in plans:
            if q is p:
                continue
            ke_le = q.arrival_ke <= p.arrival_ke
            mg_ge = q.min_margin >= p.min_margin
            strict = (q.arrival_ke < p.arrival_ke) or (q.min_margin > p.min_margin)
            if ke_le and mg_ge and strict:
                dominated = True
                break
        if not dominated:
            nd.append(p)
    return nd


def plan(inp: PlannerInputs, rng: np.random.Generator | None = None,
         prefer: str = "pareto") -> Optional[ThrowPlan]:
    """End-to-end: grid → filter → pick by `prefer`. Returns None if infeasible.

    prefer:
      "max_flight" — maximize ball flight time (highest arc, gives catcher
                     the most time to adjust — most "interesting" throw)
      "max_throw"  — flattest, fastest throw (max vx, arrives hardest)
      "min_ke"     — gentlest throw (lowest |v|, near-equivalent to max_flight
                     for symmetric throws since arc time correlates with low |v|)
      "max_margin" — most controller headroom
      "pareto"     — random pick from Pareto(KE↓, margin↑) frontier
    """
    candidates = grid_search(inp)
    if not candidates:
        return None
    rng = rng or np.random.default_rng()
    if prefer == "max_flight":
        return max(candidates, key=lambda p: p.flight_time)
    if prefer == "min_ke":
        return min(candidates, key=lambda p: p.arrival_ke)
    if prefer == "max_throw":
        return max(candidates, key=lambda p: p.release_vel[0])
    if prefer == "max_margin":
        return max(candidates, key=lambda p: p.min_margin)
    # default: Pareto frontier random pick
    frontier = pareto_frontier(candidates)
    return frontier[rng.integers(len(frontier))]


def diagnose_infeasibility(inp: PlannerInputs) -> str:
    """Walk the constraint chain to explain why no plan was found.
    For when grid_search returns []."""
    rx_lo, rx_hi = inp.release_x_range
    vz_max = np.sqrt(2 * G * max(0.0, inp.max_apex - inp.hover_z))
    if vz_max <= 0:
        return "ceiling too low — no valid vz at this hover height"
    # Try the most generous candidate: release as close to catcher as allowed
    rx = rx_hi
    R = inp.catcher_xy[0] - rx
    if R <= 0:
        return f"release_x_range max ({rx_hi}) is past catcher ({inp.catcher_xy[0]}) — no positive range to throw"
    # Try with apex-max vz (maximum vertical authority)
    vz = vz_max * 0.9
    vx = R / (2 * vz / G)
    t_x_max = 2 * (rx - inp.backup_x_min) / vx
    t_z_max = 2 * (inp.hover_z - inp.floor_margin) / vz
    t_ramp = min(t_x_max, t_z_max)
    ax, az = vx / t_ramp, vz / t_ramp
    thrust = inp.m_total * np.hypot(ax, az + G)
    tilt = np.degrees(np.arctan2(ax, az + G))
    if thrust > inp.max_thrust:
        return f"max_thrust {inp.max_thrust:.1f} N too low: cheapest throw needs {thrust:.1f} N"
    if tilt > inp.max_tilt_deg:
        return f"max_tilt {inp.max_tilt_deg:.1f}° too restrictive: cheapest throw needs {tilt:.1f}°"
    return "no obvious bottleneck — try widening grid resolution"
