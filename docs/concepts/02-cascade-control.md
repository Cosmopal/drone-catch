---
tags:
  - concept
---

# Cascade control & timescale separation

## What it is

Quadrotors are **underactuated**: 4 motor thrusts, 6 degrees of freedom.
You cannot command a sideways force directly — you must *tilt first, then
thrust*. The standard answer is two nested loops:

1. **Outer (position) loop** — PD on position error → a desired thrust
   *vector* in world frame ("I want 4 m/s² that way").
2. **Inner (attitude) loop** — rotates the body so its thrust axis aligns
   with that vector (ours is a Lee-style geometric SO(3) controller),
   while the thrust magnitude tracks the vector's length.

The contract that makes nesting legal is **timescale separation**: the
inner loop must converge much faster than the outer loop changes its mind
— rule of thumb ≥3–5× in bandwidth. Ours: attitude ωn ≈ 11 rad/s vs
position ωn ≈ 3.5 rad/s after the catch-task retune (≈3.2×, acceptable;
the original 2.45 gave 4.5×). If you stiffen the outer loop, you eat into
this margin — check it.

## Where we use it

`controller.py` — `CascadeController.compute()`: outer PD builds
`thrust_vec`, tilt-capped (see below), then the inner SO(3) loop produces
body torques. Safety layers we added on top:

- **Tilt cap**: clip the thrust vector's horizontal component so the body
  never tilts past `max_tilt_deg` (35° default, 60° in catch/throw
  maneuvers). An aggressive outer loop would otherwise command a near-
  horizontal thrust vector → drone flips → no vertical authority → falls.
- **Vertical-thrust floor**: always push up at least ½·g.

## What we learned here

- The inner loop has a 180° singularity (Lee-style attitude error blows up
  near yaw = π) — geometry-dependent bugs that only bite in specific poses
  are a signature of attitude parameterization choices. Quaternion-error
  controllers are the standard fix (still on our parking lot).
- The cascade's response to "matching a falling ball" is structurally
  awkward (thrust dip → pitch cycle): some maneuvers fight the
  underactuation rather than use it. Re-planning the task (arm absorption,
  compliance) beat fighting the cascade.

## For larger projects

Cascades are everywhere (motor current → velocity → position; robot joint
→ end-effector; vehicle attitude → trajectory). The two universal
failure modes: (1) breaking timescale separation when retuning one layer,
and (2) the outer loop commanding things the inner loop physically can't
deliver (hence our tilt cap — saturate *gracefully, by design*).
