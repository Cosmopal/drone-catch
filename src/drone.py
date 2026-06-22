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
DT = 1.0 / 240.0  # sim timestep, must match world.setup()


@dataclass
class Drone:
    start_pos: tuple
    start_yaw: float = 0.0
    urdf_path: Optional[str] = None   # default: plain quadrotor (no fingers)
    home_pos: Optional[tuple] = None
    play_area_min_offset: tuple = (-1.5, -1.5, -1.0)
    play_area_max_offset: tuple = (+1.5, +1.5, +1.0)
    controller: CascadeController = field(default_factory=CascadeController)
    arm_cfg: ArmConfig = field(default_factory=ArmConfig)
    body_id: int = field(init=False)
    mass: float = field(init=False)   # actual total model mass (base + links)
    target: np.ndarray = field(init=False)
    vel_target: np.ndarray = field(init=False)
    yaw_target: float = field(init=False)
    held_constraint: Optional[int] = field(default=None, init=False)
    # arm joint indices, end-effector link index — discovered at __post_init__
    shoulder_joint: int = field(init=False)
    elbow_joint: int = field(init=False)
    ee_link: int = field(init=False)
    # finger joints (only present with the gripper URDF). Each entry is
    # (prox_joint, dist_joint); link indices == joint indices in PyBullet.
    finger_joints: list = field(default_factory=list, init=False)
    finger_links: list = field(default_factory=list, init=False)
    _gripper_cmd: Optional[dict] = field(default=None, init=False)
    # current arm command — applied each step via _apply_arm()
    _arm_mode: str = field(default="hold", init=False)
    _arm_targets: dict = field(default_factory=dict, init=False)
    # Arm-reaction feedforward toggle. When True, drone predicts the body
    # torque that comes from accelerating the arm and adds the negation to
    # the cascade torque output, so the cascade doesn't have to react to a
    # disturbance it could have predicted. See M1 in plan.
    arm_reaction_ff: bool = False
    _shoulder_vel_cmd_prev: float = field(default=0.0, init=False)
    # Translational feedforward for body-z disturbance from arm dynamics.
    # During sweep, F_body_z = −m_eff·(α·sin(θ) + ω²·cos(θ)) — peaks downward
    # at θ=0 (mid-sweep), pulls drone down. We add the canceling thrust as
    # a world-frame z-force, separate from the cascade's thrust output.
    arm_translational_ff_z: bool = False
    # Finger-reaction feedforward toggle (additive, default OFF). When True, the
    # drone predicts the net body torque produced by the gripper's finger-joint
    # motor torques during a close and pre-cancels it on the body — the same
    # idea as arm_reaction_ff, applied to the hand. A constant-torque ("active"/
    # tendon) close never stops applying torque, so on a floating base it reacts
    # on the airframe (docs/concepts/13, iteration_findings §24 — it flipped the
    # drone). Feeding it forward lets the body absorb it like it already absorbs
    # the ball's momentum. See _finger_reaction_ff_body_torque.
    finger_reaction_ff: bool = False
    # When True, recompute kR_y and kw_y each step from the current arm pose
    # + held-mass-induced pitch inertia, so the cascade stays at its design
    # ω_n and ζ across configurations. Off by default so static-gain
    # behavior is preserved for the existing tests.
    attitude_gain_schedule: bool = False
    # Design points for gain scheduling — these match the body-only
    # numerical defaults (kR=0.30, kw=0.05, I≈0.0025): ω_n ≈ 11 rad/s,
    # ζ ≈ 0.91. We recompute kR, kw from these when scheduling is on.
    target_omega_n_y: float = 11.0
    target_zeta_y: float = 0.91

    def __post_init__(self):
        q0 = p.getQuaternionFromEuler([0.0, 0.0, self.start_yaw])
        self.body_id = p.loadURDF(self.urdf_path or URDF,
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
        fseg = {}   # {finger_id: {seg_id: joint_index}}
        for j in range(p.getNumJoints(self.body_id)):
            info = p.getJointInfo(self.body_id, j)
            jname = info[1].decode()
            child_link_name = info[12].decode()
            if jname == "shoulder_joint":
                self.shoulder_joint = j
            elif jname == "elbow_joint":
                self.elbow_joint = j
            elif jname.startswith("finger") and "_seg" in jname:
                # finger{i}_seg{k}_joint — N fingers, M segments each
                fid = int(jname[len("finger"):].split("_")[0])
                sid = int(jname.split("_seg")[1].split("_")[0])
                fseg.setdefault(fid, {})[sid] = j
            if child_link_name == "end_effector":
                self.ee_link = j  # link index == joint index whose child is this link
        assert self.shoulder_joint >= 0 and self.elbow_joint >= 0 and self.ee_link >= 0, \
            f"URDF missing expected joints/links: shoulder={self.shoulder_joint} " \
            f"elbow={self.elbow_joint} ee={self.ee_link}"
        # finger_joints[i] = [seg0_joint, seg1_joint, ...] (proximal→distal).
        # Link index == joint index of the joint whose child is that link.
        for fid in sorted(fseg):
            segs = [fseg[fid][sid] for sid in sorted(fseg[fid])]
            self.finger_joints.append(segs)
            self.finger_links.extend(segs)

        # Actual total mass from the loaded model (base + all links). The
        # gripper URDF adds finger mass, so a hardcoded constant would make
        # gravity feedforward undershoot → steady-state sag. Compute it.
        self.mass = p.getDynamicsInfo(self.body_id, -1)[0]
        for j in range(p.getNumJoints(self.body_id)):
            self.mass += p.getDynamicsInfo(self.body_id, j)[0]

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
        # Fingers (gripper URDF only): start splayed open and hold there.
        if self.finger_joints:
            for segs in self.finger_joints:
                for k, j in enumerate(segs):
                    p.resetJointState(self.body_id, j,
                                      targetValue=self.arm_cfg.finger_open[k])
            self._gripper_cmd = {"mode": "open"}

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

    def hold_arm(self, shoulder_pos: float, elbow_pos: float,
                 shoulder_vel: float = 0.0, elbow_vel: float = 0.0,
                 torque_cap: float | None = None):
        """Position-mode servo: arm tracks the given joint angles, with an
        optional joint-VELOCITY feedforward and an optional torque CAP.

        The velocity feedforward lets the arm tip move at a commanded velocity
        (via the Jacobian, `arm_kinematics.ik_velocity`). The torque cap makes
        the joints BACK-DRIVABLE — they yield to an external load above the cap
        instead of holding rigidly — so a partly-folded arm absorbs a caught
        ball's momentum (the elbow gives, like a human catch) rather than
        bouncing it back out. Default None = full motor torque (rigid)."""
        self._arm_mode = "hold"
        self._arm_targets["shoulder_pos"] = float(shoulder_pos)
        self._arm_targets["elbow_pos"] = float(elbow_pos)
        self._arm_targets["shoulder_vel_ff"] = float(shoulder_vel)
        self._arm_targets["elbow_vel_ff"] = float(elbow_vel)
        self._arm_targets["hold_torque_cap"] = torque_cap

    def fold_arm(self):
        self.hold_arm(self.arm_cfg.folded_shoulder, self.arm_cfg.folded_elbow)

    def extend_arm(self):
        """Hold the arm extended straight down (shoulder=0, elbow=0)."""
        self.hold_arm(0.0, self.arm_cfg.extended_elbow)

    def spin_arm(self, shoulder_vel: float, elbow_vel: float = 0.0,
                 torque_cap: float | None = None):
        """Velocity-mode servo: arm spins at the given joint rates.
        `torque_cap` overrides arm_max_torque for this mode — a low cap makes
        the joint back-drivable (it yields under external load), which is how
        the arm absorbs ball momentum during a compliant catch."""
        self._arm_mode = "spin"
        self._arm_targets["shoulder_vel"] = float(shoulder_vel)
        self._arm_targets["elbow_vel"] = float(elbow_vel)
        self._arm_targets["torque_cap"] = torque_cap

    # ------------ caging gripper (fingers) ------------
    def open_gripper(self):
        """Splay fingers to the open pose (wide mouth to receive a ball)."""
        if self.finger_joints:
            self._gripper_cmd = {"mode": "open"}

    def close_gripper(self, compliant: bool = False):
        """Curl fingers inward to cage.

        Default: position control to the closed pose with a torque cap.

        `compliant=True`: UNDERACTUATED / tendon-style close — apply a constant
        closing TORQUE to every finger joint (no target pose) + light damping,
        so each joint closes until IT contacts the ball and then stalls, the
        fingers CONFORMING to wherever the ball is instead of servoing to a
        fixed shape (which shoves an off-center ball out). Models a Yale-OpenHand
        /Fin-Ray hand where adaptation lives in the mechanism, not the
        controller. See docs/concepts/13. Requires disabling PyBullet's default
        per-joint velocity motor (which would otherwise fight the applied
        torque)."""
        if not self.finger_joints:
            return
        self._gripper_cmd = {"mode": "close", "compliant": compliant}
        if compliant:
            for segs in self.finger_joints:
                for jidx in segs:
                    p.setJointMotorControl2(self.body_id, jidx,
                                            p.VELOCITY_CONTROL, force=0.0)

    def gripper_is_closing(self) -> bool:
        return bool(self._gripper_cmd and self._gripper_cmd["mode"] == "close")

    def _apply_gripper(self):
        if not self.finger_joints or self._gripper_cmd is None:
            return
        cfg = self.arm_cfg
        closing = self._gripper_cmd["mode"] == "close"
        if not closing:
            # OPEN/waiting: pin the fingers kinematically at the open pose.
            # Motorizing 12 finger PD joints on a floating base overwhelms the
            # contact solver and the body diverges (~80 cm); pinning makes the
            # open hand effectively rigid → tight station-keeping (the catch's
            # tracking accuracy is set by how well the body holds station).
            # See iteration_findings §15.
            for segs in self.finger_joints:
                for k, jidx in enumerate(segs):
                    p.resetJointState(self.body_id, jidx,
                                      targetValue=cfg.finger_open[k],
                                      targetVelocity=0.0)
            return
        if self._gripper_cmd.get("compliant"):
            # COMPLIANT (underactuated/tendon) close: a constant inward torque
            # per joint + light damping, NO target pose. Each joint closes until
            # it contacts the ball, then the contact reaction balances the
            # torque and it stalls — the fingers conform to where the ball
            # actually is. (§13 / docs/concepts/13)
            for segs in self.finger_joints:
                for jidx in segs:
                    thd = p.getJointState(self.body_id, jidx)[1]
                    tau = cfg.finger_tau_close - cfg.finger_damp * thd
                    p.setJointMotorControl2(self.body_id, jidx,
                                            p.TORQUE_CONTROL, force=tau)
            return
        # CLOSING: gentle position control per segment. The force cap
        # (finger_close_torque) both limits squeeze on the ball AND, far from
        # the target, sets how hard the finger drives closed — fast yet
        # compliant on contact. Gains kept low: stiff finger servos flap and
        # excite the body's yaw singularity (§13). With 3-segment fingers the
        # long proximal reaches the ball's equator and middle+distal curl
        # under it (form closure, §15).
        for segs in self.finger_joints:
            for k, jidx in enumerate(segs):
                p.setJointMotorControl2(
                    self.body_id, jidx, p.POSITION_CONTROL,
                    targetPosition=cfg.finger_close[k], force=cfg.finger_close_torque,
                    positionGain=cfg.finger_pos_gain,
                    velocityGain=cfg.finger_vel_gain)

    def fingers_touching(self, ball_id: int) -> int:
        """Number of distinct fingers (not segments) in contact with the
        ball — the caging signal. A ball held by ≥3 wrapping fingers is
        geometrically trapped (form closure)."""
        pts = p.getContactPoints(bodyA=self.body_id, bodyB=ball_id)
        touched = set()
        for c in pts:
            link_a = c[3]
            for fid, segs in enumerate(self.finger_joints):
                if link_a in segs:
                    touched.add(fid)
        return len(touched)

    def set_finger_dynamics(self, lateral_friction=1.4, restitution=0.1,
                            contact_stiffness=None, contact_damping=None):
        """Tune the finger pads: high friction + low restitution + (optional)
        soft contact = foam-lined fingers that grip and don't bounce."""
        for link in self.finger_links:
            kw = dict(lateralFriction=lateral_friction, restitution=restitution)
            if contact_stiffness is not None:
                kw.update(contactStiffness=contact_stiffness,
                          contactDamping=contact_damping)
            p.changeDynamics(self.body_id, link, **kw)

    def step(self):
        force_world, torque = self._compute_body_wrench()
        self._apply_body_wrench(force_world, torque)
        # Arm motor commands (after body controller — they're independent)
        self._apply_arm()
        self._apply_gripper()

    def _compute_body_wrench(self):
        """Platform-specific control: returns (force_world, torque_body).

        This is the overridable seam for the body wrench. An underactuated
        quadrotor can only push along body-z, so the cascade's desired thrust
        is collapsed to a scalar magnitude and re-expanded along body-z here.
        A fully-actuated platform would override this to apply the full desired
        world-frame force directly. The gain-schedule, arm-reaction torque FF,
        and arm-translational-z FF all stay platform-side.
        """
        pos = self.position()
        vel = self.velocity()
        R = np.array(p.getMatrixFromQuaternion(self.orientation())).reshape(3, 3)
        omega = self.angular_velocity()

        if self.attitude_gain_schedule:
            self._apply_attitude_gain_schedule()
        ff_torque = self._arm_reaction_ff_body_torque() if self.arm_reaction_ff else None
        if self.finger_reaction_ff:
            fr = self._finger_reaction_ff_body_torque()
            ff_torque = fr if ff_torque is None else ff_torque + fr

        thrust_mag, torque = self.controller.compute(
            pos=pos, vel=vel, R=R, omega=omega,
            target=self.target, vel_target=self.vel_target,
            yaw_target=self.yaw_target,
            held_mass=self._held_mass(),
            MASS=self.mass, G=G,
            feedforward_torque_body=ff_torque,
        )

        # Body force: thrust along body-z. With the arm articulated and able
        # to swing far from base, system CoM shifts as joints move; the force
        # is applied at the SYSTEM CoM in _apply_body_wrench (see that method
        # and `_system_com_world`).
        force_world = R @ np.array([0.0, 0.0, thrust_mag])
        if self.arm_translational_ff_z:
            force_world = force_world + self._arm_translational_ff_world_force()
        return force_world, torque

    def _apply_body_wrench(self, force_world, torque_body):
        """Apply the body wrench to PyBullet: the world-frame force at the
        system CoM (WORLD_FRAME) and the body-frame torque (LINK_FRAME).

        Applying force at the base origin instead of the system CoM would
        generate a spurious torque proportional to the CoM offset when the arm
        swings out; computing the system CoM each step eliminates this.
        (See `_system_com_world` docstring.)
        """
        com_world = self._system_com_world()
        p.applyExternalForce(self.body_id, -1,
                             force_world.tolist(), com_world.tolist(),
                             p.WORLD_FRAME)
        p.applyExternalTorque(self.body_id, -1, torque_body.tolist(), p.LINK_FRAME)

    def _effective_pitch_inertia(self) -> float:
        """Effective body-pitch inertia (about body +y) including the arm and
        any held mass, computed from current shoulder angle. Uses point-mass
        approximations for arm CoM (at half-length) and ball at end-effector.

        Geometry: shoulder is at body z=+0.040 m above body CoM (approx,
        based on URDF top-of-base). Arm at angle θ from straight-down has:
            arm CoM at body (sin(θ)·L/2, 0, -cos(θ)·L/2 - d_z)
            ball at body (sin(θ)·L,    0, -cos(θ)·L    - d_z)
        For pitch axis (+y), perpendicular distance² = x² + z²:
            d² = r² + 2·r·d_z·cos(θ) + d_z²
        where r is the position along the arm (L/2 for arm CoM, L for ball).
        """
        s_pos, _, _, _ = self.joint_states()
        cos_t = float(np.cos(s_pos))
        L_arm = self.arm_cfg.upper_arm_len + self.arm_cfg.forearm_len
        d_z = 0.04
        m_arm_total = 0.075  # arm + EE link mass (matches URDF)
        r_arm = L_arm / 2
        # Arm self-inertia about its own CoM (thin rod): m·L²/12 ≈ 0.001
        I_arm_self = m_arm_total * L_arm**2 / 12.0
        I_arm = I_arm_self + m_arm_total * (r_arm**2
                                             + 2 * r_arm * d_z * cos_t
                                             + d_z**2)
        I_ball = 0.0
        if self.held_constraint is not None:
            m_held = self._held_mass()
            I_ball = m_held * (L_arm**2 + 2 * L_arm * d_z * cos_t + d_z**2)
        I_body = 0.0025  # body-alone pitch inertia (matches design tuning)
        return I_body + I_arm + I_ball

    def _apply_attitude_gain_schedule(self):
        """Rescale controller's kR_y and kw_y to maintain target ω_n and ζ
        across configurations. Roll axis (kR_x, kw_x) and yaw axis are left
        alone — arm motion is purely in pitch."""
        I_y = self._effective_pitch_inertia()
        omega_n = self.target_omega_n_y
        zeta = self.target_zeta_y
        self.controller.kR[1] = omega_n * omega_n * I_y
        self.controller.kw[1] = 2.0 * zeta * omega_n * I_y

    def _arm_translational_ff_world_force(self) -> np.ndarray:
        """Predicted world-frame force to cancel the body-z disturbance from
        arm dynamics (centripetal + tangential components).

        Body-frame z disturbance during sweep:
            F_body_z_dist = −m_eff·(α·sin(θ) + ω²·cos(θ))
        where m_eff = m_arm·(L/2) + m_held·L (point-mass approx),
              θ = shoulder angle (0 = down, +π/2 = forward),
              ω = measured shoulder angular velocity,
              α = commanded shoulder angular acceleration (rate-limited).

        We use the *measured* ω (from getJointState) for the centripetal
        term — it tracks reality better than commanded during transients.
        The α term uses commanded velocity finite-difference (same predictor
        as the rotational FF), since "acceleration" doesn't have a clean
        measurement.

        Returns a world-frame 3-vec; we apply the negation of the body-z
        disturbance, transformed into world via the drone's rotation matrix.
        Drone level → body-z = world-z. Drone tilted → component projects.
        """
        s_pos, s_vel, _, _ = self.joint_states()
        omega = float(s_vel)
        cos_t = float(np.cos(s_pos))
        sin_t = float(np.sin(s_pos))
        # Use the rotational FF's prev tracker for α (same kinematic model)
        cur_cmd = (self._arm_targets["shoulder_vel"]
                   if self._arm_mode == "spin" else 0.0)
        # Don't double-update prev; the rotational FF already does that
        # this tick. We just read it and recompute alpha consistently.
        prev = self._shoulder_vel_cmd_prev
        I_arm = (self.arm_cfg.I_arm_with_ball
                 if self.held_constraint is not None
                 else self.arm_cfg.I_arm_extended)
        alpha_max = self.arm_cfg.arm_max_torque / I_arm
        delta_max = alpha_max * DT
        delta = float(np.clip(cur_cmd - prev, -delta_max, +delta_max))
        alpha_cmd = delta / DT

        L = self.arm_cfg.upper_arm_len + self.arm_cfg.forearm_len
        m_arm = 0.075
        m_held = self._held_mass()
        m_eff = m_arm * (L / 2.0) + m_held * L

        # Body-frame disturbance on body
        F_body_z_dist = -m_eff * (alpha_cmd * sin_t + omega * omega * cos_t)
        # Cancel: apply opposite in body-z
        F_body_z_ff = -F_body_z_dist  # = +m_eff·(α·sin + ω²·cos)
        # Transform to world (drone may be tilted; project body-z direction)
        R = np.array(p.getMatrixFromQuaternion(self.orientation())).reshape(3, 3)
        body_z_world = R @ np.array([0.0, 0.0, 1.0])
        return body_z_world * F_body_z_ff

    def _arm_reaction_ff_body_torque(self) -> np.ndarray:
        """Predict the body torque that cancels the arm-reaction torque
        from changing the COMMANDED shoulder velocity.

        Kinematic predictor: τ_reaction = I_arm · α_cmd, where α_cmd is
        finite-difference of the commanded shoulder ω. We feed forward the
        opposite to spare the cascade from reacting to a known disturbance.

        Joint axis (URDF): shoulder = body -y. Motor torque +τ along the
        joint axis gives the body a reaction +τ along +y direction. To
        cancel, FF body torque = [0, -τ, 0] in LINK_FRAME.

        Rate-limiting the transition: when commanded ω jumps in one step
        (e.g., spin→hold), the raw finite difference implies α larger than
        the motor can physically deliver. The motor will take several ticks
        to actually brake the arm at its torque cap, so the body
        disturbance lasts for that whole window. We rate-limit our
        internal `_shoulder_vel_cmd_prev` to respect the physically-
        achievable α_max = τ_max / I_arm, which makes the FF spread the
        compensation across the same number of ticks as the real
        disturbance. Side benefit: rules out the spurious one-tick FF
        spike that double-counts during the kinematic step.

        We deliberately do NOT use the cascade's *measured* steady-state
        compensation — gravity on the arm is a baseline torque the cascade
        already absorbs cleanly during hover. FF here only catches the
        transients we know are coming from arm-acceleration commands.
        """
        cur_cmd = (self._arm_targets["shoulder_vel"]
                   if self._arm_mode == "spin" else 0.0)
        I_arm = (self.arm_cfg.I_arm_with_ball
                 if self.held_constraint is not None
                 else self.arm_cfg.I_arm_extended)
        alpha_max = self.arm_cfg.arm_max_torque / I_arm
        delta_max = alpha_max * DT
        delta = cur_cmd - self._shoulder_vel_cmd_prev
        delta = float(np.clip(delta, -delta_max, +delta_max))
        new_prev = self._shoulder_vel_cmd_prev + delta
        alpha = delta / DT  # rate-limited to ±alpha_max
        self._shoulder_vel_cmd_prev = new_prev
        tau_predicted = I_arm * alpha
        return np.array([0.0, -tau_predicted, 0.0])

    def _finger_reaction_ff_body_torque(self) -> np.ndarray:
        """Predict the body torque that cancels the net reaction from the
        gripper's finger-joint motor torques.

        Each finger joint motor that applies torque τ_j about its (world-frame)
        axis a_j exerts +τ_j·a_j on the finger and, by Newton's third law,
        −τ_j·a_j back up the chain onto the airframe. The net body disturbance
        is therefore Σ_j(−τ_j·a_j); to cancel it the body must add the opposite,
        Σ_j(τ_j·a_j). We read the ACTUAL applied joint motor torque
        (getJointState[3]) so this works for any close strategy — position-PD
        ("fixed"), constant-torque ("active"/tendon), or spring ("passive").

        Same kinematic, torque-pair approximation as `_arm_reaction_ff_body_torque`
        (it ignores the second-order moments from finger contact forces). In the
        arm-straight-down catch pose the finger axes are near-horizontal and the
        ring is symmetric, so the true net is small — but an asymmetric seated
        ball or a tilted arm breaks that symmetry, and this FF catches the
        residual. Returns a body-frame 3-vector; 0 if no fingers.
        """
        if not self.finger_joints:
            return np.zeros(3)
        R = np.array(p.getMatrixFromQuaternion(self.orientation())).reshape(3, 3)
        ff_world = np.zeros(3)
        for segs in self.finger_joints:
            for j in segs:
                tau_j = p.getJointState(self.body_id, j)[3]   # applied motor torque
                a_local = np.array(p.getJointInfo(self.body_id, j)[13], dtype=float)
                R_child = np.array(p.getMatrixFromQuaternion(
                    p.getLinkState(self.body_id, j)[5])).reshape(3, 3)
                a_world = R_child @ a_local
                ff_world += tau_j * a_world      # = -(reaction on body)
        return R.T @ ff_world

    def _apply_arm(self):
        """Drive shoulder + elbow joints based on current _arm_mode."""
        cfg = self.arm_cfg
        if self._arm_mode == "hold":
            sv = self._arm_targets.get("shoulder_vel_ff", 0.0)
            ev = self._arm_targets.get("elbow_vel_ff", 0.0)
            cap = self._arm_targets.get("hold_torque_cap")
            tq = cfg.arm_max_torque if cap is None else cap
            p.setJointMotorControl2(self.body_id, self.shoulder_joint,
                p.POSITION_CONTROL,
                targetPosition=self._arm_targets["shoulder_pos"],
                targetVelocity=sv,
                positionGain=cfg.arm_kp, velocityGain=cfg.arm_kd,
                force=tq)
            p.setJointMotorControl2(self.body_id, self.elbow_joint,
                p.POSITION_CONTROL,
                targetPosition=self._arm_targets["elbow_pos"],
                targetVelocity=ev,
                positionGain=cfg.arm_kp, velocityGain=cfg.arm_kd,
                force=tq)
        elif self._arm_mode == "spin":
            cap = self._arm_targets.get("torque_cap")
            torque = cfg.arm_max_torque if cap is None else cap
            p.setJointMotorControl2(self.body_id, self.shoulder_joint,
                p.VELOCITY_CONTROL,
                targetVelocity=self._arm_targets["shoulder_vel"],
                force=torque)
            p.setJointMotorControl2(self.body_id, self.elbow_joint,
                p.VELOCITY_CONTROL,
                targetVelocity=self._arm_targets["elbow_vel"],
                force=torque)

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

    def soft_grasp(self, target_body: int, max_distance: float = 0.15,
                   max_force: float = 8.0) -> bool:
        """Compliant capture: point-to-point constraint with a low force cap.
        The ball decelerates over many steps (impulse spread over ~m·Δv/F_max
        seconds) instead of a 1-step rigid snap — stands in for foam pad +
        compliant fingers. Call `firm_grasp()` once relative velocity decays
        to lock the carry."""
        if self.held_constraint is not None:
            return True
        ee_pos = self.gripper_world_position()
        their_pos, _ = p.getBasePositionAndOrientation(target_body)
        if np.linalg.norm(ee_pos - np.array(their_pos)) > max_distance:
            return False
        self.held_constraint = p.createConstraint(
            parentBodyUniqueId=self.body_id, parentLinkIndex=self.ee_link,
            childBodyUniqueId=target_body, childLinkIndex=-1,
            jointType=p.JOINT_POINT2POINT, jointAxis=[0, 0, 0],
            parentFramePosition=[0, 0, 0],
            childFramePosition=[0, 0, 0],
        )
        p.changeConstraint(self.held_constraint, maxForce=max_force)
        return True

    def firm_grasp(self, max_force: float = 200.0):
        """Ratchet the held constraint stiff (absorption done → carry)."""
        if self.held_constraint is not None:
            p.changeConstraint(self.held_constraint, maxForce=max_force)

    def grasp_force(self) -> float:
        """Magnitude (N) of the constraint force currently applied to the
        held body. 0 if nothing held."""
        if self.held_constraint is None:
            return 0.0
        f = p.getConstraintState(self.held_constraint)
        return float(np.linalg.norm(f[:3]))

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
