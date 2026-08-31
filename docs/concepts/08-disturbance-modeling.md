---
tags:
  - concept
---

# Disturbance modeling (OU gusts, noise envelopes, seeds)

## What it is

To trust a controller, you must attack it with the disturbances reality
will bring — *with the right statistics*. Three patterns we use:

**Ornstein–Uhlenbeck (OU) process** for wind gusts. White noise is wrong
for wind (infinitely fast wiggle, no push); a constant force is also wrong
(trivially absorbed by an integrator). Real gusts are *correlated in
time*: they lean on you for a while, then change. OU is the simplest such
process — white noise pulled back toward zero:

```
F ← F·(1 − dt/τ) + σ·√(2·dt/τ)·N(0,1)
```

τ is the correlation time (ours: 0.5 s), σ the stationary standard
deviation (ours: ~0.3 N ≈ 5% of vehicle weight). The √(2dt/τ) factor is
what keeps σ independent of timestep — a classic bug otherwise.

**Distance-scaled sensor noise**: stereo depth uncertainty grows with
range, so our `BallPerception` scales σ with viewer–ball distance
(~1 cm at 1 m, ~2.5 cm at 4 m) plus a floor. Constant-σ noise models
flatter your far-field perception and slander your near-field.

**Seeded envelope grids**: robustness claims need (a) a parameter
envelope (incoming velocity grid, intercept-offset grid — derived from
what the *adversary* can physically do), and (b) multiple random seeds
per cell, reported as a held-rate. One lucky run proves nothing; our
acceptance is 96/96 across four grids × 3 seeds.

## Where we use it

`arm_catch_solo.py` `--noise` (gusts, pre-position error, perception
noise via `src/perception.py`), `--grid`/`--grid-pos` envelopes,
`--seeds N`.

## What we learned here

- Each disturbance class found a *different* weakness: latency → estimator
  design; gusts → position-loop stiffness (static offset = F/(m·kp));
  prediction jitter + repositioning → loop bandwidth. A single "add some
  noise" blob would have produced one blurry failure instead of three
  crisp ones.
- Deterministic seeds make failures **reproducible** — every fix in M5b
  started by re-running the exact failing (cell, seed) pair.

## For larger projects

Build the disturbance model *with* the controller, not after it. Write
the envelope down from physics/adversary limits, not vibes; scale noise
the way the sensor actually behaves; give every stochastic test a seed;
and keep a table of disturbance class → failure mode → fix. That table
is the robustness documentation auditors and teammates actually want.
