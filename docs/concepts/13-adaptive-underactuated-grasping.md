# Adaptive & underactuated grasping (and why a flying base changes the answer)

## What it is

Robust grasping under **position uncertainty** (you never know exactly where
the object is) is a solved-in-principle problem, and the key idea is:

> **Put the adaptation in the MECHANISM, not the controller.**

A position-controlled rigid hand servos every joint to a fixed shape, so it
assumes the object is where you expected — and shoves it out when it isn't
(see iteration_findings §21, the off-center ball "paddled out"). The field's
answer is **mechanical compliance + underactuation**:

- **Underactuated / tendon-driven hands** — one actuator drives many joints
  through a **differential (whiffletree)** + **compliant (flexure) joints**.
  Each finger closes until *it* contacts, then the shared tendon feeds travel
  to the fingers that haven't. The hand self-distributes around the object with
  no per-finger sensing. (Dollar & Howe, **SDM Hand**; the **Yale OpenHand**
  project — 3D-printable, fishing-line tendons, flexure joints.)
- **Structural compliance** — **Fin Ray** fingers (a flexing rib truss, printed
  in TPU) wrap *further the harder you push*; the compliance is in the plastic,
  no actuation needed to conform.
- **Caging** (Rodriguez, Mason & Ferry, *From Caging to Grasping*) — trap the
  object topologically *with clearance*, then optionally squeeze. Robust because
  it's a topological condition, not a precise-contact one. (Our "loose oval.")
- **Jamming / universal gripper** (Brown et al.) — a granular bag that conforms
  then vacuum-jams rigid. Maximally uncertainty-tolerant, but heavy + needs
  vacuum.

Force vs form closure and the inversion test are in [[09-grasping-caging-and-actuator-disturbance]].

## Where we use it / what we tried

`Drone.close_gripper(compliant=True)` implements the underactuated idea: a
**constant inward torque per joint + light damping, no target pose** (the
"tendon tension"), so each joint stalls on contact and conforms. Config
`finger_tau_close`, `finger_damp`.

## What we learned — the flying base changes the answer

Two findings, the second is the important one:

1. **A fixed-pose close shoves an off-center ball out**; the renders show 4
   fingers leave 66° diagonal gaps (~30% equator coverage). Geometry isn't the
   limit (the fingers are 2× the ball) — the *fixed-target close* is.

2. **Active underactuation (constant finger torque) DESTABILIZES a floating
   base.** On the drone, the compliant close pitched the body to ~90° (it
   flipped) — the sustained finger torques react on the airframe (Newton's
   third law, the §09/§15 actuator-disturbance problem) and a position-PD close
   that reaches its target and stops applying torque doesn't have this; a
   *constant*-torque tendon never stops. A real Yale hand lives on a fixed arm
   that absorbs this reaction; a drone has nothing to absorb it.

**The transferable conclusion:** on a mobile/flying manipulator, the gripper's
own actuation reaction is a disturbance on the base. So **passive structural
compliance (Fin Ray) is strictly better than active underactuation (tendon)
for a flying catcher** — Fin Ray conforms with *zero actuation torque*, hence
*zero body reaction*, while a tendon hand's closing torque fights the flight
controller. If you do use an actuated underactuated hand on a drone, its
finger-reaction must be fed forward/countered like the arm-reaction FF.

## For larger projects

- **Adaptation belongs in the mechanism.** Trying to make a rigid hand conform
  by *control* fights the contact solver and the platform; compliant mechanics
  get it for free and are robust to the uncertainty that always exists.
- **On a mobile base, budget the end-effector's actuation reaction** as a base
  disturbance — it can flip a flying platform. Prefer *passive* compliance
  where you can; it has no reaction.
- **Test the gripper on a fixed base before coupling it to the moving system**
  (§09) — it separates "is the grasp mechanism right" from "does the platform
  survive the grasp." (We re-learned this the hard way.)

## Update — a trustworthy study tested these claims (and refuted most)

The intuitions above ("adaptation in the mechanism", "compliance beats a rigid
close under uncertainty") came from noisy quick experiments. A deterministic
fixed-base harness with a real form-closure metric (26-direction, 2.5 g
disturbance battery; `tests/cage_harness.py`, iteration_findings §25) tested them:

- **Compliance did NOT beat the rigid fixed-pose close** under cm-scale offset.
  A force-limited "conform on contact" close scored *worse* off-center, and a
  soft-spring (Fin-Ray analogue) scored **zero — too soft to resist 2.5 g**.
  The conform-vs-hold tradeoff is real: soft enough to adapt = too soft to hold.
- **Form closure here is a specific SHAPE, not just contact.** The validated cage
  (long proximal to the equator, middle+distal tucked under) is a tuned pose; a
  uniform constant-torque "tendon" close does not reproduce it (it balls up or
  paddles the object out). True underactuation needs a *differential*
  (whiffletree) to distribute travel correctly — one per-joint torque is not it.
- **The real failure mode is finger-COUNT/coverage, not compliance**: an
  off-center ball escapes through a finger *gap*; only a denser ring (with a
  re-tuned close pose) helps.
- **The finger-reaction feedforward** (predict body torque from finger motor
  torques, pre-cancel — the arm-reaction-FF idea applied to the hand) is a clean
  **negative** on a flying base: in the arm-down pose the symmetric ring's motor
  torques sum to ~0, so the FF predicts ~0, while the actual disturbance is the
  *asymmetric finger-link inertial/contact* reaction the model can't see. The
  rigid winning close needs no FF anyway — on a level-holding (thrust-vectoring)
  body it disturbs pitch < 2.5 deg.

Transferable: **measure the cage with a disturbance battery, not distance** —
and don't trust a compliance/FF win until a deterministic harness reproduces it.

## Buildable at home (sim2real)

- **Fin Ray fingers** — print in **TPU** (flexible filament; widely available,
  e.g. Bangalore FDM services), one servo to close. Lightest + most
  position-robust + no body reaction → best fit for a drone catcher.
- **Yale OpenHand** — open-source, 3D-printed links + fishing-line tendons +
  flexure joints; the canonical adaptive hand, but its active closing torque
  needs reaction budgeting on a drone.
- Sim caveat: PyBullet's rigid contact can approximate underactuation (constant
  torque + soft joints) and a discretized Fin Ray (multi-link soft chain), but
  not true continuous deformation or jamming — those need FEM.
