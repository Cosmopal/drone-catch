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

- **A flying gripper's servo can flip the aircraft.** Stiff or velocity-driven
  finger motors, with the arm extended, injected enough body-yaw disturbance
  to drive our attitude controller into its singularity (§1) and crash it.
  The static gripper was harmless; the *motor dynamics* were the problem.
  Diagnosis: freeze the fingers kinematically vs motorize them — the freeze
  was rock-stable, the motors diverged. Fix: gentle position control. (And a
  PyBullet-specific trap: its explicit joint-motor PD goes numerically
  unstable at *high* gain on near-massless links — so "stiffer" is not safer.)

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
