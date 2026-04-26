"""Quadrotor with cascaded position+attitude control.

Outer loop:  position PD -> desired thrust vector (world frame).
Inner loop:  Lee-style attitude controller (geometric SO(3) PD)
             tracks the orientation that aligns body-z with the thrust vector
             and body-yaw with `yaw_target`. Outputs body-frame torques.

Forces and torques are applied directly to the base via PyBullet's external
force/torque API. Still no rotor mixing or motor dynamics — when porting to
real hardware, replace the (thrust, torque) command with rotor RPMs through
a mixer matrix.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import pybullet as p

ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
URDF = os.path.join(ASSETS, "quadrotor.urdf")

MASS = 0.504  # base 0.5 + 4 prop disks at 0.001 each (matches URDF total)
G = 9.81


@dataclass
class Drone:
    start_pos: tuple
    start_yaw: float = 0.0
    # play-area soft bound (centered on home_pos); set_target clips to this box
    home_pos: Optional[tuple] = None  # defaults to start_pos in __post_init__
    play_area_half_extents: tuple = (1.5, 1.5, 1.0)
    # outer (position) loop
    kp: np.ndarray = field(default_factory=lambda: np.array([6.0, 6.0, 12.0]))
    kd: np.ndarray = field(default_factory=lambda: np.array([4.0, 4.0, 6.0]))
    # inner (attitude) loop — sized for I ≈ 2-4 mN·m·s²
    kR: np.ndarray = field(default_factory=lambda: np.array([0.30, 0.30, 0.15]))
    kw: np.ndarray = field(default_factory=lambda: np.array([0.05, 0.05, 0.03]))
    max_thrust: float = 25.0
    max_torque: float = 0.5
    max_tilt_deg: float = 35.0  # cap on desired body tilt from vertical
    body_id: int = field(init=False)
    target: np.ndarray = field(init=False)
    vel_target: np.ndarray = field(init=False)
    yaw_target: float = field(init=False)
    held_constraint: Optional[int] = field(default=None, init=False)

    GRIPPER_OFFSET = np.array([0.0, 0.0, -0.08])

    def __post_init__(self):
        q0 = p.getQuaternionFromEuler([0.0, 0.0, self.start_yaw])
        self.body_id = p.loadURDF(URDF,
                                  basePosition=list(self.start_pos),
                                  baseOrientation=q0)
        if self.home_pos is None:
            self.home_pos = tuple(self.start_pos)
        self.home_pos = np.array(self.home_pos, dtype=float)
        self.play_area_half_extents = np.array(self.play_area_half_extents, dtype=float)
        self.target = np.array(self.start_pos, dtype=float)
        self.vel_target = np.zeros(3)
        self.yaw_target = float(self.start_yaw)

    # ------------ state ------------
    def position(self) -> np.ndarray:
        pos, _ = p.getBasePositionAndOrientation(self.body_id)
        return np.array(pos)

    def orientation(self):
        _, q = p.getBasePositionAndOrientation(self.body_id)
        return q

    def velocity(self) -> np.ndarray:
        v, _ = p.getBaseVelocity(self.body_id)
        return np.array(v)

    def angular_velocity(self) -> np.ndarray:
        _, w = p.getBaseVelocity(self.body_id)
        return np.array(w)

    # ------------ control ------------
    def set_target(self, xyz, vel=None):
        """Set position and (optionally) velocity feed-forward target.
        Position is clipped to the drone's play area (soft boundary)."""
        xyz = np.array(xyz, dtype=float)
        lo = self.home_pos - self.play_area_half_extents
        hi = self.home_pos + self.play_area_half_extents
        self.target = np.clip(xyz, lo, hi)
        self.vel_target = (np.array(vel, dtype=float) if vel is not None
                           else np.zeros(3))

    def go_home(self):
        self.set_target(self.home_pos, vel=[0, 0, 0])

    def set_yaw_target(self, psi: float):
        self.yaw_target = float(psi)

    def step(self):
        pos = self.position()
        vel = self.velocity()
        R = np.array(p.getMatrixFromQuaternion(self.orientation())).reshape(3, 3)
        omega = self.angular_velocity()

        # --- Outer loop: desired thrust vector in world frame ---
        err = self.target - pos
        derr = self.vel_target - vel
        # Gravity feed-forward includes any held body's mass so we don't droop
        # while carrying. (Constraint couples the two bodies rigidly, so the
        # drone has to support both.)
        total_mass = MASS + self._held_mass()
        thrust_vec = (MASS * (self.kp * err + self.kd * derr)
                      + total_mass * np.array([0.0, 0.0, G]))

        # Cap desired body tilt: when a big horizontal target makes the desired
        # thrust vector mostly horizontal, the attitude cascade would tilt the
        # drone past 90° and lose all vertical authority → drone falls. Real
        # autopilots clip the horizontal component so tilt stays bounded.
        tx, ty, tz = thrust_vec
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
        x_c = np.array([np.cos(self.yaw_target), np.sin(self.yaw_target), 0.0])
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

        # --- Apply: thrust is along body-z by construction; use LINK_FRAME so
        # `posObj=[0,0,0]` correctly means the body's COM (in WORLD_FRAME it
        # would mean the world origin, which generates a spurious torque). ---
        p.applyExternalForce(self.body_id, -1,
                             [0.0, 0.0, thrust_mag], [0, 0, 0], p.LINK_FRAME)
        p.applyExternalTorque(self.body_id, -1, torque.tolist(), p.LINK_FRAME)

    # ------------ "arm" / gripper via constraint ------------
    def grasp(self, target_body: int, max_distance: float = 0.15) -> bool:
        if self.held_constraint is not None:
            return True
        my_pos = self.position()
        their_pos, _ = p.getBasePositionAndOrientation(target_body)
        if np.linalg.norm(my_pos - np.array(their_pos)) > max_distance:
            return False
        self.held_constraint = p.createConstraint(
            parentBodyUniqueId=self.body_id, parentLinkIndex=-1,
            childBodyUniqueId=target_body, childLinkIndex=-1,
            jointType=p.JOINT_FIXED, jointAxis=[0, 0, 0],
            parentFramePosition=self.GRIPPER_OFFSET.tolist(),
            childFramePosition=[0, 0, 0],
        )
        return True

    def _held_mass(self) -> float:
        if self.held_constraint is None:
            return 0.0
        info = p.getConstraintInfo(self.held_constraint)
        child_body = info[2]
        return float(p.getDynamicsInfo(child_body, -1)[0])

    def gripper_world_velocity(self) -> np.ndarray:
        """Velocity of the gripper attachment point in the world frame."""
        R = np.array(p.getMatrixFromQuaternion(self.orientation())).reshape(3, 3)
        r_world = R @ self.GRIPPER_OFFSET
        return self.velocity() + np.cross(self.angular_velocity(), r_world)

    def release(self, throw_velocity=None):
        """Release the held body. By default it inherits the gripper's world
        velocity (drone linear + omega x r). Pass `throw_velocity` to override.
        """
        if self.held_constraint is None:
            return None
        info = p.getConstraintInfo(self.held_constraint)
        child_body = info[2]
        v = list(throw_velocity) if throw_velocity is not None \
            else self.gripper_world_velocity().tolist()
        p.removeConstraint(self.held_constraint)
        self.held_constraint = None
        p.resetBaseVelocity(child_body, linearVelocity=v)
        return child_body
