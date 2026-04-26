"""Cascaded position + attitude controller for a quadrotor.

Outer loop:  position PD -> desired thrust vector (world frame),
             tilt-clipped so we never lose vertical authority.
Inner loop:  Lee-style geometric SO(3) attitude controller. Builds R_des
             from the desired thrust direction + a yaw target, then computes
             body-frame torques from the SO(3) error.

The controller is intentionally stateless — pass current state and target in,
get (thrust_along_body_z, body_torque) out. Drone wraps state queries and
PyBullet force application around it.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np


@dataclass
class CascadeController:
    # outer (position) loop
    kp: np.ndarray = field(default_factory=lambda: np.array([6.0, 6.0, 12.0]))
    kd: np.ndarray = field(default_factory=lambda: np.array([4.0, 4.0, 6.0]))
    # inner (attitude) loop — sized for I ≈ 2-4 mN·m·s²
    kR: np.ndarray = field(default_factory=lambda: np.array([0.30, 0.30, 0.15]))
    kw: np.ndarray = field(default_factory=lambda: np.array([0.05, 0.05, 0.03]))
    max_thrust: float = 12.0
    max_torque: float = 0.5
    max_tilt_deg: float = 35.0  # cap on desired body tilt from vertical

    def compute(self, *, pos, vel, R, omega, target, vel_target, yaw_target,
                held_mass, MASS, G):
        """Return (thrust_mag_along_body_z, torque_body_3vec)."""
        pos = np.asarray(pos, dtype=float)
        vel = np.asarray(vel, dtype=float)
        omega = np.asarray(omega, dtype=float)
        target = np.asarray(target, dtype=float)
        vel_target = np.asarray(vel_target, dtype=float)

        # --- Outer loop: desired thrust vector in world frame ---
        err = target - pos
        derr = vel_target - vel
        # Gravity feed-forward includes any held body's mass so we don't droop
        # while carrying. (Constraint couples the two bodies rigidly, so the
        # drone has to support both.)
        total_mass = MASS + held_mass
        thrust_vec = (MASS * (self.kp * err + self.kd * derr)
                      + total_mass * np.array([0.0, 0.0, G]))

        # Cap desired body tilt: when a big horizontal target makes the desired
        # thrust vector mostly horizontal, the attitude cascade would tilt the
        # drone past 90° and lose all vertical authority → drone falls. Real
        # autopilots clip the horizontal component so tilt stays bounded.
        # When max_tilt_deg < 90 we also enforce a vertical-thrust floor (drone
        # always pushes up at least half-gravity-worth) so the controller can't
        # command the body into the no-vertical-authority regime. When evade
        # mode raises max_tilt to ≥90°, we drop that floor so the drone CAN
        # command thrust pointing down (flip past 90° to brake hard while
        # descending).
        tx, ty, tz = thrust_vec
        if self.max_tilt_deg < 90:
            min_tz = 0.5 * total_mass * G
            tz = max(tz, min_tz)
            max_h = tz * np.tan(np.deg2rad(self.max_tilt_deg))
            h = float(np.hypot(tx, ty))
            if h > max_h:
                s = max_h / h
                tx *= s; ty *= s
        thrust_vec = np.array([tx, ty, tz])

        # Project onto current body-z (the only axis we can push along)
        body_z = R @ np.array([0.0, 0.0, 1.0])
        thrust_mag = float(np.dot(thrust_vec, body_z))
        thrust_mag = max(0.0, min(thrust_mag, self.max_thrust))

        # --- Inner loop: build R_des from desired thrust direction + yaw ---
        n = np.linalg.norm(thrust_vec)
        z_des = thrust_vec / n if n > 1e-6 else np.array([0.0, 0.0, 1.0])
        x_c = np.array([np.cos(yaw_target), np.sin(yaw_target), 0.0])
        y_des = np.cross(z_des, x_c)
        ny = np.linalg.norm(y_des)
        y_des = y_des / ny if ny > 1e-6 else np.array([0.0, 1.0, 0.0])
        x_des = np.cross(y_des, z_des)
        R_des = np.column_stack([x_des, y_des, z_des])

        # Lee attitude error: vee( 0.5 (R_des^T R - R^T R_des) )
        skew = 0.5 * (R_des.T @ R - R.T @ R_des)
        e_R = np.array([skew[2, 1], skew[0, 2], skew[1, 0]])
        omega_body = R.T @ omega
        torque = -self.kR * e_R - self.kw * omega_body

        tn = np.linalg.norm(torque)
        if tn > self.max_torque:
            torque = torque * (self.max_torque / tn)

        return thrust_mag, torque
