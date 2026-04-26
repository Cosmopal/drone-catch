"""Quadrotor body wrapper: URDF loading, state queries, target setting,
and a constraint-based "arm" (grasp/release).

The control law itself lives in `controller.py` (`CascadeController`). This
class just stitches together state queries, the controller call, and the
PyBullet force/torque application.

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

from controller import CascadeController

ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
URDF = os.path.join(ASSETS, "quadrotor.urdf")

MASS = 0.55   # 500g chassis + 50g arm budget (matches URDF base 0.546 + 4 props)
G = 9.81


@dataclass
class Drone:
    start_pos: tuple
    start_yaw: float = 0.0
    # play-area soft bound (set_target clips to this box). Specified as offsets
    # from home_pos so areas can be asymmetric (e.g. lots of room behind for a
    # backup runway, less room in front past the opponent).
    home_pos: Optional[tuple] = None  # defaults to start_pos in __post_init__
    play_area_min_offset: tuple = (-1.5, -1.5, -1.0)  # lo corner offset from home
    play_area_max_offset: tuple = (+1.5, +1.5, +1.0)  # hi corner offset from home
    controller: CascadeController = field(default_factory=CascadeController)
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
        self.play_area_min_offset = np.array(self.play_area_min_offset, dtype=float)
        self.play_area_max_offset = np.array(self.play_area_max_offset, dtype=float)
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
        lo = self.home_pos + self.play_area_min_offset
        hi = self.home_pos + self.play_area_max_offset
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

        thrust_mag, torque = self.controller.compute(
            pos=pos, vel=vel, R=R, omega=omega,
            target=self.target, vel_target=self.vel_target,
            yaw_target=self.yaw_target,
            held_mass=self._held_mass(),
            MASS=MASS, G=G,
        )

        # Apply: thrust is along body-z by construction; use LINK_FRAME so
        # `posObj=[0,0,0]` correctly means the body's COM (in WORLD_FRAME it
        # would mean the world origin, which generates a spurious torque).
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
