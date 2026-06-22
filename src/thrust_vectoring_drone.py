"""ThrustVectoringDrone: an over-actuated quadrotor variant.

This is the platform from CLAUDE.md parking-lot #11 / iteration_findings §22 /
docs/concepts/12. A standard quad is underactuated (4 inputs, 6 DoF) so it must
pitch the whole body to translate. Here each rotor gets a **radial tilt servo**
(one per rotor -> 8 inputs vs 6 DoF, over-actuated, 2-dim null space), so the
body can produce a horizontal force WITHOUT tilting. The cascade's
thrust->attitude inversion is gone: position and attitude are commanded
independently and a **control-allocation** map turns the desired 6-vector wrench
into 8 actuator commands (4 thrusts + 4 tilt angles).

Subclassing seam: we override ONLY `_compute_body_wrench()` (and apply the
per-rotor forces ourselves). All inherited state queries, arm motor control,
gripper, and grasp logic are reused unchanged.

--------------------------------------------------------------------------
Geometry / sign conventions (body frame, z up, x forward)
--------------------------------------------------------------------------
Rotor i sits at body position p_i = (x_i, y_i, z0), on the quadrant diagonals
(+-0.10, +-0.10). Its **radial** unit (hub -> rotor, horizontal) is
r_i = (x_i, y_i, 0)/|.|. The tilt servo angle beta_i nods the thrust in the
vertical plane that contains r_i, so the thrust vector in body frame is

    F_i = T_i * ( cos(beta_i) * z_hat  +  sin(beta_i) * r_i )     (T_i >= 0)

i.e. the horizontal component is **radial** (points through the hub). Because a
radial force has zero moment arm about the hub axis, radial tilts produce **no
yaw torque** (and, modeled in the CoM plane, no roll/pitch either) -> the
allocation separates cleanly:

  * vertical thrusts v_i = T_i cos(beta_i)  -> Fz, tau_x, tau_y  (the usual X-mix)
    plus yaw from rotor-drag differential   -> tau_z
  * radial thrusts   h_i = T_i sin(beta_i)  -> Fx, Fy            (torque-free)

MODELING CHOICE: rotor forces are applied in the **CoM plane** (rotor z set to
the system-CoM height) so the radial-tilt-is-torque-free property holds exactly
as the arm shifts the CoM. The rotors' true ~4 cm height above the CoM is a
small second-order coupling that is out of scope for this platform validation
(it would only re-introduce a fraction of the underactuation we're removing).

See assets/make_tv_gripper_urdf.py for the matching URDF and the note on why the
hinge axis is *tangential* (the design doc's "hinge along the arm" wording is a
slip; the testable property is radial force / zero yaw torque).
"""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import pybullet as p

from drone import Drone, G

# rotor name -> drag-torque (yaw) sign. X-quad: opposite corners spin together.
_ROTOR_YAW_SIGN = {"fl": +1.0, "br": +1.0, "fr": -1.0, "bl": -1.0}


@dataclass
class ThrustVectoringDrone(Drone):
    # --- allocator / actuator limits ---
    beta_max: float = 0.785          # rad, max tilt servo deflection (~45 deg)
    rotor_thrust_max: float = 8.0    # N, per-rotor thrust cap
    kappa: float = 0.02              # rotor drag-torque / thrust ratio (yaw auth)
    allocator: str = "per_rotor"     # "per_rotor" (deliverable) or "ideal" (CoM wrench)

    # --- independent attitude PD (replaces the cascade inner loop) ---
    # Sized for the gripper-arm pitch inertia (~0.02 kg.m^2): omega_n ~ 10 rad/s,
    # zeta ~ 1.0. Integral absorbs the steady arm-weight torque so the body holds
    # level (no standing pitch offset) without a thrust->attitude detour.
    kR_att: np.ndarray = field(default_factory=lambda: np.array([2.0, 2.0, 0.8]))
    kw_att: np.ndarray = field(default_factory=lambda: np.array([0.4, 0.4, 0.15]))
    kI_att: np.ndarray = field(default_factory=lambda: np.array([1.5, 1.5, 0.0]))
    att_integral_clamp: float = 0.5  # rad.s
    # attitude reference: "level" holds pitch=roll=0 (the point of full
    # actuation). "align" points body-z along the desired force (quad-like) and
    # lets the tilt servos do less work -- used for the B1 let-it-tilt sub-mode.
    attitude_mode: str = "level"
    # Full 3-axis arm-recoil cancellation (vs the base z-only). Off by default;
    # the platform's advantage over the underactuated drone during an arm sweep.
    arm_translational_ff_full: bool = False

    # --- discovered / state (init=False) ---
    tilt_joints: list = field(default_factory=list, init=False)   # [(jidx, name)]
    _rotor_pos_body: np.ndarray = field(default=None, init=False)  # (4,3)
    _rotor_yaw_sign: np.ndarray = field(default=None, init=False)  # (4,)
    _e_att_integral: np.ndarray = field(default=None, init=False)
    # last-step diagnostics (read by tests)
    last_wrench_des: np.ndarray = field(default=None, init=False)
    last_wrench_realized: np.ndarray = field(default=None, init=False)
    last_tilts: np.ndarray = field(default=None, init=False)
    last_thrusts: np.ndarray = field(default=None, init=False)
    last_saturated: bool = field(default=False, init=False)

    def __post_init__(self):
        super().__post_init__()
        self._e_att_integral = np.zeros(3)
        # Discover tilt joints + rotor positions from the URDF.
        pos, sign, joints = [], [], []
        for j in range(p.getNumJoints(self.body_id)):
            info = p.getJointInfo(self.body_id, j)
            jname = info[1].decode()
            if jname.startswith("tilt_") and jname.endswith("_joint"):
                key = jname[len("tilt_"):-len("_joint")]    # fl/fr/bl/br
                frame_pos = np.array(info[14])               # joint origin in base
                pos.append(frame_pos)
                sign.append(_ROTOR_YAW_SIGN[key])
                joints.append((j, key))
        assert len(joints) == 4, f"expected 4 tilt rotors, found {len(joints)}"
        self.tilt_joints = joints
        self._rotor_pos_body = np.array(pos)
        self._rotor_yaw_sign = np.array(sign)
        # Tilt joints are cosmetic: pin them kinematically (zero dynamic load),
        # we drive the angle each step purely for the rendered tilt.
        for j, _ in self.tilt_joints:
            p.resetJointState(self.body_id, j, targetValue=0.0, targetVelocity=0.0)
            p.setJointMotorControl2(self.body_id, j, p.VELOCITY_CONTROL, force=0.0)

    # ----------------------------------------------------------------- wrench
    def _compute_body_wrench(self):
        """Override: build the desired wrench (position force + attitude torque,
        decoupled), allocate to 8 actuators, apply per-rotor forces. Returns the
        residual (force_world, torque_body) for the base `_apply_body_wrench`:
        in per_rotor mode that's (0, [0,0,tau_z_drag]) since we apply the rotor
        forces ourselves; in ideal mode it's the full (F_des, tau_des)."""
        pos = self.position()
        vel = self.velocity()
        R = np.array(p.getMatrixFromQuaternion(self.orientation())).reshape(3, 3)
        omega = self.angular_velocity()

        # FORCE half: reuse the position-PD outer loop (raw desired world force,
        # gravity FF incl. held mass). NO tilt cap / vertical floor -- a fully
        # actuated body needs neither.
        F_des_world = self.controller.desired_force_world(
            pos=pos, vel=vel, target=self.target, vel_target=self.vel_target,
            MASS=self.mass, G=G, held_mass=self._held_mass())
        # The arm's reaction on the body is a predictable disturbance ORTHOGONAL
        # to underactuation (it exists for any airframe). The torque feedforward
        # MUST be computed first: it advances `_shoulder_vel_cmd_prev`, which the
        # translational FF then reads (same ordering contract as the base Drone).
        ff_torque = (self._arm_reaction_ff_body_torque()
                     if self.arm_reaction_ff else None)
        # Finger-reaction FF (additive, default off): pre-cancel the body torque
        # from the gripper's finger-joint motor torques during a close, the same
        # way arm_reaction_ff handles the arm sweep. See Drone.finger_reaction_ff.
        if self.finger_reaction_ff:
            fr = self._finger_reaction_ff_body_torque()
            ff_torque = fr if ff_torque is None else ff_torque + fr
        # Translational recoil cancellation. The sweep's centripetal+tangential
        # force flings the body in the arm's plane (body x AND z). A full quad can
        # only cancel z directly (x needs a tilt it doesn't want); THE OVER-
        # ACTUATED BODY CANCELS BOTH (push any direction while staying level) --
        # this is exactly where full actuation should win the arm-sweep test.
        if self.arm_translational_ff_full:
            F_des_world = F_des_world + self._arm_reaction_force_world()
        elif self.arm_translational_ff_z:
            F_des_world = F_des_world + self._arm_translational_ff_world_force()

        # TORQUE half: independent attitude PD (no thrust->attitude inversion).
        tau_des_body = self._attitude_torque(R, omega, F_des_world, ff_torque)

        self.last_wrench_des = np.concatenate([F_des_world, R @ tau_des_body])

        if self.allocator == "ideal":
            # Idealised sanity: apply the net wrench at the CoM directly.
            self.last_wrench_realized = self.last_wrench_des.copy()
            self.last_tilts = np.zeros(4)
            self.last_thrusts = np.full(4, np.nan)
            return F_des_world, tau_des_body

        # Per-rotor allocation + application.
        F_des_body = R.T @ F_des_world
        thrusts, betas, rel_xy_body, rhat_body, tau_z_drag = self._allocate(
            F_des_body, tau_des_body)
        self._apply_rotor_forces(R, thrusts, betas, rel_xy_body, rhat_body)
        self._drive_tilt_visuals(betas)

        # residual yaw drag torque -> applied by base _apply_body_wrench
        return np.zeros(3), np.array([0.0, 0.0, tau_z_drag])

    def _arm_reaction_force_world(self) -> np.ndarray:
        """Full world-frame force to cancel the arm's translational recoil, in
        BOTH the body x and z (the sweep plane). The base class only cancels z
        (an underactuated quad can't add a body-x force without tilting); the
        over-actuated body adds it directly while staying level.

        Body-frame recoil = m_eff * arm-CoM acceleration:
            a = alpha*(cos θ, 0, sin θ) + ω²*(-sin θ, 0, cos θ)
        with θ = shoulder angle (0 down, +forward), ω measured, alpha the
        rate-limited commanded shoulder acceleration (same predictor as the
        torque FF, which must run first to advance `_shoulder_vel_cmd_prev`)."""
        s_pos, s_vel, _, _ = self.joint_states()
        omega = float(s_vel)
        cos_t, sin_t = float(np.cos(s_pos)), float(np.sin(s_pos))
        cur_cmd = (self._arm_targets["shoulder_vel"]
                   if self._arm_mode == "spin" else 0.0)
        I_arm = (self.arm_cfg.I_arm_with_ball if self.held_constraint is not None
                 else self.arm_cfg.I_arm_extended)
        alpha_max = self.arm_cfg.arm_max_torque / I_arm
        delta_max = alpha_max * self.controller.DT
        # read (not update) prev — the torque FF advanced it this tick already
        delta = float(np.clip(cur_cmd - self._shoulder_vel_cmd_prev,
                              -delta_max, delta_max))
        alpha = delta / self.controller.DT
        L = self.arm_cfg.upper_arm_len + self.arm_cfg.forearm_len
        m_eff = 0.075 * (L / 2.0) + self._held_mass() * L
        F_body_x = m_eff * (alpha * cos_t - omega * omega * sin_t)
        F_body_z = m_eff * (alpha * sin_t + omega * omega * cos_t)
        R = np.array(p.getMatrixFromQuaternion(self.orientation())).reshape(3, 3)
        return R @ np.array([F_body_x, 0.0, F_body_z])

    def _attitude_torque(self, R, omega, F_des_world, ff_torque=None) -> np.ndarray:
        """Geometric SO(3) PD+I attitude torque (body frame). R_des is built
        independently of thrust: 'level' = upright at yaw_target; 'align' =
        body-z along the desired force (quad-like)."""
        psi = self.yaw_target
        x_c = np.array([np.cos(psi), np.sin(psi), 0.0])
        if self.attitude_mode == "align":
            n = np.linalg.norm(F_des_world)
            z_des = F_des_world / n if n > 1e-6 else np.array([0.0, 0.0, 1.0])
        else:  # "level"
            z_des = np.array([0.0, 0.0, 1.0])
        y_des = np.cross(z_des, x_c)
        ny = np.linalg.norm(y_des)
        y_des = y_des / ny if ny > 1e-6 else np.array([0.0, 1.0, 0.0])
        x_des = np.cross(y_des, z_des)
        R_des = np.column_stack([x_des, y_des, z_des])

        skew = 0.5 * (R_des.T @ R - R.T @ R_des)
        e_R = np.array([skew[2, 1], skew[0, 2], skew[1, 0]])
        omega_body = R.T @ omega
        self._e_att_integral = np.clip(self._e_att_integral + e_R * self.controller.DT,
                                       -self.att_integral_clamp, self.att_integral_clamp)
        tau = (-self.kR_att * e_R - self.kw_att * omega_body
               - self.kI_att * self._e_att_integral)
        if ff_torque is not None:
            tau = tau + np.asarray(ff_torque, dtype=float)
        return tau

    # --------------------------------------------------------------- allocate
    def _allocate(self, F_des_body, tau_des_body):
        """Separable closed-form allocation.

        Vertical sub-problem (4 unknowns v_i, 4 eqns): the standard X-mixer maps
        [Fz, tau_x, tau_y, tau_z] -> v_i (with tau_z via drag differential).
        Horizontal sub-problem (4 unknowns h_i, 2 eqns Fx,Fy): under-determined
        -> min-norm pseudo-inverse (the 2-dim null space; v1 leaves it unused).
        Then T_i = hypot(v_i,h_i), beta_i = atan2(h_i,v_i), clamped.
        """
        Fx, Fy, Fz = F_des_body
        tx, ty, tz = tau_des_body

        # rotor positions relative to system CoM, projected into the CoM plane.
        com_world = self._system_com_world()
        base_pos = np.array(p.getBasePositionAndOrientation(self.body_id)[0])
        R = np.array(p.getMatrixFromQuaternion(self.orientation())).reshape(3, 3)
        c_body = R.T @ (com_world - base_pos)
        rel = self._rotor_pos_body - c_body            # (4,3) body frame
        rx, ry = rel[:, 0], rel[:, 1]                  # CoM-plane offsets

        # --- vertical mixer: rows [Fz, tau_x, tau_y, tau_z] ---
        #   Fz   = sum v_i
        #   tau_x= sum v_i * ry_i        (p x z_hat -> +ry on x)
        #   tau_y= sum v_i * (-rx_i)
        #   tau_z= sum sigma_i kappa v_i (rotor drag)
        Mv = np.vstack([np.ones(4), ry, -rx, self._rotor_yaw_sign * self.kappa])
        v = np.linalg.solve(Mv, np.array([Fz, tx, ty, tz]))

        # Vertical-PRIORITY saturation: Fz / tau_x / tau_y / tau_z are always
        # realized exactly (so the body never loses altitude or attitude
        # authority). v_i is only clipped to the physical [0, rotor_max] (a rotor
        # can't pull down or exceed its cap). The horizontal (lateral) force is
        # then best-effort: limited so each rotor stays within BOTH its tilt
        # limit (|beta|<=beta_max -> |h|<=v*tan) and its thrust cap
        # (hypot(v,h)<=rotor_max). This degrades lateral authority gracefully
        # under saturation instead of letting v explode (which would launch the
        # body) -- the key stability property under aggressive demands.
        v = np.clip(v, 0.0, self.rotor_thrust_max)

        # --- horizontal: radial unit per rotor (from CoM), min-norm h ---
        rnorm = np.hypot(rx, ry)
        rhat = np.stack([rx / rnorm, ry / rnorm], axis=1)    # (4,2)
        Mh = rhat.T                                          # (2,4)
        h = np.linalg.pinv(Mh) @ np.array([Fx, Fy])

        h_tilt_lim = v * np.tan(self.beta_max)
        h_thrust_lim = np.sqrt(np.maximum(0.0, self.rotor_thrust_max**2 - v**2))
        h_lim = np.minimum(h_tilt_lim, h_thrust_lim)
        sat = np.abs(h) > h_lim + 1e-9
        h = np.clip(h, -h_lim, h_lim)
        thrusts = np.hypot(v, h)
        betas = np.arctan2(h, v)
        self.last_saturated = bool(np.any(sat))
        self.last_tilts = betas.copy()
        self.last_thrusts = thrusts.copy()

        rel_xy = np.stack([rx, ry, np.zeros(4)], axis=1)     # apply in CoM plane
        rhat3 = np.stack([rhat[:, 0], rhat[:, 1], np.zeros(4)], axis=1)
        # realized yaw drag from the *clamped* vertical thrust
        v_real = thrusts * np.cos(betas)
        tau_z_drag = float(np.sum(self._rotor_yaw_sign * self.kappa * v_real))
        return thrusts, betas, rel_xy, rhat3, tau_z_drag

    def _apply_rotor_forces(self, R, thrusts, betas, rel_xy_body, rhat_body):
        """Apply each rotor's thrust as a world-frame vector at the rotor's
        (CoM-plane) position. PyBullet integrates the net force + the torque
        about the CoM from the application points. Also records the realized
        net wrench (about the CoM) for U1 fidelity checks."""
        com_world = self._system_com_world()
        F_net = np.zeros(3)
        tau_net = np.zeros(3)
        z_b = np.array([0.0, 0.0, 1.0])
        for i in range(4):
            F_body = thrusts[i] * (np.cos(betas[i]) * z_b
                                   + np.sin(betas[i]) * rhat_body[i])
            F_world = R @ F_body
            point_world = com_world + R @ rel_xy_body[i]
            p.applyExternalForce(self.body_id, -1, F_world.tolist(),
                                 point_world.tolist(), p.WORLD_FRAME)
            F_net += F_world
            tau_net += np.cross(R @ rel_xy_body[i], F_world)   # about CoM, world
        # add the explicit yaw drag torque (world) for the realized record
        v_real = thrusts * np.cos(betas)
        tau_z = float(np.sum(self._rotor_yaw_sign * self.kappa * v_real))
        tau_net += R @ np.array([0.0, 0.0, tau_z])
        self.last_wrench_realized = np.concatenate([F_net, tau_net])

    def _drive_tilt_visuals(self, betas):
        """Kinematically set the cosmetic rotor disks to the commanded tilt so
        the rendered drone visibly vectors its thrust (no dynamic effect)."""
        for (j, _), b in zip(self.tilt_joints, betas):
            p.resetJointState(self.body_id, j, targetValue=float(b),
                              targetVelocity=0.0)
