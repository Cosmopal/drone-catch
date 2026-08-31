---
tags:
  - concept
---

# PD control, natural frequency, damping

## What it is

The workhorse feedback law. To drive a position `x` to a target, command an
acceleration from the error and its rate:

```
a = kp·(x_target − x) + kd·(v_target − v)
```

- **kp (proportional gain)** — "spring stiffness." How hard you get pulled
  back per meter of error. More kp → faster response, stronger disturbance
  rejection, but more overshoot if kd doesn't keep up.
- **kd (derivative gain)** — "damper." Resists velocity error; bleeds energy
  out of the spring so the system settles instead of ringing.

The spring-damper analogy is exact: a PD-controlled point mass IS a
mass-spring-damper. That gives two numbers that describe everything:

- **Natural frequency** `ωn = √kp` — how fast the loop responds
  (settle time ≈ 4/(ζ·ωn)).
- **Damping ratio** `ζ = kd / (2·√kp)` — the shape of the response.
  ζ < 1 underdamped (overshoots, rings), ζ = 1 critically damped (fastest
  without overshoot), ζ > 1 overdamped (sluggish).

Steady-state offset under a constant force F: `Δx = F/(m·kp)`. PD alone
never fully rejects constant disturbances — that's what integrators (PID)
or feedforward are for.

## Where we use it

- Position outer loop: `controller.py` `kp=[6,6,12]`, `kd=[4,4,6]`
  → lateral ωn ≈ 2.45 rad/s, ζ ≈ 0.82.
- Catch task override (`arm_catch_solo.py`): `kp=[12,12,14]`, `kd=[7,7,7]`
  → ωn ≈ 3.5, ζ ≈ 1.0.
- The attitude inner loop is the same idea on rotation (kR, kw).

## What we learned here

- **Tune kp and kd together.** Our hard-won M5b lesson: commanding a
  velocity target proportional to position error (`vtgt = K·err`) is
  algebraically a kp increase of `kd·K` with no matching kd — ζ fell
  0.82 → 0.58 and the drone oscillated through the catch window. If the
  loop is too slow, raise ωn *at constant ζ*: double kp → multiply kd
  by √2.
- **Gain stiffness is disturbance rejection.** Doubling kp halved our
  static wind-gust offset (8 cm → 4 cm) for free.
- **A PD position loop is already a good rendezvous law.** Attempts to
  outsmart it with "arrive just in time" velocity carrots (vtgt =
  dist/t_remaining) capped the drone at a crawl — the kd term *punishes*
  going faster than the carrot.

## For larger projects

Any time you see two gains on an error and its derivative — vehicle
position, attitude, motor servo, camera gimbal — compute ωn and ζ before
touching anything. Most "controller feels sluggish/jittery" bugs are a ζ
that drifted away from ~0.7–1.0 because someone changed one gain without
the other, or because the plant's inertia changed (see gain scheduling).
