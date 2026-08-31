---
tags:
  - concept
---

# Ballistic prediction & interception

## What it is

Drag-free projectile motion is fully determined by one state sample:

```
p(t) = p₀ + v₀·t + ½·g·t²
```

Everything the catcher needs falls out of one quadratic solve — where the
ball crosses a height z (predicted landing), and *when* (time-to-
intercept): solve `½g·t² − vz·t + (z − pz) = 0`, take the **later root**
(the descending crossing; the earlier root is the ball passing that height
on the way up).

Interception then has three separable sub-problems:

1. **Where to be**: predicted crossing point of a chosen plane/height.
2. **When**: time-to-intercept drives all choreography (sweep windows,
   trigger arming) — recompute it every tick, never latch a one-shot plan.
3. **How to arrive**: a rendezvous problem for the body — and a PD position
   loop with adequate ωn *is* a fine rendezvous law (see 01).

Geometric subtlety that bit us twice: an arm tip moves on a **circle**, a
ball on a **parabola**. Velocity-matching them is tangency at one instant;
their accelerations (centripetal ω²L vs gravity) point nearly opposite, so
separation regrows as ½|Δa|t² — a ~30–70 ms window. You don't widen it
with better timing; you change the problem (compliance, or track the curve
with more DOF).

## Where we use it

`ball.py` `predict_landing` (planner + catcher), time-to-intercept in
`arm_catch_solo.py` and `main.py`, the throw planner's inverse problem
(choose release velocity to hit a landing point), and the test harness's
own inverse-inverse problem (choose a launch state so the ball *arrives*
at a chosen point with a chosen velocity).

## What we learned here

- Prediction error is dominated by **velocity** noise early (σ_landing ≈
  σ_v·t_flight ≈ 20+ cm at launch), shrinking as the ball nears. So:
  filter, and expect the predicted intercept to wander early — don't
  over-commit to it (the demo gates on "ball committed" before trusting).
- Time-shifted views of the same parabola predict the *same landing
  point* — which is why pure (even unmodeled, if small) latency hurts
  timing but not positioning. See 05.
- Solving "arrive with velocity v at point p" backwards (our launch
  helper) needs its feasibility constraints written down (floor, walls,
  ceiling) — two of our "controller bugs" were actually infeasible
  spawn geometry.

## For larger projects

Closed-form motion models are a gift — exploit them for prediction,
inverse planning, and latency compensation before reaching for learned or
numeric models. When the model gains terms (drag, spin/Magnus, bounces),
the same structure survives but prediction degrades with horizon — that's
when estimation quality and replanning rate start to dominate the design.
