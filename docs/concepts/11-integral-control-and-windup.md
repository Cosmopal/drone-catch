# Integral control and windup (the "I" in PID)

## What it is

A **proportional** (P) controller commands force proportional to the *current*
error: `u = kp·e`. Against a **constant** disturbance (gravity on an offset
mass, steady wind), P alone leaves a **standing error** — it balances when
`kp·e = disturbance`, i.e. `e = disturbance/kp ≠ 0`. Bigger kp shrinks the
offset but never zeroes it (and eventually oscillates, §01).

The **integral** term accumulates the error over time and commands force
proportional to that running sum: `u += kI·∫e dt`. As long as *any* error
persists, the accumulator keeps growing and pushing harder — so it drives a
constant disturbance's error to *exactly* zero. It is the only linear term that
can.

The cost is **memory / lag**. The accumulated term reflects *past* error, not
present, so it adds a slow mode. If it winds up large — high gain, or a slow or
saturating plant — it **overshoots**: the body sails past the target and swings
slowly back (**integrator windup**). An **anti-windup clamp** bounds the
accumulator to limit this.

## Where we use it

`CascadeController.kI` (attitude integral, default `[0.05, 0.05, 0]`) and
`kI_pos` (position integral, default off; the finger-gripper catcher turns it
on), with `pos_integral_clamp` bounding the windup. The yaw integral `kI[2]`
cancels the gripper's steady yaw torque (§09); the position integral cancels
the gripper COM's hover sag.

## What we learned here

- **The caging gripper's offset COM is a constant disturbance** — gravity on a
  mass that isn't under the thrust center → a hover sag that P can't remove →
  needs integral *or* feedforward.
- **Aggressive integral overshoots, and tuning only moves the phase.** The
  diagonal-station catch made this vivid: `kI_pos = 20` wound up against the COM
  offset and drove a big *slow body swing* (the drone wallowing for >1 s). A
  gentler integral (3) with more damping shrank the swing — but only *shifted
  its phase* so the body happened to be near-station at the catch instant; it
  didn't kill the swing. Integral is feedback that reacts *after* the error
  appears, so it always carries this lag/overshoot mode.
- **The robust fix for a *known* steady disturbance is feedforward, not a
  bigger/smaller integral.** Compute the disturbance and cancel it directly, so
  the integral never has to wind up. The user's phrase "react to the upcoming
  torque" *is* feedforward. Integral should be left to mop up only the small,
  *unmodeled* residual.

## For larger projects

- Reach for integral to null constant biases you **can't model** (slow drift,
  mild wind, small mass errors).
- But it is a blunt tool: it adds lag and an overshoot mode and is slow to act.
  For any disturbance you can **predict** (known payload mass, arm-pose COM,
  gravity), feed it forward and let a *small* integral clean up the remainder. A
  small integral on top of good feedforward beats a large integral alone.
- **Always anti-windup-clamp the accumulator**, especially with actuator
  saturation — a saturated plant winds the integral way up, then dumps a huge
  overshoot when it finally moves. See [[03-feedforward-and-gain-scheduling]],
  [[01-pd-control]], [[08-disturbance-modeling]].
