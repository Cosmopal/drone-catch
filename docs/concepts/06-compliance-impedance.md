---
tags:
  - concept
---

# Compliance, impedance, and impulse

## What it is

A catch is a **momentum transfer**: the ball's momentum p = m·v must end
up in the catcher. Force is Δp/Δt — momentum is non-negotiable, but *you
choose Δt* by choosing how much the contact yields ("stroke"):

- Rigid contact: transfer in ~1 ms → huge peak force, and the coefficient
  of restitution decides the outcome (the ball bounces off).
- Compliant contact: spread over 60–100 ms of give → gentle forces, ball
  stays.

Our 65 g ball at ~4.6 m/s carries 0.3 N·s. Absorbed over 70 ms: ~4 N
average. Absorbed in one rigid step: a hammer tap.

**Impedance control** is the general framing: don't control position OR
force — control the *relationship* the contact point presents to the
world, F = K·Δx + B·Δẋ (a virtual spring-damper whose stiffness you
choose, and can re-schedule: soft to absorb, stiff to carry).

**Backdrivability**: a joint is back-drivable if external loads can move
it. Torque-cap a velocity-mode motor and it yields at a force you chose —
poor man's impedance, and exactly what real current-controlled servos
(e.g., Dynamixel current mode) give you.

A key hardware truth: **control cannot shape the first millisecond of an
impact** — control bandwidth (~100 Hz–few kHz) is far below contact
dynamics (1–10 kHz). The first instant is decided by *passive* mechanics
(pad material, finger springs, gear friction). Compliance is a stack:
material (mm, instant) → fingers (cm) → joint (tens of cm) → whole body
(meters, slow). Software only orchestrates the slower layers.

## Where we use it (the grasp mechanism, precisely)

`drone.py` `soft_grasp`/`firm_grasp`/`grasp_force`:

1. Trigger is geometric only (estimated ball within 15 cm of the
   end-effector) — no relative-velocity gate.
2. `soft_grasp`: a PyBullet **point-to-point constraint** (ball joint —
   couples position only, free rotation) between the EE link and the ball,
   with `maxForce = 8 N`. The solver may pull the two together with at
   most that force → the ball decelerates over ~m·Δv/F ≈ 60–80 ms and
   ~10 cm of stroke. This is a *behavioral stand-in* for foam pad +
   compliant fingers, not contact physics.
3. Shoulder goes back-drivable during absorption: `spin_arm(...,
   torque_cap=0.3)` (vs 2.0 N·m max) so the arm yields under load.
4. Two-stage lock: when relative velocity < 0.3 m/s, `firm_grasp` raises
   the cap to 200 N (rigid carry) and the shoulder brakes to ω=0.

Caveat we measured: PyBullet's `maxForce` caps **each axis
independently**, so an "8 N" constraint can apply 8·√3 ≈ 13.9 N of vector
force.

## What we learned here

- Compliance bought a 3× relaxation of the catch condition: velocity
  matching needed rel-vel ≤ 1.5 m/s in a ~27 ms window; compliant capture
  handles 4.6 m/s contacts with a purely geometric trigger.
- Impulse bookkeeping is the validation: logged ∫F·dt matched m·Δv (plus
  the gravity contribution over the absorb window).
- Compliance and planning *compose*: the velocity-matched arm sweep halves
  contact rel-vel, then compliance absorbs the residual — each makes the
  other's tolerances loose.

## For larger projects

Whenever a robot must touch something fast or uncertain (catching,
grasping, footsteps, docking), reach for impedance first, precision
second. Softness is tolerance: every N/m you don't need is millimeters of
error you don't have to fight for. And put real passive compliance in the
hardware — software can't react in the first millisecond.
