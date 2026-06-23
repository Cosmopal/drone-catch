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
import yale_hand                                 # noqa: E402

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
sys.path.insert(0, ASSETS)
import make_gripper_variants as variants         # noqa: E402

DT = 1.0 / 240.0
G = 9.81

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

    def apply_close(self, strategy, ball_id=None, progress=1.0):
        """Apply the close command for one step.

        `fixed`/`compliant`/`soft` servo toward the validated CLOSE_POSE and
        differ only in compliance (force cap / gain). `under` is a per-joint
        deep-curl stand-in (no coupling). `yale` is the FAITHFUL underactuated
        hand (`src/yale_hand.py`): one actuator displacement (ramped by
        `progress`), inter-finger whiffletree + intra-finger tendon couplings, so
        the hand SELF-DISTRIBUTES around the ball (`ball_id` read for live
        contact). `under` was per-joint independent — `yale` is the real
        mechanism."""
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
             verbose=False):
    """Seat a ball at (offset_m, direction) in the cup, close with `strategy`,
    then score the 26-direction disturbance battery. Returns a result dict.

    `direction` in {"finger","gap","outside"}; "outside" places the ball
    `offset_m` laterally OUTSIDE the cup (negative control). The harness owns the
    PyBullet connection (caller must not be connected)."""
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

        # --- disturbance battery (26 directions, re-applied from saved state) ---
        state = p.saveState()
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
        p.removeState(state)

        score = survived / len(DIRS_26)
        # seating offset of the ball from the cup center after the close
        seat_off = float(np.linalg.norm(seated - cup))
        if verbose:
            print(f"strategy={strategy} n={n_fingers} off={offset_m*100:.1f}cm "
                  f"dir={direction} ready={ready} | score={score:.2f} "
                  f"({survived}/26) seated_nf={nf} seat_off={seat_off*100:.1f}cm "
                  f"max_disp={max_disp_all*100:.1f}cm ball_r={rad*100:.1f}cm")
        return {"strategy": strategy, "n": n_fingers, "offset": offset_m,
                "dir": direction, "ready": ready, "score": score,
                "survived": survived, "seated_nf": nf, "seat_off": seat_off,
                "max_disp": max_disp_all, "ball_r": rad}
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
            lines = [f"{strategy}  off={offset_m*100:.0f}cm  dir={direction}"
                     + ("  [pinned]" if pin else ""),
                     f"CLOSE   fingers touching: {nf}"]
            if strategy == "yale":
                fl = yale_hand.finger_flexions(g.body, g.finger_joints, g.yale_cfg)
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
                            f"{strategy}  off={offset_m*100:.0f}cm  dir={direction}",
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
    ap.add_argument("--cell", action="store_true")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--video", action="store_true")
    ap.add_argument("--strategy", default="fixed",
                    choices=["fixed", "compliant", "soft", "under", "yale", "tendon"])
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--offset", type=float, default=0.0)
    ap.add_argument("--dir", default="finger", choices=["finger", "gap", "outside"])
    ap.add_argument("--ready", default="splayed", choices=["splayed", "curled"])
    ap.add_argument("--out", default="runs/cage")
    ap.add_argument("--pin", action="store_true",
                    help="with --video: pin the ball during close (see the wrap)")
    ap.add_argument("--slowmo", action="store_true",
                    help="with --video: ~9 s slow-motion of the grasp")
    ap.add_argument("--substep", type=int, default=None,
                    help="override sim sub-steps/240Hz tick (default 4=1/960); "
                         "use to inspect the off-center timestep-fragility (§26)")
    args = ap.parse_args()
    if args.substep is not None:
        global SUBSTEP, SIM_DT
        SUBSTEP = args.substep
        SIM_DT = DT / SUBSTEP
    if args.self_test:
        return self_test()
    if args.grid:
        return grid()
    if args.render:
        render(args.strategy, args.n, args.offset, args.dir, args.ready, args.out)
        return 0
    if args.video:
        render_video(args.strategy, args.n, args.offset, args.dir, args.ready,
                     args.out, slow=args.slowmo, pin=args.pin)
        return 0
    # default: single cell
    run_cell(args.strategy, args.n, args.offset, args.dir, args.ready, verbose=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
