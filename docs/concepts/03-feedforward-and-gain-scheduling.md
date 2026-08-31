---
tags:
  - concept
---

# Feedforward & gain scheduling

## What it is

**Feedback** reacts to error after it appears. **Feedforward (FF)** cancels
a disturbance you can *predict*, before the error ever forms. The division
of labor: FF handles what you know, feedback mops up what you don't.

The simplest example everyone uses without naming it: gravity
compensation — thrust = m·g + corrections. We never ask the feedback loop
to "discover" gravity each tick.

**Gain scheduling** is the sibling idea for *parameters*: when the plant
itself changes predictably (inertia, mass, speed), recompute the gains so
the closed-loop behavior (ωn, ζ) stays constant, instead of letting the
response quality drift.

## Where we use it

| Layer | What it predicts and cancels |
|---|---|
| Gravity FF (incl. held mass) | weight of drone + carried ball/cube |
| Arm-reaction torque FF | torque the body feels when the shoulder accelerates (τ = I_arm·α, Newton's third law) |
| Body-z translational FF | vertical force from arm centripetal+tangential motion: F = −m_eff·(α·sinθ + ω²·cosθ) |
| Attitude gain scheduling | rescales kR_y, kw_y as arm pose + held mass change pitch inertia (6× swing!) so the attitude loop stays at design ωn, ζ ≈ 0.91 |

## What we learned here

- Gain scheduling was the single most dramatic fix in the project: hover
  drift during arm sweep went 33 cm → 0.5 cm. With the arm extended + ball
  held, pitch inertia is ~6× body-only; fixed gains meant ζ collapsed
  0.91 → 0.37 (ringy). Same gains, recomputed for the actual inertia each
  tick → problem gone.
- FF quality is limited by model quality. Our arm-reaction FF uses a
  rate-limited finite difference of *commanded* ω — good enough; chasing
  perfect cancellation isn't worth it because feedback covers the residual.
- Sometimes the answer is "plan around it" instead: the drone's forward
  push from arm centripetal force during the throw is *planned into* the
  cruise speed rather than cancelled (`cruise_speed_for_release`).
  FF-vs-replan is a judgment call: cancel what disturbs you, exploit what
  helps you.

## For larger projects

Before adding feedback gain to fight a "disturbance," ask: is it
predictable from state I already have? If yes, feedforward is cheaper,
faster, and doesn't destabilize anything. And whenever your plant's mass/
inertia/operating point varies by more than ~2×, schedule the gains —
a controller tuned at one operating point is silently mistuned at the
others.
