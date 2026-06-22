# Grasping, caging, and actuator-induced disturbance

## What it is

Two ways to hold an object after contact:

- **Force closure**: fingers pinch hard enough that friction alone resists
  any wrench (push/twist). Needs accurate force control and good friction.
- **Form/cage closure**: fingers wrap so the object is *geometrically*
  trapped — it can't leave no matter the forces, friction optional. More
  robust to uncertainty, which is why a basket/net catches a ball a precise
  pinch would fumble.

Our 3-finger gripper aims for caging: two-segment fingers curl past the ball
so the tips converge underneath it.

The deeper, more transferable lesson from building it is about **actuator
disturbance**: a manipulator's own joint motors push back on the body that
carries them (Newton's third law). On a fixed industrial base that reaction
is absorbed by the floor. On a *flying* base it is a disturbance the flight
controller must reject — and a poorly-tuned gripper servo can destabilize the
whole aircraft.

## Where we use it

`assets/make_gripper_urdf.py` (gripper geometry), the `Drone` finger API in
`src/drone.py` (`open_gripper` / `close_gripper` / `fingers_touching` /
`set_finger_dynamics`), and `tests/finger_catch_solo.py` (the catch probe).
See `docs/iteration_findings.md` §13 for the full build narrative.

## What we learned here

- **Cage geometry has a sweet spot.** Fingers converge ~4 cm beyond the
  fingertip-mount, not at the palm and not at the tip. Aim the ball there;
  too shallow and it bounces off the palm, too deep and it falls through
  behind the closing fingers. We found it with a stationary-ball test before
  trusting any moving catch — *isolate the geometry from the dynamics.*

- **A flying gripper's servo can flip the aircraft — and the mechanism is
  subtle.** Symmetric fingers moving together *should* produce zero net
  reaction (the 3 joint-axis vectors sum to zero, so equal torques cancel).
  Two things break that, both needing the arm **horizontal** (the catch pose):
  (1) the finger joint axes are perpendicular to the arm, so when the arm is
  horizontal those axes point partly *vertical* — i.e. finger torque now has a
  **yaw** component (with the arm vertical, the axes are horizontal → no yaw);
  (2) a horizontal arm loads the three fingers *unequally* under gravity (each
  at a different clock angle), so the motors hold them with unequal torques —
  which therefore *don't* cancel. Measured in the catch pose: per-finger hold
  torques +0.22 / +0.28 / −0.29 N·m onto axes with world-z components
  +1.0 / −0.47 / −0.53 → **net +0.24 N·m of body yaw**; the same arm pointing
  straight down gives −0.03 N·m (≈10× less). That steady yaw torque, on the
  weakly-gained yaw channel with no integral, drives the body toward the Lee
  SO(3) singularity (§1) and crashes it. It is *not* the closing motion —
  freezing the fingers kinematically (zero motor torque) is rock-stable;
  motorizing them produces the yaw. Fixes: gentle position control + a yaw
  integral. (PyBullet trap: its explicit joint-motor PD goes numerically
  unstable at *high* gain on near-massless links — "stiffer" is not safer.)

- **Persistent disturbances need integrators, not just stiffer P.** The
  gripper's mass offset (→ position sag) and residual yaw torque (→ steady
  yaw) are constant biases; a PD leaves a standing error against them
  (offset = F/(m·kp), §1). Integral action is what drives a *constant*
  disturbance to zero. We added position and yaw integrals (default-off) for
  exactly this.

- **Holding mass changes the plant.** Fingers at the arm tip roughly doubled
  the arm's rotational inertia, making the timed catch sweep lag. A held or
  end-mounted mass is not a passenger — it re-tunes your dynamics.

- **Caging a *moving* target is a rendezvous problem, and 1 DOF isn't enough.**
  A single sweeping joint traces the cup through an arc; landing that arc on
  the ball at the exact intercept instant is a knife-edge. The principled fix
  is more DOF (an elbow) so the end-effector can servo to a point and track
  it, turning timing into tracking.

## For larger projects

- Prefer **caging over pinching** whenever the target pose is uncertain —
  it trades precision for geometric robustness.
- On any mobile manipulator (aerial, legged, floating-base), **budget the
  arm/gripper reaction as a disturbance** on the base controller, and tune
  the manipulator's own servos for *gentleness*, not just tracking — a fast
  finger that destabilizes the platform is a net loss.
- **Test the end-effector mechanism in isolation** (static, scripted poses)
  before coupling it to the full moving system; it tells you whether a failure
  is geometry or dynamics. That one habit saved us from chasing a control bug
  that was really a 2 cm cup-depth error — and from trusting a "catch" whose
  real problem was the platform flipping.

## Update (M8): from force closure to form closure

The 2-segment fingers above only achieved **force closure** — friction at a
few contact points, which is orientation-fragile (a ball it "held" in an
upright cup fell out the moment the hand tilted ~90°). The honest gate is the
**inversion test**: close on the object, rotate 180°, does it stay? Force
closure fails it; **form closure** (geometric trapping) passes it.

Form closure of a sphere needed three things, all geometric:
- **Mount ring ≥ object radius** so fingers start *outside* the ball and can
  wrap around it (ours started inside — they couldn't enclose what they were
  mounted within).
- **Three-jointed fingers** (not two) so each finger curls into a tight "C".
- **A long proximal phalanx** (human-like) so the finger reaches *down past
  the equator* before the shorter middle/distal segments curl *under* — that
  under-tuck is what closes the basket and survives inversion.

Process lesson that recurred: a **screenshot review caught the bug**. The
"caged" catch had really been containment-in-an-upright-cup the whole time;
the rendered close pose showed fingers folding back over the wrist instead of
enclosing. Render your mechanism in the pose that matters and look at it —
numbers (contact count, "held through a vertical lift") hid the failure that
one picture made obvious.

Platform lesson: **N PD-controlled joints on a floating base can overwhelm
the contact solver.** 12 finger joints (4×3) diverged the body ~80 cm even
though the fingers were barely moving — the *static* hand was fine, the motor
loops weren't. Pinning the fingers kinematically while open (and only
motorizing to close) gave the tightest hover; raising solver iterations also
worked. Tight station-keeping matters directly: the catch's tracking accuracy
is set by how well the body holds station.
