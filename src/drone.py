"""Quadrotor body wrapper: URDF loading, state queries, target setting,
arm joint motor control, and a constraint-based gripper at the end-effector.

The control law itself lives in `controller.py` (`CascadeController`). This
class stitches together state queries, the controller call, the PyBullet
force/torque application, AND the per-joint arm motor commands.

Forces/torques applied directly to the base link via PyBullet's external
force/torque API. Arm joints driven via setJointMotorControl2 (PyBullet's
PD servo) — POSITION_CONTROL while holding a pose, VELOCITY_CONTROL during
throw windup. Gripper attaches the held body to the end_effector LINK so
the ball follows the arm tip, not the drone COM.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import pybullet as p

from controller import CascadeController
from config import ArmConfig

ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
URDF = os.path.join(ASSETS, "quadrotor.urdf")

MASS = 0.625  # full URDF mass: base 0.546 + 4 props (4e-3) + arm (~0.075)
G = 9.81


@dataclass
class Drone:
    start_pos: tuple
    start_yaw: float = 0.0
    home_pos: Optional[tuple] = None
    play_area_min_offset: tuple = (-1.5, -1.5, -1.0)
    play_area_max_offset: tuple = (+1.5, +1.5, +1.0)
    controller: CascadeController = field(default_factory=CascadeController)
    arm_cfg: ArmConfig = field(default_factory=ArmConfig)
    body_id: int = field(init=False)
    target: np.ndarray = field(init=False)
    vel_target: np.ndarray = field(init=False)
    yaw_target: float = field(init=False)
    held_constraint: Optional[int] = field(default=None, init=False)
    # arm joint indices, end-effector link index — discovered at __post_init__
    shoulder_joint: int = field(init=False)
    elbow_joint: int = field(init=False)
    ee_link: int = field(init=False)
    # current arm command — applied each step via _apply_arm()
    _arm_mode: str = field(default="hold", init=False)
    _arm_targets: dict = field(default_factory=dict, init=False)

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

        # Discover joint + link indices from the URDF
        self.shoulder_joint = -1
        self.elbow_joint = -1
        self.ee_link = -1
        for j in range(p.getNumJoints(self.body_id)):
            info = p.getJointInfo(self.body_id, j)
            jname = info[1].decode()
            child_link_name = info[12].decode()
            if jname == "shoulder_joint":
                self.shoulder_joint = j
            elif jname == "elbow_joint":
                self.elbow_joint = j
            if child_link_name == "end_effector":
                self.ee_link = j  # link index == joint index whose child is this link
        assert self.shoulder_joint >= 0 and self.elbow_joint >= 0 and self.ee_link >= 0, \
            f"URDF missing expected joints/links: shoulder={self.shoulder_joint} " \
            f"elbow={self.elbow_joint} ee={self.ee_link}"

        # Initial pose: arm folded, holding pose with motor PD
        p.resetJointState(self.body_id, self.shoulder_joint,
                          targetValue=self.arm_cfg.folded_shoulder, targetVelocity=0.0)
        p.resetJointState(self.body_id, self.elbow_joint,
                          targetValue=self.arm_cfg.folded_elbow, targetVelocity=0.0)
        self._arm_mode = "hold"
        self._arm_targets = {
            "shoulder_pos": self.arm_cfg.folded_shoulder,
            "elbow_pos": self.arm_cfg.folded_elbow,
            "shoulder_vel": 0.0,
            "elbow_vel": 0.0,
        }

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

    def ee_state(self):
        """End-effector world state. Returns (pos, orn, lin_vel, ang_vel).
        Indices into getLinkState's 8-tuple: 4=worldLinkFramePosition,
        5=worldLinkFrameOrientation, 6=worldLinkLinearVelocity (with
        computeLinkVelocity=1), 7=worldLinkAngularVelocity."""
        s = p.getLinkState(self.body_id, self.ee_link,
                           computeLinkVelocity=1, computeForwardKinematics=1)
        return np.array(s[4]), s[5], np.array(s[6]), np.array(s[7])

    def gripper_world_position(self) -> np.ndarray:
        return self.ee_state()[0]

    def gripper_world_velocity(self) -> np.ndarray:
        """Velocity of the end-effector link in world frame. PyBullet computes
        this including the contribution from arm joint motion AND drone body
        motion AND drone rotation — so this is the *true* velocity the ball
        would inherit at release."""
        return self.ee_state()[2]

    def joint_states(self):
        """Return (shoulder_pos, shoulder_vel, elbow_pos, elbow_vel)."""
        s = p.getJointState(self.body_id, self.shoulder_joint)
        e = p.getJointState(self.body_id, self.elbow_joint)
        return s[0], s[1], e[0], e[1]

    def _system_com_world(self) -> np.ndarray:
        """World-frame position of the multi-body system center of mass,
        including base link + all child links + the held body (if any).
        Used to apply thrust at the actual CoM rather than the base link
        origin — without this, an articulated arm AND/OR a held ball at the
        end-effector shifts the system CoM, creating a spurious torque on
        the body every step (drone tilts and drifts).
        """
        base_m = p.getDynamicsInfo(self.body_id, -1)[0]
        base_pos = np.array(p.getBasePositionAndOrientation(self.body_id)[0])
        total_m = base_m
        com_sum = base_m * base_pos
        for j in range(p.getNumJoints(self.body_id)):
            link_m = p.getDynamicsInfo(self.body_id, j)[0]
            if link_m <= 0:
                continue
            link_com_world = np.array(p.getLinkState(self.body_id, j)[0])
            total_m += link_m
            com_sum += link_m * link_com_world
        # Include held body (ball/cube) — it's rigidly constrained and its
        # gravity acts at its own location, NOT the drone's COM.
        if self.held_constraint is not None:
            info = p.getConstraintInfo(self.held_constraint)
            child_body = info[2]
            held_m = p.getDynamicsInfo(child_body, -1)[0]
            held_pos = np.array(p.getBasePositionAndOrientation(child_body)[0])
            total_m += held_m
            com_sum += held_m * held_pos
        return com_sum / total_m

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

    def hold_arm(self, shoulder_pos: float, elbow_pos: float):
        """Position-mode servo: arm tracks the given joint angles."""
        self._arm_mode = "hold"
        self._arm_targets["shoulder_pos"] = float(shoulder_pos)
        self._arm_targets["elbow_pos"] = float(elbow_pos)

    def fold_arm(self):
        self.hold_arm(self.arm_cfg.folded_shoulder, self.arm_cfg.folded_elbow)

    def extend_arm(self):
        """Hold the arm extended straight down (shoulder=0, elbow=0)."""
        self.hold_arm(0.0, self.arm_cfg.extended_elbow)

    def spin_arm(self, shoulder_vel: float, elbow_vel: float = 0.0):
        """Velocity-mode servo: arm spins at the given joint rates."""
        self._arm_mode = "spin"
        self._arm_targets["shoulder_vel"] = float(shoulder_vel)
        self._arm_targets["elbow_vel"] = float(elbow_vel)

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

        # Body force: thrust along body-z, applied at the SYSTEM CoM (not the
        # base link origin). With the arm articulated and able to swing far
        # from base, system CoM shifts as joints move — applying force at
        # base origin in that case generates a spurious torque proportional
        # to the CoM offset. Computing system CoM each step and using
        # WORLD_FRAME with the explicit world-frame application point
        # eliminates this. (See `_system_com_world` docstring.)
        force_world = R @ np.array([0.0, 0.0, thrust_mag])
        com_world = self._system_com_world()
        p.applyExternalForce(self.body_id, -1,
                             force_world.tolist(), com_world.tolist(),
                             p.WORLD_FRAME)
        p.applyExternalTorque(self.body_id, -1, torque.tolist(), p.LINK_FRAME)

        # Arm motor commands (after body controller — they're independent)
        self._apply_arm()

    def _apply_arm(self):
        """Drive shoulder + elbow joints based on current _arm_mode."""
        cfg = self.arm_cfg
        if self._arm_mode == "hold":
            p.setJointMotorControl2(self.body_id, self.shoulder_joint,
                p.POSITION_CONTROL,
                targetPosition=self._arm_targets["shoulder_pos"],
                positionGain=cfg.arm_kp, velocityGain=cfg.arm_kd,
                force=cfg.arm_max_torque)
            p.setJointMotorControl2(self.body_id, self.elbow_joint,
                p.POSITION_CONTROL,
                targetPosition=self._arm_targets["elbow_pos"],
                positionGain=cfg.arm_kp, velocityGain=cfg.arm_kd,
                force=cfg.arm_max_torque)
        elif self._arm_mode == "spin":
            p.setJointMotorControl2(self.body_id, self.shoulder_joint,
                p.VELOCITY_CONTROL,
                targetVelocity=self._arm_targets["shoulder_vel"],
                force=cfg.arm_max_torque)
            p.setJointMotorControl2(self.body_id, self.elbow_joint,
                p.VELOCITY_CONTROL,
                targetVelocity=self._arm_targets["elbow_vel"],
                force=cfg.arm_max_torque)

    # ------------ "arm" gripper via constraint at end-effector link ------------
    def grasp(self, target_body: int, max_distance: float = 0.15) -> bool:
        """Attach `target_body` to the end-effector link via a fixed constraint.
        Distance is checked from the EE world position (NOT drone COM).
        """
        if self.held_constraint is not None:
            return True
        ee_pos = self.gripper_world_position()
        their_pos, _ = p.getBasePositionAndOrientation(target_body)
        if np.linalg.norm(ee_pos - np.array(their_pos)) > max_distance:
            return False
        self.held_constraint = p.createConstraint(
            parentBodyUniqueId=self.body_id, parentLinkIndex=self.ee_link,
            childBodyUniqueId=target_body, childLinkIndex=-1,
            jointType=p.JOINT_FIXED, jointAxis=[0, 0, 0],
            parentFramePosition=[0, 0, 0],   # at EE link origin (small sphere center)
            childFramePosition=[0, 0, 0],    # at child body's COM
        )
        return True

    def _held_mass(self) -> float:
        if self.held_constraint is None:
            return 0.0
        info = p.getConstraintInfo(self.held_constraint)
        child_body = info[2]
        return float(p.getDynamicsInfo(child_body, -1)[0])

    def release(self, throw_velocity=None):
        """Release the held body. By default it inherits the EE world velocity
        (PyBullet's `getLinkState` already accounts for arm + body motion).
        Pass `throw_velocity` to override."""
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
