"""Trustworthy FIXED-BASE caging-robustness harness (Phase 0/1).

Why this exists: prior quick grasp experiments (iteration_findings §24) gave
noisy / contradictory results because the "caged" signal was distance + fingers
touching, and the ball seating was non-deterministic. This harness replaces both:

  * Deterministic seating — the gripper is on a FIXED base in the catch pose, the
    arm held rigid, gravity OFF during the close, and the ball is placed at a
    controlled (offset magnitude, direction) in the cup. No flight dynamics, no
    perception, no randomness -> the same config gives the identical score.

  * A REAL form-closure metric — NOT "distance + touching". After the close we
    save the world state and fire a battery of 26 disturbance accelerations
    (the {-1,0,1}^3 sphere directions) at ~2.5 g each, re-applied from the saved
    state, and check whether the ball stays trapped within the finger envelope
    for EACH. robustness score = fraction of directions survived. This is the
    topological cage test (the inversion test, generalised to all directions).

Self-validation (the Phase-0 GATE; run `--self-test`):
  (a) determinism      — same config 3x -> identical score.
  (b) positive control — centered ball + current fixed-pose close -> caged.
  (c) negative control — ball 8 cm outside the cup -> score 0.

Phase-1 study (`--grid`): robustness vs offset x direction x close-strategy x
finger-count x ready-pose. `--cell` runs one configuration; `--render` saves
frames of a grasp.

Run from repo root (adds src/ to path):
    python tests/cage_harness.py --self-test
    python tests/cage_harness.py --grid
    python tests/cage_harness.py --cell --strategy passive --n 6 --offset 0.025 --dir gap
    python tests/cage_harness.py --render --strategy passive --n 6 --offset 0.025 --dir gap
"""
from __future__ import annotations
import argparse
import itertools
import math
import os
import sys

import numpy as np
import pybullet as p
import pybullet_data

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from config import ArmConfig                     # noqa: E402
from ball import spawn_ball                      # noqa: E402
import yale_hand                                 # noqa: E402 (contact-reading stand-in)
import yale_prb                                  # noqa: E402 (faithful PRB mechanism)

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
sys.path.insert(0, ASSETS)
import make_gripper_variants as variants         # noqa: E402

DT = 1.0 / 240.0
G = 9.81
PRB_INERTIA_OVERRIDE = None    # set by --prb-inertia to sweep the PRB inertia scale

# ---- fixed-base catch pose (arm straight down, fingers below the EE) ----
BASE_POS = (0.0, 0.0, 1.0)
SHOULDER_HOLD = 0.0          # arm hangs straight down
ELBOW_HOLD = 0.0            # extended
CUP_DEPTH = 0.045           # enclosure center beyond the EE link (the cup)

# ---- close strategies (constants mirror config.ArmConfig defaults) ----
# All strategies drive the joints toward the VALIDATED cage pose (long proximal
# to the equator, middle+distal curl under, §15) via force-limited POSITION
# control. They differ ONLY in compliance:
#   fixed     - rigid: high force cap, servos to the fixed shape (current close).
#   compliant - "active underactuated" stand-in: LOW force cap, so each joint
#               yields/stalls on contact (conforms to where the ball is). NOTE:
#               we model active underactuation this way rather than as a constant
#               joint torque ("tendon") because a constant torque on this near-
#               massless 3-link finger chain is NUMERICALLY ill-conditioned in
#               PyBullet (a Coulomb-friction-like joint threshold, sign-flips,
#               frozen distal joints) -> it neither reproduces the cage shape nor
#               gives repeatable results. Force-limited position control is the
#               robust, behaviourally-faithful model of yield-on-contact. The raw
#               constant-torque mode is kept as `tendon` for the record (excluded
#               from the ranking).
#   soft      - "passive soft-joint" / Fin-Ray flexure stand-in: low force AND a
#               soft position gain, so the finger is a weak spring toward the cage
#               pose and conforms with little holding torque (low body reaction).
CFG = ArmConfig()
READY_SPLAYED = CFG.finger_open            # (-0.4, -0.2, 0.0)
READY_CURLED = (0.10, 0.30, 0.50)          # partly-curled ready pose
CLOSE_POSE = CFG.finger_close              # (0.5, 1.0, 1.3) — validated cage pose
FIX_TORQUE = CFG.finger_close_torque       # 0.5  N.m rigid position cap
FIX_KP, FIX_KD = CFG.finger_pos_gain, CFG.finger_vel_gain   # 0.6, 0.8
COMPLIANT_FORCE = 0.06     # N.m yield-on-contact cap (conforming close)
SOFT_FORCE = 0.06          # N.m
SOFT_KP = 0.10             # soft position gain (Fin-Ray flexure spring)
# Underactuated/differential close: low force toward a DEEP curl (past the cage
# pose), so each joint stalls on contact and uncontacted joints curl further —
# the shape ADAPTS to where the ball is (whiffletree analogue). UNDER_DEEP > the
# cage pose so the distal keeps tucking under after the proximal seats.
UNDER_DEEP = (1.3, 1.9, 1.9)
UNDER_FORCE = 0.05         # N.m yield-on-contact cap
TENDON_TAU = CFG.finger_tau_close          # 0.12 N.m constant (record only)
JOINT_DAMP = CFG.finger_damp               # 0.010 N.m.s

# ---- numerics (the trustworthy operating point) ----
# CRITICAL (found the hard way, see iteration_findings §26): with RIGID contact
# at the project's 1/240 timestep, the OFF-CENTER caging verdict is numerically
# fragile — near-massless (3e-6) rigid fingers paddling a rigid ball at the
# capture boundary, under continuous PD pressing in zero-g, is ill-conditioned,
# and "caged vs paddled out" flips with the timestep (a false "gap fails"
# artifact). The fix is BOTH (a) compliant contact PADS (also more physical —
# real fingers have foam/rubber) and (b) a finer substep. With both, the verdict
# CONVERGES (substep 4 == 8) and the centered/finger/gap cases all cage to 3.5 cm
# while the negative control still escapes. The centered + far-outside controls
# are timestep-stable at any setting (so the self-validation passed even at
# 1/240); only the marginal off-center band needed this.
SUBSTEP = 4                # sim sub-steps per 240 Hz tick -> fixedTimeStep 1/960
SIM_DT = DT / SUBSTEP
CONTACT_STIFFNESS = 1.0e4  # N/m, compliant finger-pad + ball contact
CONTACT_DAMPING = 3.0e2    # N.s/m

# ---- timing (step counts below are in 240 Hz ticks; scaled by SUBSTEP) ----
CLOSE_STEPS = 130          # ~0.54 s to close + seat
SETTLE_STEPS = 24          # ~0.10 s to settle the cage
WINDOW_STEPS = 84          # ~0.35 s disturbance window per direction

# ---- disturbance battery ----
GACC = 2.5 * G             # ~2.5 g each direction
ESCAPE_DELTA = 0.040       # m; ball displacement from settled pos beyond which
                           # it has left the basket (validated by the controls)

PAD_FRICTION = 1.4
BALL_RESTITUTION = 0.10
BALL_FRICTION = 1.4


def setup_physics():
    """Solver + finer timestep + zero gravity — the validated numerics."""
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setPhysicsEngineParameter(numSolverIterations=150, fixedTimeStep=SIM_DT)
    p.setGravity(0, 0, 0)


def setup_ball(pos):
    """Spawn the ball with compliant contact (matches the finger pads)."""
    ball = spawn_ball(pos)
    p.changeVisualShape(ball, -1, rgbaColor=[1.0, 0.3, 0.3, 1])
    p.changeDynamics(ball, -1, mass=0.065, linearDamping=0.0, angularDamping=0.0,
                     restitution=BALL_RESTITUTION, lateralFriction=BALL_FRICTION,
                     contactStiffness=CONTACT_STIFFNESS, contactDamping=CONTACT_DAMPING)
    p.resetBaseVelocity(ball, [0, 0, 0], [0, 0, 0])
    return ball

# the 26 directions on the {-1,0,1}^3 sphere (excluding origin), unit-normalized
DIRS_26 = [np.array(v, float) / np.linalg.norm(v)
           for v in itertools.product((-1, 0, 1), repeat=3) if any(v)]


# --------------------------------------------------------------------------- #
class FixedGripper:
    """A gripper URDF loaded on a FIXED base with the arm held in the catch
    pose. Discovers finger joints, drives the chosen close strategy, exposes the
    EE/cup geometry."""

    def __init__(self, urdf_path):
        self.body = p.loadURDF(urdf_path, basePosition=list(BASE_POS),
                               useFixedBase=True)
        self.shoulder = self.elbow = self.ee_link = -1
        self.yale_cfg = yale_hand.YaleConfig()
        self.prb_cfg = (yale_prb.PRBConfig(inertia_scale=PRB_INERTIA_OVERRIDE)
                        if PRB_INERTIA_OVERRIDE is not None
                        else yale_prb.PRBConfig())
        fseg = {}
        for j in range(p.getNumJoints(self.body)):
            info = p.getJointInfo(self.body, j)
            name = info[1].decode()
            child = info[12].decode()
            if name == "shoulder_joint":
                self.shoulder = j
            elif name == "elbow_joint":
                self.elbow = j
            elif name.startswith("finger") and "_seg" in name:
                fid = int(name[len("finger"):].split("_")[0])
                sid = int(name.split("_seg")[1].split("_")[0])
                fseg.setdefault(fid, {})[sid] = j
            if child == "end_effector":
                self.ee_link = j
        self.finger_joints = [[fseg[f][s] for s in sorted(fseg[f])]
                              for f in sorted(fseg)]
        self.finger_links = [j for segs in self.finger_joints for j in segs]
        # arm in catch pose, held rigid
        p.resetJointState(self.body, self.shoulder, SHOULDER_HOLD)
        p.resetJointState(self.body, self.elbow, ELBOW_HOLD)

    def hold_arm_rigid(self):
        for j, tgt in ((self.shoulder, SHOULDER_HOLD), (self.elbow, ELBOW_HOLD)):
            p.setJointMotorControl2(self.body, j, p.POSITION_CONTROL,
                                    targetPosition=tgt, force=50.0,
                                    positionGain=0.6, velocityGain=1.0)

    def set_ready(self, ready_pose):
        for segs in self.finger_joints:
            for k, j in enumerate(segs):
                p.resetJointState(self.body, j, ready_pose[k])

    def set_finger_dynamics(self):
        for link in self.finger_links:
            p.changeDynamics(self.body, link, lateralFriction=PAD_FRICTION,
                             restitution=BALL_RESTITUTION,
                             contactStiffness=CONTACT_STIFFNESS,
                             contactDamping=CONTACT_DAMPING)

    def prep_strategy(self, strategy):
        """One-time motor setup for torque-driven strategies."""
        if strategy == "tendon":
            for j in self.finger_links:
                p.changeDynamics(self.body, j, jointDamping=0.0)
                p.setJointMotorControl2(self.body, j, p.VELOCITY_CONTROL,
                                        force=0.0)
        elif strategy == "prb":
            # faithful PRB Yale: regularize the near-massless-finger inertia
            # (stated ceiling) + free the motors so pure torque governs the joints.
            yale_prb.regularize_inertia(self.body, self.finger_links,
                                        self.prb_cfg.inertia_scale)
            yale_prb.prep(self.body, self.finger_joints)

    def apply_close(self, strategy, ball_id=None, progress=1.0):
        """Apply the close command for one step.

        `fixed`/`compliant`/`soft` servo toward the validated CLOSE_POSE and
        differ only in compliance (force cap / gain). `under` is a per-joint
        deep-curl stand-in (no coupling). `prb` is the FAITHFUL PRB Yale mechanism
        (`src/yale_prb.py`): flexure return springs + a constant-tension tendon
        (ramped `progress`), self-distribution EMERGENT from force balance with NO
        contact-reading. `yale` is the OLD contact-reading stand-in
        (`src/yale_hand.py`, reads `ball_id` contacts to script the redistribution)
        — kept for the record; use `prb` for scoring the mechanism."""
        if strategy == "prb":
            pull = min(1.0, progress / 0.7) * self.prb_cfg.pull_max
            yale_prb.actuate(self.body, self.finger_joints, pull, self.prb_cfg)
            return
        if strategy == "yale":
            d_act = min(1.0, progress / 0.6) * self.yale_cfg.d_max
            yale_hand.actuate(self.body, self.finger_joints, ball_id, d_act,
                              self.yale_cfg)
            return
        if strategy == "fixed":
            target, force, kp = CLOSE_POSE, FIX_TORQUE, FIX_KP
        elif strategy == "compliant":
            target, force, kp = CLOSE_POSE, COMPLIANT_FORCE, FIX_KP
        elif strategy == "soft":
            target, force, kp = CLOSE_POSE, SOFT_FORCE, SOFT_KP
        elif strategy == "under":
            target, force, kp = UNDER_DEEP, UNDER_FORCE, FIX_KP
        elif strategy == "tendon":   # constant-torque (record only, ill-conditioned)
            for segs in self.finger_joints:
                for j in segs:
                    thd = p.getJointState(self.body, j)[1]
                    p.setJointMotorControl2(self.body, j, p.TORQUE_CONTROL,
                                            force=TENDON_TAU - JOINT_DAMP * thd)
            return
        else:
            raise ValueError(strategy)
        for segs in self.finger_joints:
            for k, j in enumerate(segs):
                p.setJointMotorControl2(
                    self.body, j, p.POSITION_CONTROL,
                    targetPosition=target[k], force=force,
                    positionGain=kp, velocityGain=FIX_KD)

    def ee_world(self):
        return np.array(p.getLinkState(self.body, self.ee_link,
                                       computeForwardKinematics=1)[4])

    def cup_world(self):
        # arm straight down -> cup direction is world -z
        return self.ee_world() + np.array([0.0, 0.0, -CUP_DEPTH])


def ball_radius(ball):
    lo, hi = p.getAABB(ball, -1)
    return 0.5 * (hi[2] - lo[2])


def _draw_hud(frame, lines, color=(255, 255, 60)):
    """Overlay text metric lines on a frame (so the video shows the numbers)."""
    from PIL import Image, ImageDraw
    img = Image.fromarray(frame)
    d = ImageDraw.Draw(img)
    y = 6
    for ln in lines:
        d.text((9, y + 1), ln, fill=(0, 0, 0))      # shadow for legibility
        d.text((8, y), ln, fill=color)
        y += 15
    return np.array(img)


def run_cell(strategy, n_fingers, offset_m, direction, ready="splayed",
             verbose=False, quality=False, seed=None):
    """Seat a ball at (offset_m, direction) in the cup, close with `strategy`,
    then score the 26-direction disturbance battery. Returns a result dict.

    `direction` in {"finger","gap","outside"}; "outside" places the ball
    `offset_m` laterally OUTSIDE the cup (negative control). The harness owns the
    PyBullet connection (caller must not be connected).

    `quality=True` additionally computes the CONTINUOUS hold-quality metrics
    (§2.1): escape-margin (min dislodging accel over all directions), centering
    error (ball<->cup), # fingers in contact, and contact symmetry. In quality
    mode the binary `score` is derived from the escape-margin sweep (survived =
    #directions whose margin >= 2.5 g) so the two never disagree.

    `seed` (optional) perturbs the initial ball placement by a sub-mm random
    offset — used by the convergence check to confirm the metric is not on a
    knife-edge (the iteration-1 artifact was a knife-edge)."""
    p.connect(p.DIRECT)
    try:
        setup_physics()                     # finer substep + compliant contact
        urdf = variants.ensure_variant(n_fingers)
        g = FixedGripper(urdf)
        ready_pose = READY_CURLED if ready == "curled" else READY_SPLAYED
        g.set_ready(ready_pose)
        g.set_finger_dynamics()
        g.prep_strategy(strategy)

        # offset direction in the cup plane (xy). Fingers sit at azimuths
        # phi = 2*pi*i/N + pi/2, so finger 0 points +y. "finger" = toward a
        # finger (+y); "gap" = bisector between two fingers.
        if direction == "finger":
            az = math.pi / 2
        elif direction == "gap":
            az = math.pi / 2 + math.pi / n_fingers
        else:  # outside (negative control) — same as "gap" bearing, far out
            az = math.pi / 2 + math.pi / n_fingers
        off = offset_m * np.array([math.cos(az), math.sin(az), 0.0])
        if seed is not None:
            jitter = np.random.default_rng(seed).normal(0, 3e-4, 3)  # ~0.3 mm
            jitter[2] = 0.0
            off = off + jitter

        cup = g.cup_world()
        ball = setup_ball(cup + off)
        rad = ball_radius(ball)

        # --- close + settle (gravity off) ---
        n_close = (CLOSE_STEPS + SETTLE_STEPS) * SUBSTEP
        for s in range(n_close):
            g.hold_arm_rigid()
            g.apply_close(strategy, ball_id=ball, progress=s / n_close)
            p.stepSimulation()

        seated = np.array(p.getBasePositionAndOrientation(ball)[0])
        nf = _fingers_touching(g, ball)
        # seating offset of the ball from the cup center after the close
        seat_off = float(np.linalg.norm(seated - cup))
        res = {"strategy": strategy, "n": n_fingers, "offset": offset_m,
               "dir": direction, "ready": ready, "seated_nf": nf,
               "seat_off": seat_off, "ball_r": rad}

        state = p.saveState()
        if quality:
            # --- CONTINUOUS quality metrics (measured at the settled instant) ---
            ncf, npts, sym, resR, per_f = _contact_analysis(g, ball, seated)
            flex = _finger_flexions_generic(g)
            esc_margin, margins, weakest = _escape_margin(g, strategy, ball,
                                                          seated, state)
            rattle = _rattle(g, strategy, ball, seated, state, RATTLE_G * G)
            survived = sum(1 for m in margins if m >= GACC)
            score = survived / len(DIRS_26)
            max_disp_all = ESCAPE_DELTA if survived < len(DIRS_26) else 0.0
            # pull-in: how much the close DRAGGED the ball toward the cup center
            # (injected offset - residual centering error). >0 = re-centered; ~0 =
            # ball stayed put (rigid close just holds where it landed); <0 = pushed
            # out. THIS is the axis an adaptive/compliant hand can win on.
            pull_in = offset_m - seat_off
            res.update({
                "score": score, "survived": survived,
                "escape_margin": esc_margin,            # m/s^2 (min over dirs)
                "escape_margin_g": esc_margin / G,
                "margins": margins, "weakest_dir": weakest,
                "rattle": rattle,                       # m, worst residual @ 2 g
                "injected_offset": offset_m, "pull_in": pull_in,
                "n_contact_fingers": ncf, "n_contact_points": npts,
                "symmetry": sym, "resultant": resR,
                "per_finger_pts": per_f, "flexions": flex,
                "max_disp": max_disp_all})
            if verbose:
                print(f"strategy={strategy} n={n_fingers} off={offset_m*100:.1f}cm "
                      f"dir={direction} ready={ready}\n"
                      f"  QUALITY: escape-margin={esc_margin/G:.2f} g "
                      f"({esc_margin:.1f} m/s^2, weakest bearing) | "
                      f"rattle@2g={rattle*100:.2f} cm (worst residual)\n"
                      f"  centering: injected={offset_m*100:.2f}cm -> err="
                      f"{seat_off*100:.2f}cm  PULL-IN={pull_in*100:+.2f}cm | "
                      f"contact-fingers={ncf} pts={npts} symmetry={sym:.2f}\n"
                      f"  per-finger flex(rad)={['%.2f'%x for x in flex]} "
                      f"contacts/finger={dict(per_f)}\n"
                      f"  binary score={score:.2f} ({survived}/26 held@2.5g)")
        else:
            # --- binary form-closure battery (26 dirs @ 2.5 g) — UNCHANGED ---
            survived = 0
            max_disp_all = 0.0
            for d in DIRS_26:
                p.restoreState(state)
                p.setGravity(*(d * GACC))
                max_disp = 0.0
                for _ in range(WINDOW_STEPS * SUBSTEP):
                    g.hold_arm_rigid()
                    g.apply_close(strategy, ball_id=ball, progress=1.0)
                    p.stepSimulation()
                    pos = np.array(p.getBasePositionAndOrientation(ball)[0])
                    max_disp = max(max_disp, float(np.linalg.norm(pos - seated)))
                max_disp_all = max(max_disp_all, max_disp)
                if max_disp < ESCAPE_DELTA:
                    survived += 1
            score = survived / len(DIRS_26)
            res.update({"score": score, "survived": survived,
                        "max_disp": max_disp_all})
            if verbose:
                print(f"strategy={strategy} n={n_fingers} off={offset_m*100:.1f}cm "
                      f"dir={direction} ready={ready} | score={score:.2f} "
                      f"({survived}/26) seated_nf={nf} seat_off={seat_off*100:.1f}cm "
                      f"max_disp={max_disp_all*100:.1f}cm ball_r={rad*100:.1f}cm")
        p.removeState(state)
        return res
    finally:
        p.disconnect()


def _fingers_touching(g, ball):
    pts = p.getContactPoints(bodyA=g.body, bodyB=ball)
    touched = set()
    for c in pts:
        for fid, segs in enumerate(g.finger_joints):
            if c[3] in segs:
                touched.add(fid)
    return len(touched)


# --------------------------------------------------------------------------- #
# Hold-QUALITY metrics (iteration-2 §2.1). The binary form-closure score
# ("survived N/26 at a fixed 2.5 g") over-credits precarious holds: a ball
# pinned by one off-center finger scores the same as a deep symmetric wrap
# (iteration-1's core miss, reflection §4.3). These are CONTINUOUS quality
# signals cross-checked against rendered frames (never reported without one).
# --------------------------------------------------------------------------- #

# escape-margin sweep: bisect the disturbance magnitude PER direction to find the
# minimum accel that dislodges the ball; the hold's escape-margin is the
# min-over-directions (its weakest bearing). Continuous, not pass/fail at 2.5 g.
A_MAX_ESCAPE = 10.0 * G      # m/s^2 cap on the margin search (holds above read ">=cap")
N_BISECT = 6                 # bisection iters -> ~A_MAX/64 = 1.5 m/s^2 resolution
RATTLE_G = 2.0               # sub-dislodging pulse (g) for the within-band metric
                             # (below the 2.5 g battery so a caged ball never
                             # escapes it; how far it RATTLES grades seating depth)


def _finger_flexions_generic(g):
    """Per-finger total flexion above the splayed open pose (rad). Works for any
    strategy (the yale module has its own; this is the geometric read used by the
    HUD + symmetry cross-check for fixed/compliant/soft/under)."""
    open_pose = READY_SPLAYED
    open_sum = sum(open_pose[:len(g.finger_joints[0])])
    out = []
    for segs in g.finger_joints:
        ang = [p.getJointState(g.body, j)[0] for j in segs]
        out.append(sum(ang) - open_sum)
    return out


def _contact_analysis(g, ball, center):
    """Real contact points (getContactPoints), and how evenly they surround the
    ball. Returns (n_fingers, n_points, symmetry, resultant, per_finger_pts).

    contact SYMMETRY (the headline `symmetry`) is the AZIMUTHAL balance: 1 - |R_xy|
    where R_xy = mean over all ball-surface contacts of the UNIT direction from the
    ball center to the contact, projected into the cup (xy) plane. Contacts spread
    evenly around the ring cancel (|R_xy|~0 -> symmetry~1 = surrounded); a one-sided
    graze piles up on one bearing (|R_xy|~1 -> symmetry~0 = precarious). We use the
    AZIMUTHAL (not full-3D) resultant because this cup opens DOWNWARD: every finger
    contacts the ball at or below its equator and NOTHING touches the top, so a 3D
    resultant always has a large -z bias (|R_3d|~0.6 even for a perfect centered
    hold) that swamps the lateral one-sidedness we actually want to detect. The 3D
    resultant is still returned (as `resultant`) for the record. Reported alongside
    n_fingers so a high symmetry from a 2-point graze can't masquerade as good."""
    pts = p.getContactPoints(bodyA=g.body, bodyB=ball)
    center = np.asarray(center, float)
    dirs = []
    per_finger = {}
    for c in pts:
        link = c[3]
        pos_on_ball = np.array(c[6], float)          # positionOnB (world)
        v = pos_on_ball - center
        n = np.linalg.norm(v)
        if n < 1e-9:
            continue
        dirs.append(v / n)
        for fid, segs in enumerate(g.finger_joints):
            if link in segs:
                per_finger.setdefault(fid, 0)
                per_finger[fid] += 1
    n_points = len(dirs)
    if n_points == 0:
        return 0, 0, 0.0, 1.0, per_finger
    dirs = np.array(dirs)
    R3 = np.linalg.norm(np.mean(dirs, axis=0))        # full 3D resultant (record)
    xy = dirs[:, :2]                                  # azimuthal projection
    norms = np.linalg.norm(xy, axis=1, keepdims=True)
    xy_unit = xy / np.clip(norms, 1e-9, None)         # re-normalize in the plane
    Rxy = np.linalg.norm(np.mean(xy_unit, axis=0))    # azimuthal resultant in [0,1]
    symmetry = 1.0 - Rxy
    return len(per_finger), n_points, float(symmetry), float(R3), per_finger


def _escapes_under(g, strategy, ball, seated, accel_vec, state):
    """Restore the settled state, apply a constant disturbance accel, step the
    window; return (escaped_bool, max_disp). Early-exits on escape."""
    p.restoreState(state)
    p.setGravity(*accel_vec)
    max_disp = 0.0
    for _ in range(WINDOW_STEPS * SUBSTEP):
        g.hold_arm_rigid()
        g.apply_close(strategy, ball_id=ball, progress=1.0)
        p.stepSimulation()
        pos = np.array(p.getBasePositionAndOrientation(ball)[0])
        max_disp = max(max_disp, float(np.linalg.norm(pos - seated)))
        if max_disp >= ESCAPE_DELTA:
            return True, max_disp
    return False, max_disp


def _rattle(g, strategy, ball, seated, state, accel):
    """Within-band graded companion to the (saturated) escape-margin: apply a
    FIXED sub-dislodging accel in every direction from the settled state and
    return the WORST residual displacement (m). A deeply-seated symmetric hold
    barely moves; a precarious one-sided hold rattles/shifts more — a continuous
    signal INSIDE the caged band, where escape-margin saturates at the cap."""
    worst = 0.0
    for d in DIRS_26:
        _, md = _escapes_under(g, strategy, ball, seated, d * accel, state)
        worst = max(worst, md)
    return worst


def _escape_margin(g, strategy, ball, seated, state):
    """Per-direction bisection for the minimum disturbance accel (m/s^2) that
    dislodges the ball; the hold's escape-margin is the min over all 26
    directions (weakest bearing). Returns (min_margin, margins_by_dir, weakest).
    A direction that still holds at A_MAX_ESCAPE is recorded as A_MAX_ESCAPE
    (">=cap")."""
    margins = []
    weakest = None
    min_margin = A_MAX_ESCAPE
    for d in DIRS_26:
        esc_hi, _ = _escapes_under(g, strategy, ball, seated, d * A_MAX_ESCAPE, state)
        if not esc_hi:
            margins.append(A_MAX_ESCAPE)          # held even at the cap
            continue
        lo, hi = 0.0, A_MAX_ESCAPE                 # lo holds, hi escapes
        for _ in range(N_BISECT):
            mid = 0.5 * (lo + hi)
            esc, _ = _escapes_under(g, strategy, ball, seated, d * mid, state)
            if esc:
                hi = mid
            else:
                lo = mid
        margins.append(hi)
        if hi < min_margin:
            min_margin = hi
            weakest = d
    return min_margin, margins, weakest


# --------------------------------------------------------------------------- #
def self_test():
    print("=== Phase 0 self-validation ===")
    ok = True

    # (a) determinism
    scores = [run_cell("fixed", 4, 0.0, "finger")["score"] for _ in range(3)]
    det = (scores[0] == scores[1] == scores[2])
    print(f"(a) determinism : scores={scores}  -> {'PASS' if det else 'FAIL'}")
    ok &= det

    # (b) positive control: centered ball, current 4-finger fixed-pose close
    pos = run_cell("fixed", 4, 0.0, "finger", verbose=True)
    pos_ok = pos["score"] >= 0.80
    print(f"(b) positive ctrl: centered fixed-pose score={pos['score']:.2f} "
          f"-> {'PASS' if pos_ok else 'FAIL'} (need >=0.80)")
    ok &= pos_ok

    # (c) negative control: ball 8 cm outside the cup
    neg = run_cell("fixed", 4, 0.08, "outside", verbose=True)
    neg_ok = neg["score"] == 0.0
    print(f"(c) negative ctrl: 8cm-outside score={neg['score']:.2f} "
          f"-> {'PASS' if neg_ok else 'FAIL'} (need 0.00)")
    ok &= neg_ok

    print(f"\nself-validation: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def grid():
    offsets = [0.0, 0.015, 0.025, 0.035]
    dirs = ["finger", "gap"]
    strategies = ["fixed", "compliant", "soft"]
    ns = [4, 6, 8]
    readies = ["splayed", "curled"]
    print(f"{'strat':>7} {'n':>2} {'ready':>7} {'dir':>6} | "
          + " ".join(f"{o*100:4.1f}cm" for o in offsets))
    rows = []
    for strat in strategies:
        for n in ns:
            for ready in readies:
                for dr in dirs:
                    cells = [run_cell(strat, n, o, dr, ready) for o in offsets]
                    sc = [c["score"] for c in cells]
                    rows.extend(cells)
                    print(f"{strat:>7} {n:>2} {ready:>7} {dr:>6} | "
                          + " ".join(f"{s:6.2f}" for s in sc))
    # baseline = current 4-finger fixed-pose splayed
    base = {(c["dir"], c["offset"]): c["score"] for c in rows
            if c["strategy"] == "fixed" and c["n"] == 4 and c["ready"] == "splayed"}
    print("\n--- summary: score at offset>=2.5cm (robust-to-uncertainty band) ---")
    agg = {}
    for c in rows:
        if c["offset"] >= 0.025:
            key = (c["strategy"], c["n"], c["ready"])
            agg.setdefault(key, []).append(c["score"])
    ranked = sorted(agg.items(), key=lambda kv: -np.mean(kv[1]))
    for (strat, n, ready), scs in ranked:
        print(f"  {strat:>7} n={n} {ready:>7}: mean off>=2.5cm = {np.mean(scs):.2f}")
    best = ranked[0]
    print(f"\nBEST off-center config: {best[0]} (mean {np.mean(best[1]):.2f})")
    print(f"current-close baseline off>=2.5cm: "
          f"{np.mean([s for (d,o),s in base.items() if o>=0.025]):.2f}")
    return 0


def quality_grid(strategies=("fixed", "compliant", "soft", "yale"),
                 ns=(4, 6, 8), offsets=(0.0, 0.015, 0.025, 0.035),
                 dirs=("finger", "gap"), compare_strat="yale"):
    """§2.2 — re-score strategies on the CONTINUOUS quality metric per
    offset x direction x finger-count. Reports escape-margin (the discriminating
    signal — a precarious hold has a low margin even if it survives 2.5 g),
    centering error, #contact fingers, and contact symmetry for every cell, then
    answers the fixed-vs-Yale question directly. All cells at the converged
    numerics (substep 4 + compliant pads)."""
    print("=== §2.2 QUALITY re-score (converged numerics: substep "
          f"{SUBSTEP}, compliant pads) ===")
    print("legend: EM=escape-margin(g,min/26) PI=PULL-IN(cm,+re-centered) "
          "RT=rattle@2g(cm,worst residual) CE=centering-err(cm) "
          "CF=#contact-fingers SY=symmetry(1=surrounded,0=one-sided) SC=score")
    hdr = f"{'strat':>9} {'n':>2} {'dir':>6} | " + " ".join(
        f"{o*100:>5.1f}cm" for o in offsets)
    rows = []
    for strat in strategies:
        for n in ns:
            for dr in dirs:
                cells = [run_cell(strat, n, o, dr, quality=True) for o in offsets]
                rows.extend(cells)
                print("\n" + hdr)
                print(f"{strat:>9} {n:>2} {dr:>6} EM| " + " ".join(
                    f"{c['escape_margin_g']:>7.2f}" for c in cells))
                print(f"{'':>9} {'':>2} {'':>6} PI| " + " ".join(
                    f"{c['pull_in']*100:>+7.2f}" for c in cells))
                print(f"{'':>9} {'':>2} {'':>6} RT| " + " ".join(
                    f"{c['rattle']*100:>7.2f}" for c in cells))
                print(f"{'':>9} {'':>2} {'':>6} CE| " + " ".join(
                    f"{c['seat_off']*100:>7.2f}" for c in cells))
                print(f"{'':>9} {'':>2} {'':>6} CF| " + " ".join(
                    f"{c['n_contact_fingers']:>7d}" for c in cells))
                print(f"{'':>9} {'':>2} {'':>6} SY| " + " ".join(
                    f"{c['symmetry']:>7.2f}" for c in cells))
                print(f"{'':>9} {'':>2} {'':>6} SC| " + " ".join(
                    f"{c['score']:>7.2f}" for c in cells))

    # --- the fixed-vs-<compare_strat> quality question, answered with numbers ---
    # PULL-IN is the axis on which an adaptive hand can win — lead with it.
    cs = compare_strat
    cl = cs[:2]
    print(f"\n=== fixed vs {cs} on QUALITY (mean over n x dir, per offset) ===")
    print(f"{'offset':>7} | {'fx PULLIN':>9} {cl+' PULLIN':>9} | "
          f"{'fx rattle':>9} {cl+' rattle':>9} | {'fx SY':>6} {cl+' SY':>6} | "
          f"{'fx CF':>6} {cl+' CF':>6} | {'fx SC':>6} {cl+' SC':>6}")
    for o in offsets:
        def agg(strat, key):
            xs = [c[key] for c in rows if c["strategy"] == strat and c["offset"] == o]
            return np.mean(xs) if xs else float("nan")
        print(f"{o*100:>6.1f}cm | "
              f"{agg('fixed','pull_in')*100:>+9.2f} {agg(cs,'pull_in')*100:>+9.2f} | "
              f"{agg('fixed','rattle')*100:>9.2f} {agg(cs,'rattle')*100:>9.2f} | "
              f"{agg('fixed','symmetry'):>6.2f} {agg(cs,'symmetry'):>6.2f} | "
              f"{agg('fixed','n_contact_fingers'):>6.2f} {agg(cs,'n_contact_fingers'):>6.2f} | "
              f"{agg('fixed','score'):>6.2f} {agg(cs,'score'):>6.2f}")
    print(f"\n(PULL-IN>0 => the close dragged the ball toward center; ~0 => it "
          f"held where the ball landed. If {cs}'s PULL-IN does not exceed fixed's, "
          f"the adaptive hand does not win on re-centering in this sim.)")
    return 0


def converge_cell(strategy, n_fingers, offset_m, direction, ready="splayed"):
    """§2.3 — convergence table for ONE contact-rich cell. Vary (a) the sim
    substep (timestep), (b) the contact-model stiffness/damping, and (c) the seed
    (sub-mm ball-placement jitter), and confirm the quality metric CONVERGES /
    is stable. A quality number without this table does not count (iteration-1's
    determinism-mistaken-for-convergence artifact, §26). Prints a table."""
    global SUBSTEP, SIM_DT, CONTACT_STIFFNESS, CONTACT_DAMPING
    base_ss, base_k, base_c = SUBSTEP, CONTACT_STIFFNESS, CONTACT_DAMPING
    print(f"=== §2.3 convergence: {strategy} n={n_fingers} "
          f"off={offset_m*100:.1f}cm dir={direction} ===")
    print(f"{'variation':>22} | {'EM(g)':>7} {'PI(cm)':>7} {'RT(cm)':>7} "
          f"{'CF':>3} {'SY':>5} {'score':>6}")

    def show(tag, c):
        print(f"{tag:>22} | {c['escape_margin_g']:>7.2f} "
              f"{c['pull_in']*100:>+7.2f} {c['rattle']*100:>7.2f} "
              f"{c['n_contact_fingers']:>3d} {c['symmetry']:>5.2f} "
              f"{c['score']:>6.2f}")

    def one(tag, seed=None):
        c = run_cell(strategy, n_fingers, offset_m, direction, ready,
                     quality=True, seed=seed)
        show(tag, c)
        return c

    results = {}
    # (a) timestep
    for ss in (2, 4, 8):
        SUBSTEP, SIM_DT = ss, DT / ss
        results[f"substep {ss} (1/{240*ss})"] = one(f"substep {ss} (1/{240*ss})")
    SUBSTEP, SIM_DT = base_ss, DT / base_ss
    # (b) contact model (softer/stiffer pads by 3x)
    for scale in (0.33, 3.0):
        CONTACT_STIFFNESS, CONTACT_DAMPING = base_k * scale, base_c * scale
        results[f"contact x{scale:.2g}"] = one(f"contact x{scale:.2g}")
    CONTACT_STIFFNESS, CONTACT_DAMPING = base_k, base_c
    # (c) seed (sub-mm ball jitter)
    for sd in (1, 2, 3):
        results[f"seed {sd} (+jitter)"] = one(f"seed {sd} (+jitter)", seed=sd)

    # convergence verdict: substep 4 vs 8 agreement + seed spread
    em = [results[k]["escape_margin_g"] for k in results]
    em4 = results[f"substep 4 (1/960)"]["escape_margin_g"]
    em8 = results[f"substep 8 (1/1920)"]["escape_margin_g"]
    seed_em = [results[f"seed {s} (+jitter)"]["escape_margin_g"] for s in (1, 2, 3)]
    print(f"\n  substep 4 vs 8 escape-margin: {em4:.2f}g vs {em8:.2f}g "
          f"(|d|={abs(em4-em8):.2f}g)")
    print(f"  seed spread (jitter) escape-margin: "
          f"{min(seed_em):.2f}..{max(seed_em):.2f}g (range {max(seed_em)-min(seed_em):.2f}g)")
    conv = abs(em4 - em8) <= 1.0 and (max(seed_em) - min(seed_em)) <= 1.5
    print(f"  CONVERGED: {'YES' if conv else 'NO — knife-edge, do not trust'}")
    # pull-in SIGN convergence — the magnitude/EM can be a knife-edge while the
    # DIRECTION of re-centering is robust (the honest soft claim, lead steer #4).
    pis = [results[k]["pull_in"] * 100 for k in results]
    all_pos = all(x > 0.05 for x in pis)
    all_neg = all(x < -0.05 for x in pis)
    sign = ("robustly POSITIVE (re-centers)" if all_pos
            else "robustly NEGATIVE (pushes out)" if all_neg
            else "SIGN NOT stable")
    print(f"  pull-in across all variations: {min(pis):+.2f}..{max(pis):+.2f} cm "
          f"-> sign {sign}")
    SUBSTEP, SIM_DT = base_ss, DT / base_ss
    CONTACT_STIFFNESS, CONTACT_DAMPING = base_k, base_c
    return 0


def paired_converge(strat_a, strat_b, n_fingers, offset_m, direction,
                    ready="splayed"):
    """§2.3 PAIRED convergence (lead steer): the claim 'A re-centers MORE than B'
    is only earned if the PAIRED DELTA (A.pull_in - B.pull_in) at the SAME
    offset/dir/n/perturbation converges POSITIVE. A single cell can show A's band
    overlapping B's, so test the delta per-perturbation (same substep/contact/seed
    for both -> the seed jitter is identical, a fair pairing) and report whether
    the delta stays > 0 across ALL perturbations."""
    global SUBSTEP, SIM_DT, CONTACT_STIFFNESS, CONTACT_DAMPING
    base_ss, base_k, base_c = SUBSTEP, CONTACT_STIFFNESS, CONTACT_DAMPING
    print(f"=== §2.3 PAIRED delta ({strat_a}-{strat_b}) n={n_fingers} "
          f"off={offset_m*100:.1f}cm dir={direction} ===")
    print(f"{'variation':>22} | {strat_a[:5]+' PI':>9} {strat_b[:5]+' PI':>9} "
          f"{'DELTA':>7}")

    def pair(tag, seed=None):
        a = run_cell(strat_a, n_fingers, offset_m, direction, ready,
                     quality=True, seed=seed)["pull_in"] * 100
        b = run_cell(strat_b, n_fingers, offset_m, direction, ready,
                     quality=True, seed=seed)["pull_in"] * 100
        d = a - b
        print(f"{tag:>22} | {a:>+9.2f} {b:>+9.2f} {d:>+7.2f}")
        return d

    deltas = []
    for ss in (2, 4, 8):
        SUBSTEP, SIM_DT = ss, DT / ss
        deltas.append(pair(f"substep {ss} (1/{240*ss})"))
    SUBSTEP, SIM_DT = base_ss, DT / base_ss
    for scale in (0.33, 3.0):
        CONTACT_STIFFNESS, CONTACT_DAMPING = base_k * scale, base_c * scale
        deltas.append(pair(f"contact x{scale:.2g}"))
    CONTACT_STIFFNESS, CONTACT_DAMPING = base_k, base_c
    for sd in (1, 2, 3):
        deltas.append(pair(f"seed {sd} (+jitter)", seed=sd))

    dmin, dmax = min(deltas), max(deltas)
    if dmin > 0.3:
        verdict = f"CONVERGENT POSITIVE -> '{strat_a} re-centers MORE than {strat_b}' EARNED"
    elif dmax < -0.3:
        verdict = f"CONVERGENT NEGATIVE -> '{strat_b} re-centers more' "
    else:
        verdict = (f"OVERLAPS 0 -> NOT convergently distinguishable; "
                   f"downgrade to 'sign positive, magnitude not separable from {strat_b}'")
    print(f"  paired delta across all variations: {dmin:+.2f}..{dmax:+.2f} cm -> {verdict}")
    SUBSTEP, SIM_DT = base_ss, DT / base_ss
    CONTACT_STIFFNESS, CONTACT_DAMPING = base_k, base_c
    return 0


def boundary_scan(strategy, n_fingers, direction, ready="splayed"):
    """§2.3 boundary check — the caged->escaped transition is exactly where §26's
    artifact lived (the verdict flipped with the timestep). Sweep offsets across
    the cliff at substeps {2,4,8}; report each substep's boundary offset (largest
    still-caged) and FLAG any offset whose caged verdict is not timestep-stable.
    A boundary that shifts with the timestep is untrustworthy — do not pick a
    winner from it."""
    global SUBSTEP, SIM_DT
    base_ss = SUBSTEP
    offs = [0.035, 0.040, 0.043, 0.045, 0.048, 0.050]
    substeps = [2, 4, 8]

    def caged(c):                       # majority form-closure + real contact
        return c["score"] >= 0.5 and c["n_contact_fingers"] >= 2

    print(f"=== §2.3 boundary scan: {strategy} n={n_fingers} dir={direction} ===")
    print("verdict grid (C=caged, .=escaped); columns = offset cm")
    print(f"{'substep':>10} | " + " ".join(f"{o*100:>4.1f}" for o in offs))
    grid_v = {}
    for ss in substeps:
        SUBSTEP, SIM_DT = ss, DT / ss
        verds = []
        for o in offs:
            c = run_cell(strategy, n_fingers, o, direction, ready, quality=True)
            verds.append(caged(c))
        grid_v[ss] = verds
        print(f"    1/{240*ss:<5d} | " + " ".join(
            f"{'   C' if v else '   .'}" for v in verds))
    SUBSTEP, SIM_DT = base_ss, DT / base_ss

    # boundary = largest caged offset per substep; flag per-offset disagreement
    print("\n  boundary (largest caged offset) per substep:")
    for ss in substeps:
        caged_offs = [offs[i] for i, v in enumerate(grid_v[ss]) if v]
        b = max(caged_offs) * 100 if caged_offs else 0.0
        print(f"    1/{240*ss}: {b:.1f} cm")
    unstable = [offs[i] * 100 for i in range(len(offs))
                if len({grid_v[ss][i] for ss in substeps}) > 1]
    if unstable:
        print(f"  ⚠ NOT timestep-stable at offsets (cm): {unstable} "
              f"— verdict flips with substep; DO NOT trust the boundary here.")
    else:
        print("  boundary is timestep-stable across 1/480..1/1920 (converged).")
    return 0


def migration_trace(strategies=("fixed", "soft"), n_fingers=4, offset_m=0.025,
                    direction="finger", ready="splayed", samples=12,
                    out_dir="docs/cage_frames/iter2", save_frames=True):
    """CAUSAL check for the pull-in claim (reviewer D5): does the ball MIGRATE to
    center DURING the close (a progressive squeeze), or SNAP in one step? Records
    the ball's centering-err vs close progress for each strategy and prints the
    trajectory; optionally saves under-view frames at 0/33/66/100% so the
    migration is visible. If soft's centering-err decreases GRADUALLY over many
    steps while fixed's stays flat, the 'gentle squeeze toward equilibrium' story
    is verified; a one-step drop would falsify it and the story gets rewritten."""
    import imageio.v2 as imageio
    os.makedirs(out_dir, exist_ok=True)
    print(f"=== CAUSAL: ball migration during close (off={offset_m*100:.1f}cm "
          f"{direction} n={n_fingers}) ===")
    print("centering-err (cm) vs close progress:")
    traces = {}
    dense_traces = {}
    for strat in strategies:
        p.connect(p.DIRECT)
        try:
            setup_physics()
            urdf = variants.ensure_variant(n_fingers)
            g = FixedGripper(urdf)
            g.set_ready(READY_CURLED if ready == "curled" else READY_SPLAYED)
            g.set_finger_dynamics()
            g.prep_strategy(strat)
            az = (math.pi / 2 if direction == "finger"
                  else math.pi / 2 + math.pi / n_fingers)
            off = offset_m * np.array([math.cos(az), math.sin(az), 0.0])
            cup = g.cup_world()
            ball = setup_ball(cup + off)
            ee = g.ee_world()
            view_under = p.computeViewMatrix((0.13, -0.13, ee[2] - 0.40),
                                             (0, 0, ee[2] - 0.05), [0, 0, 1])
            proj = p.computeProjectionMatrixFOV(46, 1.0, 0.02, 4.0)
            n_close = (CLOSE_STEPS + SETTLE_STEPS) * SUBSTEP
            sample_at = {int(k * (n_close - 1) / (samples - 1)) for k in range(samples)}
            # frames DURING the roll window (migration completes in the first
            # ~60 sim steps) + one settled — so the stills show the migration, not
            # four identical settled poses.
            frame_at = {0, 20, 40, 60, n_close - 1}
            # DENSE early sampling (every sim step over the first ~0.3 s) so a
            # physical roll is distinguishable from a single-solver-step teleport
            # artifact — the reviewer-D5 causal test for the pull-in claim.
            dense = set(range(0, 80))
            dense_trace = []
            trace = []
            for s in range(n_close):
                g.hold_arm_rigid()
                g.apply_close(strat, ball_id=ball, progress=s / n_close)
                p.stepSimulation()
                if s in dense:
                    pos = np.array(p.getBasePositionAndOrientation(ball)[0])
                    dense_trace.append((s, float(np.linalg.norm(pos - cup))))
                if s in sample_at:
                    pos = np.array(p.getBasePositionAndOrientation(ball)[0])
                    ce = float(np.linalg.norm(pos - cup))
                    nf = _fingers_touching(g, ball)
                    trace.append((s / n_close, ce, nf))
                if save_frames and s in frame_at:
                    _, _, rgba, _, _ = p.getCameraImage(
                        480, 480, viewMatrix=view_under, projectionMatrix=proj,
                        renderer=p.ER_TINY_RENDERER)
                    fr = np.array(rgba, np.uint8).reshape(480, 480, 4)[:, :, :3]
                    pos = np.array(p.getBasePositionAndOrientation(ball)[0])
                    ce = float(np.linalg.norm(pos - cup))
                    fr = _draw_hud(fr, [
                        f"{strat}  off={offset_m*100:.1f}cm {direction}",
                        f"close {int(100*s/n_close)}%   centering-err {ce*100:.2f}cm",
                        f"fingers touching {_fingers_touching(g, ball)}"])
                    pct = int(round(100 * s / (n_close - 1)))
                    imageio.imwrite(os.path.join(
                        out_dir, f"migrate_{strat}_{direction}_{int(offset_m*1000)}mm_{pct:03d}pct.png"), fr)
            traces[strat] = trace
            dense_traces[strat] = dense_trace
            hdr = "  progress: " + " ".join(f"{t[0]*100:>4.0f}%" for t in trace)
            print(hdr)
            print(f"  {strat:>6} CE: " + " ".join(f"{t[1]*100:>5.2f}" for t in trace))
            print(f"  {strat:>6} nf: " + " ".join(f"{t[2]:>5d}" for t in trace))
            print(f"  {strat:>6} DENSE early CE (sim steps 0..24, cm): "
                  + " ".join(f"{ce*100:.2f}" for _, ce in dense_trace))
        finally:
            p.disconnect()
    # verdict on the DENSE per-sim-step trace (the coarse trace can't tell a
    # physical roll from a teleport — it was sampled after the roll completed).
    for strat, dtr in dense_traces.items():
        ces = [ce for _, ce in dtr]
        total_drop = ces[0] - min(ces)
        steps = [ces[i] - ces[i + 1] for i in range(len(ces) - 1)]
        biggest = max(steps) if steps else 0.0
        frac = (biggest / total_drop) if total_drop > 1e-4 else float("nan")
        # count sim steps over which 10%..90% of the drop happens (roll duration)
        moved = [i for i in range(len(ces)) if ces[0] - ces[i] > 0.1 * total_drop]
        n_roll = (max(moved) - min(moved)) if len(moved) > 1 else 0
        verdict = ("negligible re-centering" if total_drop < 0.005
                   else "GRADUAL roll over %d sim steps (~%.0f ms)" % (
                       n_roll, n_roll * SIM_DT * 1000) if frac < 0.5
                   else "one-step SNAP (<=1 sim step) — SUSPECT, investigate")
        print(f"  {strat}: dense-trace drop {total_drop*100:+.2f}cm, biggest single "
              f"SIM step = {frac*100:.0f}% of it -> {verdict}")
    return 0


def render_quality(strategy, n_fingers, offset_m, direction, ready, out_dir,
                   video=True):
    """§2.4 — legible review evidence for ONE cell, HUD-annotated with the
    CONTINUOUS quality metrics so every reported number has a citable frame.

    Produces, under `out_dir`:
      * a 3x3 grid of still PNGs — key moments {close-mid, SEATED, post-disturbance
        on the weakest bearing} x camera angles {diag, under, side} — each stamped
        with fingers-touching, per-finger flexion, centering-err, symmetry, the
        escape-margin, and HELD/ESCAPED;
      * (video=True) a slow-mo MP4 of the same close from the diag+under pair with
        the live HUD.
    The escape-margin + contact metrics are computed ONCE at the settled instant
    (they are properties of the hold) and stamped on every frame."""
    import imageio.v2 as imageio
    os.makedirs(out_dir, exist_ok=True)
    tag = f"{strategy}_n{n_fingers}_{direction}_{int(offset_m*1000)}mm"
    p.connect(p.DIRECT)
    try:
        setup_physics()
        urdf = variants.ensure_variant(n_fingers)
        g = FixedGripper(urdf)
        g.set_ready(READY_CURLED if ready == "curled" else READY_SPLAYED)
        g.set_finger_dynamics()
        g.prep_strategy(strategy)
        az = (math.pi / 2 if direction == "finger"
              else math.pi / 2 + math.pi / n_fingers)
        off = offset_m * np.array([math.cos(az), math.sin(az), 0.0])
        cup = g.cup_world()
        ball = setup_ball(cup + off)
        ee = g.ee_world()

        # three camera angles (the reviewer rejects single-angle evidence)
        proj = p.computeProjectionMatrixFOV(46, 1.0, 0.02, 4.0)
        cams = {
            "diag": p.computeViewMatrix((0.34, -0.34, ee[2] + 0.10),
                                        (0, 0, ee[2] - 0.04), [0, 0, 1]),
            "under": p.computeViewMatrix((0.13, -0.13, ee[2] - 0.40),
                                         (0, 0, ee[2] - 0.05), [0, 0, 1]),
            "side": p.computeViewMatrix((0.45, 0.0, ee[2] - 0.02),
                                        (0, 0, ee[2] - 0.05), [0, 0, 1]),
        }

        def shot(view):
            _, _, rgba, _, _ = p.getCameraImage(
                560, 560, viewMatrix=view, projectionMatrix=proj,
                renderer=p.ER_TINY_RENDERER)
            return np.array(rgba, np.uint8).reshape(560, 560, 4)[:, :, :3]

        # ---- close + settle, optionally recording a slow-mo video ----
        n_close = (CLOSE_STEPS + SETTLE_STEPS) * SUBSTEP
        writer = mid_frame = None
        if video:
            vpath = os.path.join(out_dir, f"cageQ_{tag}_slowmo.mp4")
            fps = max(1, round((n_close // 2) / 9.0))
            writer = imageio.get_writer(vpath, fps=fps, codec="libx264",
                                        quality=7, macro_block_size=1)
        for s in range(n_close):
            g.hold_arm_rigid()
            g.apply_close(strategy, ball_id=ball, progress=s / n_close)
            p.stepSimulation()
            if s == n_close // 2:
                mid_frame = {k: shot(v) for k, v in cams.items()}
            if writer is not None and s % 2 == 0:
                nf = _fingers_touching(g, ball)
                flex = _finger_flexions_generic(g)
                frame = np.hstack([shot(cams["diag"]), shot(cams["under"])])
                writer.append_data(_draw_hud(frame, [
                    f"{strategy}  off={offset_m*100:.1f}cm  dir={direction}",
                    f"CLOSE   fingers touching: {nf}",
                    "finger flex: " + " ".join(f"{x:+.1f}" for x in flex)]))

        # ---- SEATED instant: the quality metrics (measured once) ----
        seated = np.array(p.getBasePositionAndOrientation(ball)[0])
        ncf, npts, sym, resR, per_f = _contact_analysis(g, ball, seated)
        flex = _finger_flexions_generic(g)
        seat_err = float(np.linalg.norm(seated - cup))
        seated_frame = {k: shot(v) for k, v in cams.items()}

        state = p.saveState()
        esc_margin, margins, weakest = _escape_margin(g, strategy, ball,
                                                      seated, state)
        survived = sum(1 for m in margins if m >= GACC)

        # ---- post-disturbance on the WEAKEST bearing (drive at 2.5 g) ----
        wdir = weakest if weakest is not None else np.array([1.0, 0, 0])
        p.restoreState(state)
        p.setGravity(*(wdir * GACC))
        max_disp = 0.0
        for _ in range(WINDOW_STEPS * SUBSTEP):
            g.hold_arm_rigid()
            g.apply_close(strategy, ball_id=ball, progress=1.0)
            p.stepSimulation()
            pos = np.array(p.getBasePositionAndOrientation(ball)[0])
            max_disp = max(max_disp, float(np.linalg.norm(pos - seated)))
        held = max_disp < ESCAPE_DELTA
        dist_frame = {k: shot(v) for k, v in cams.items()}
        p.removeState(state)
        if writer is not None:
            writer.close()

        # ---- HUD-stamp + save the 3x3 still grid ----
        emg = esc_margin / G
        emtxt = f">={emg:.1f}g" if emg >= (A_MAX_ESCAPE / G - 0.01) else f"{emg:.2f}g"
        common = [
            f"{strategy}  off={offset_m*100:.1f}cm  dir={direction}  n={n_fingers}",
            f"escape-margin: {emtxt} (min/26)   centering-err: {seat_err*100:.2f}cm",
            f"contact-fingers: {ncf}   symmetry: {sym:.2f}   score: {survived}/26",
            "finger flex: " + " ".join(f"{x:+.1f}" for x in flex),
        ]
        moments = {
            "close": (mid_frame, ["MOMENT: mid-close (fingers wrapping)"]),
            "seated": (seated_frame, ["MOMENT: SEATED (metrics measured here)"]),
            "disturb": (dist_frame, [
                f"MOMENT: post-disturbance 2.5g weakest bearing",
                f"ball moved {max_disp*100:.1f}cm   {'HELD' if held else 'ESCAPED'}"]),
        }
        paths = []
        for mname, (frames, extra) in moments.items():
            if frames is None:
                continue
            for cname, fr in frames.items():
                lines = [f"[{mname} | {cname}]"] + common + extra
                out = _draw_hud(fr.copy(), lines,
                                color=(120, 255, 120) if mname == "seated"
                                else (255, 255, 60))
                path = os.path.join(out_dir, f"cageQ_{tag}_{mname}_{cname}.png")
                imageio.imwrite(path, out)
                paths.append(path)
        print(f"§2.4 quality frames for {tag}:")
        print(f"  escape-margin={emtxt}  centering-err={seat_err*100:.2f}cm  "
              f"fingers={ncf}  symmetry={sym:.2f}  score={survived}/26  "
              f"weakest-bearing-held={held}")
        for pth in paths:
            print("  " + os.path.abspath(pth))
        if video:
            print("  " + os.path.abspath(vpath))
        return paths
    finally:
        p.disconnect()


def render(strategy, n_fingers, offset_m, direction, ready, out_dir):
    """Save 2 frames of the closed grasp around an off-center ball."""
    os.makedirs(out_dir, exist_ok=True)
    p.connect(p.DIRECT)
    try:
        setup_physics()
        urdf = variants.ensure_variant(n_fingers)
        g = FixedGripper(urdf)
        g.set_ready(READY_CURLED if ready == "curled" else READY_SPLAYED)
        g.set_finger_dynamics()
        g.prep_strategy(strategy)
        az = (math.pi / 2 if direction == "finger"
              else math.pi / 2 + math.pi / n_fingers)
        off = offset_m * np.array([math.cos(az), math.sin(az), 0.0])
        cup = g.cup_world()
        ball = setup_ball(cup + off)
        _nc = (CLOSE_STEPS + SETTLE_STEPS) * SUBSTEP
        for s in range(_nc):
            g.hold_arm_rigid()
            g.apply_close(strategy, ball_id=ball, progress=s / _nc)
            p.stepSimulation()
        ee = g.ee_world()
        paths = []
        views = {
            "side": dict(eye=(0.45, -0.0, ee[2]), tgt=(0, 0, ee[2] - 0.03)),
            "diag": dict(eye=(0.32, -0.32, ee[2] + 0.12), tgt=(0, 0, ee[2] - 0.03)),
            "under": dict(eye=(0.06, -0.06, ee[2] - 0.34), tgt=(0, 0, ee[2] - 0.04)),
        }
        proj = p.computeProjectionMatrixFOV(fov=42, aspect=1.0,
                                            nearVal=0.02, farVal=4.0)
        for name, v in views.items():
            view = p.computeViewMatrix(v["eye"], v["tgt"], [0, 0, 1])
            _, _, rgba, _, _ = p.getCameraImage(
                600, 600, viewMatrix=view, projectionMatrix=proj,
                renderer=p.ER_TINY_RENDERER)
            frame = np.array(rgba, np.uint8).reshape(600, 600, 4)[:, :, :3]
            import imageio.v2 as imageio
            path = os.path.join(
                out_dir,
                f"cage_{strategy}_n{n_fingers}_{direction}_{int(offset_m*1000)}mm_{name}.png")
            imageio.imwrite(path, frame)
            paths.append(path)
        nf = _fingers_touching(g, ball)
        print(f"rendered {len(paths)} frames (seated fingers touching={nf}):")
        for pth in paths:
            print("  " + os.path.abspath(pth))
        return paths
    finally:
        p.disconnect()


# --- video presets -----------------------------------------------------------
# Both clips render the SAME close physics (so fast and slow AGREE) and differ
# only in PLAYBACK: FAST = sampled close + the 8-direction battery (~5.5 s); SLOW
# = TRUE slow-motion of the grasp (every 2nd sim step of the finer-dt close,
# played slow for a ~9 s clip — finer dt gives 4x more frames, so it is smooth).
# This is NOT a re-simulated "slower close" (that changed the dynamics, disagreed
# with the fast clip, and jittered the fingers); it is the identical close.
FAST_DIRS = [("down", (0, 0, -1)), ("up/invert", (0, 0, 1)),
             ("+x", (1, 0, 0)), ("-x", (-1, 0, 0)),
             ("+y", (0, 1, 0)), ("-y", (0, -1, 0)),
             ("diag-down", (1, 1, -1)), ("diag-up", (-1, -1, 1))]


def render_video(strategy, n_fingers, offset_m, direction, ready, out_dir,
                 slow=False, pin=False):
    """Record an MP4 of the close (and, for the fast clip, the disturbance
    battery) from TWO camera angles side-by-side — a 3/4 diagonal view (left) and
    an under/below view (right) that reveals whether the distal segments tuck
    UNDER the ball (the form-closure test). A HUD overlays the live metrics
    (fingers touching, ball displacement, HELD/ESCAPED, and for `yale` the
    per-finger flexions = the self-distribution). `slow=True` is true slow-motion
    of the grasp. `pin=True` holds the ball fixed during the close (gravity-off
    free balls eject for an aggressive adaptive close — pin to SEE the wrap /
    self-distribution; the battery still runs on the released ball)."""
    import imageio.v2 as imageio
    os.makedirs(out_dir, exist_ok=True)
    # close window is now (CLOSE+SETTLE)*SUBSTEP sim steps (finer dt -> more
    # frames -> smoother slow-mo for free). SLOW = grasp only, every 2nd step,
    # fps chosen so the clip is ~9 s. FAST = sampled close + battery, ~5.5 s.
    n_close = (CLOSE_STEPS + SETTLE_STEPS) * SUBSTEP
    if slow:
        close_every = 2
        fps = max(1, round((n_close // close_every) / 9.0))
    else:
        close_every = 4 * SUBSTEP
        fps = 30
    batt_every = 5 * SUBSTEP
    p.connect(p.DIRECT)
    try:
        setup_physics()
        urdf = variants.ensure_variant(n_fingers)
        g = FixedGripper(urdf)
        ready_pose = READY_CURLED if ready == "curled" else READY_SPLAYED
        g.set_ready(ready_pose)
        g.set_finger_dynamics()
        g.prep_strategy(strategy)
        az = (math.pi / 2 if direction == "finger"
              else math.pi / 2 + math.pi / n_fingers)
        off = offset_m * np.array([math.cos(az), math.sin(az), 0.0])
        cup = g.cup_world()
        ball = setup_ball(cup + off)
        ee = g.ee_world()
        # two cameras: 3/4 diagonal (left), and from BELOW looking up (right)
        proj = p.computeProjectionMatrixFOV(46, 1.0, 0.02, 4.0)
        view_diag = p.computeViewMatrix((0.34, -0.34, ee[2] + 0.10),
                                        (0, 0, ee[2] - 0.04), [0, 0, 1])
        view_under = p.computeViewMatrix((0.13, -0.13, ee[2] - 0.40),
                                         (0, 0, ee[2] - 0.05), [0, 0, 1])

        def shot(view):
            _, _, rgba, _, _ = p.getCameraImage(
                480, 480, viewMatrix=view, projectionMatrix=proj,
                renderer=p.ER_TINY_RENDERER)
            return np.array(rgba, np.uint8).reshape(480, 480, 4)[:, :, :3]

        def grab(lines=()):
            frame = np.hstack([shot(view_diag), shot(view_under)])  # 960x480
            return _draw_hud(frame, lines) if lines else frame

        def hud_close():
            nf = _fingers_touching(g, ball)
            bp = np.array(p.getBasePositionAndOrientation(ball)[0])
            cerr = float(np.linalg.norm(bp[:2] - cup[:2]))  # live re-centering
            lines = [f"{strategy}  off={offset_m*100:.1f}cm  dir={direction}"
                     + ("  [pinned]" if pin else ""),
                     f"CLOSE   fingers touching: {nf}",
                     f"centering-err: {cerr*100:.2f}cm  (injected {offset_m*100:.1f}cm)"]
            if strategy in ("yale", "prb"):
                fl = (yale_prb.finger_flexions(g.body, g.finger_joints, g.prb_cfg)
                      if strategy == "prb"
                      else yale_hand.finger_flexions(g.body, g.finger_joints,
                                                     g.yale_cfg))
                lines.append("finger flex: " + " ".join(f"{x:+.1f}" for x in fl))
                lines.append(f"self-distrib spread: {max(fl)-min(fl):.2f} rad")
            return lines

        suffix = ("_pin" if pin else "") + ("_slowmo" if slow else "")
        path = os.path.join(
            out_dir,
            f"cagevid_{strategy}_n{n_fingers}_{direction}_{int(offset_m*1000)}mm{suffix}.mp4")
        writer = imageio.get_writer(path, fps=fps, codec="libx264", quality=7,
                                    macro_block_size=1)
        # phase 1: the close (gravity off). IDENTICAL window + physics for fast
        # and slow (so they agree); slow just samples finer and plays slower.
        ball_pos0 = np.array(p.getBasePositionAndOrientation(ball)[0])
        for s in range(n_close):
            if pin:
                p.resetBasePositionAndOrientation(ball, ball_pos0.tolist(), [0, 0, 0, 1])
                p.resetBaseVelocity(ball, [0, 0, 0], [0, 0, 0])
            g.hold_arm_rigid()
            g.apply_close(strategy, ball_id=ball, progress=s / n_close)
            p.stepSimulation()
            if s % close_every == 0:
                writer.append_data(grab(hud_close()))
        seated = np.array(p.getBasePositionAndOrientation(ball)[0])
        seated_nf = _fingers_touching(g, ball)   # measured at the SAME instant
        results = []                             # (right after the close) for both
        # phase 2: the disturbance battery (FAST overview only). The SLOW clip is
        # the grasp only (the first 1.5 s) for analysis — no battery.
        if not slow:
            state = p.saveState()
            for label, vec in FAST_DIRS:
                p.restoreState(state)
                d = np.array(vec, float); d /= np.linalg.norm(d)
                p.setGravity(*(d * GACC))
                max_disp = 0.0
                for s in range(WINDOW_STEPS * SUBSTEP):
                    g.hold_arm_rigid()
                    g.apply_close(strategy, ball_id=ball, progress=1.0)
                    p.stepSimulation()
                    pos = np.array(p.getBasePositionAndOrientation(ball)[0])
                    max_disp = max(max_disp, float(np.linalg.norm(pos - seated)))
                    if s % batt_every == 0:
                        status = "HELD" if max_disp < ESCAPE_DELTA else "ESCAPED"
                        writer.append_data(grab([
                            f"{strategy}  off={offset_m*100:.1f}cm  dir={direction}",
                            f"BATTERY 2.5g  pull: {label}",
                            f"ball moved: {max_disp*100:.1f}cm   {status}"]))
                results.append((label, max_disp < ESCAPE_DELTA, max_disp))
            p.removeState(state)
        writer.close()
        n_batt = 0 if slow else len(FAST_DIRS) * (WINDOW_STEPS * SUBSTEP // batt_every)
        dur = (n_close // close_every + n_batt) / fps
        print(f"video ({'SLOW grasp-only' if slow else 'fast'}, ~{dur:.1f}s, "
              f"diag+under): {os.path.abspath(path)}")
        print(f"  {strategy} n={n_fingers} off={offset_m*100:.1f}cm dir={direction} "
              f"ready={ready}  seated_fingers={seated_nf}"
              + ("" if slow else f"  battery(shown)={sum(h for _,h,_ in results)}/{len(FAST_DIRS)}"))
        for label, held, md in results:
            print(f"    {label:10s} -> {'HELD ' if held else 'ESCAPED'} "
                  f"(max ball move {md*100:.1f}cm)")
        return path
    finally:
        p.disconnect()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--grid", action="store_true")
    ap.add_argument("--quality-grid", action="store_true",
                    help="re-score strategies on the continuous QUALITY metric "
                         "(escape-margin/centering/contacts/symmetry), §2.2")
    ap.add_argument("--converge", action="store_true",
                    help="convergence table for one cell: vary substep + contact "
                         "model + seed, confirm the quality metric is stable (§2.3)")
    ap.add_argument("--boundary", action="store_true",
                    help="scan the caged->escaped boundary across substeps and "
                         "flag any timestep-unstable offset (§2.3 boundary)")
    ap.add_argument("--migration", action="store_true",
                    help="CAUSAL check: trace ball centering-err DURING the close "
                         "(gradual migration vs one-step snap) for fixed vs soft")
    ap.add_argument("--paired", action="store_true",
                    help="PAIRED-delta convergence: is soft.pull_in - fixed.pull_in "
                         "convergently >0 (earns 'soft re-centers MORE')? (§2.3)")
    ap.add_argument("--quality", action="store_true",
                    help="with a single cell: report the continuous quality metrics")
    ap.add_argument("--quality-frames", action="store_true",
                    help="render the §2.4 HUD-annotated key-moment x 3-angle "
                         "still grid + slow-mo video for one cell")
    ap.add_argument("--no-video", action="store_true",
                    help="with --quality-frames: skip the MP4 (stills only)")
    ap.add_argument("--cell", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--strategy", default="fixed",
                    choices=["fixed", "compliant", "soft", "under", "yale",
                             "tendon", "prb"])
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--offset", type=float, default=0.0)
    ap.add_argument("--dir", default="finger", choices=["finger", "gap", "outside"])
    ap.add_argument("--ready", default="splayed", choices=["splayed", "curled"])
    ap.add_argument("--out", default="runs/cage")
    ap.add_argument("--pin", action="store_true",
                    help="with --video: pin the ball during close (see the wrap)")
    ap.add_argument("--slowmo", action="store_true",
                    help="with --video: ~9 s slow-motion of the grasp")
    ap.add_argument("--prb-inertia", type=float, default=None,
                    help="override the PRB inertia-regularization scale (to sweep "
                         "whether the faithful-Yale behavior is scale-invariant)")
    ap.add_argument("--substep", type=int, default=None,
                    help="override sim sub-steps/240Hz tick (default 4=1/960); "
                         "use to inspect the off-center timestep-fragility (§26)")
    ap.add_argument("--strats", default=None,
                    help="with --quality-grid: comma list of strategies to score "
                         "(default fixed,compliant,soft,yale). Additive.")
    ap.add_argument("--compare", default="yale",
                    help="with --quality-grid: strategy compared against fixed in "
                         "the per-offset mean table (default yale)")
    ap.add_argument("--paired-a", default="soft",
                    help="with --paired: strategy A in the A-B pull-in delta")
    ap.add_argument("--paired-b", default="fixed",
                    help="with --paired: strategy B in the A-B pull-in delta")
    args = ap.parse_args()
    if args.prb_inertia is not None:
        global PRB_INERTIA_OVERRIDE
        PRB_INERTIA_OVERRIDE = args.prb_inertia
    if args.substep is not None:
        global SUBSTEP, SIM_DT
        SUBSTEP = args.substep
        SIM_DT = DT / SUBSTEP
    if args.self_test:
        return self_test()
    if args.grid:
        return grid()
    if args.quality_grid:
        if args.strats is not None:
            strats = tuple(s.strip() for s in args.strats.split(",") if s.strip())
            return quality_grid(strategies=strats, compare_strat=args.compare)
        return quality_grid(compare_strat=args.compare)
    if args.converge:
        return converge_cell(args.strategy, args.n, args.offset, args.dir,
                             args.ready)
    if args.boundary:
        return boundary_scan(args.strategy, args.n, args.dir, args.ready)
    if args.migration:
        return migration_trace(n_fingers=args.n, offset_m=args.offset,
                               direction=args.dir, ready=args.ready,
                               out_dir=args.out)
    if args.paired:
        return paired_converge(args.paired_a, args.paired_b, args.n, args.offset,
                               args.dir, args.ready)
    if args.quality_frames:
        render_quality(args.strategy, args.n, args.offset, args.dir, args.ready,
                       args.out, video=not args.no_video)
        return 0
    if args.render:
        render(args.strategy, args.n, args.offset, args.dir, args.ready, args.out)
        return 0
    if args.video:
        render_video(args.strategy, args.n, args.offset, args.dir, args.ready,
                     args.out, slow=args.slowmo, pin=args.pin)
        return 0
    # default: single cell
    run_cell(args.strategy, args.n, args.offset, args.dir, args.ready,
             verbose=True, quality=args.quality)
    return 0


if __name__ == "__main__":
    sys.exit(main())
