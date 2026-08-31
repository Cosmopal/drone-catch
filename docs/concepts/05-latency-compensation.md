---
tags:
  - concept
---

# Sensor latency & compensation

## What it is

Every real perception pipeline delivers the *past*: exposure, transfer,
detection, filtering. Stereo-camera ball tracking is ~50 ms behind truth.
Acting on a delayed measurement of a moving target costs

```
position error ≈ closing_speed × latency
```

— at our nominal 4.6 m/s closing speed and 50 ms, that's **23 cm**, larger
than our entire 15 cm catch radius. Latency, not noise, is the
first-order enemy.

**Compensation**: if you know the latency τ and have a dynamics model,
estimate the delayed state (filter it there — that's where measurements
live), then extrapolate forward by τ:

```
p_now = p_delayed + v·τ + ½·g·τ²
v_now = v_delayed + g·τ
```

For a ballistic ball this extrapolation is *exact* in the mean; only noise
amplification grows with τ (a velocity error σ_v becomes a position error
σ_v·τ).

## Where we use it

`BallEstimator.estimate()` in `src/perception.py`. The filter tracks the
delayed state; `estimate()` projects it to "now" before any decision
reads it.

## What we measured (the experiments are the lesson)

Sweeping true latency with *correct* compensation, 3 scenarios × 3 seeds:

| true latency | held |
|---|---|
| 50 → 300 ms | 9/9 at every step |

Modeled latency is nearly free when the dynamics model is exact.

Sweeping *unmodeled* latency (estimator assumes less than reality),
nominal case:

| true | assumed | held |
|---|---|---|
| 50 ms | none | 3/3 |
| 100 ms | half | 3/3 |
| 100 ms | **none** | **0/3** |
| 200 ms | **half** | **0/3** |

Two punchlines:

1. **What kills you is the latency you didn't model**, not the latency you
   have. 300 ms known: fine. 100 ms unknown: every catch fails.
2. **Why 50 ms unmodeled still survived**: a time-delayed view of a
   ballistic trajectory still predicts the same *landing point* — pure
   delay doesn't displace the predicted path, it only shifts *timing*
   (the sweep and trigger fire ~τ late). Compliance forgives ~50 ms of
   timing slip, not 100. Errors that displace the path are deadly;
   errors that shift time only spend margin.

## Variable latency, and why sensors carry timestamps

Real latency isn't a constant — it *jitters* (variable exposure, scheduling,
USB/network transfer, frame drops). If you compensate with a fixed assumed
τ, every measurement is off by `(true_age − assumed_τ)`, which extrapolation
turns into a position error of `velocity × jitter`. Estimation error near
the catch instant (ball at 7 m/s, mean latency 100 ms, 20 trials), measured
in `/tmp/variable_latency.py`:

| latency jitter | fixed-τ assumption | per-measurement timestamp |
|---|---|---|
| ±0 ms  | 1.5 cm | 1.5 cm |
| ±10 ms | 1.9 cm | 1.4 cm |
| ±20 ms | 2.9 cm | 1.5 cm |
| ±40 ms | 5.8 cm | 1.6 cm |
| ±80 ms | 11.0 cm | 1.5 cm |

The fix is the answer to "do sensors timestamp their data?": **yes, and
that's exactly why.** A real driver stamps each measurement with the
*capture* time (not arrival time), so the estimator knows each sample's true
age and extrapolates by *that*, not by an assumed mean. The timestamp column
above stays flat at the noise floor regardless of jitter — the jitter is
fully absorbed.

This generalizes to the **out-of-sequence / late-measurement problem**: with
timestamps the estimator can fuse a measurement at its correct point in
time even if a fresher one already arrived (rewind the filter, apply the
late sample, re-roll forward — or keep a short buffer of past states). The
discipline is "the estimator runs in *sensor time*, the controller runs in
*wall-clock time*, and the timestamp is the bridge." Without timestamps you
can only assume a mean and eat the jitter; this is the single biggest reason
mature robotics stacks (ROS, PX4, every VIO system) propagate hardware
timestamps end-to-end.

## For larger projects

Measure your pipeline's latency end-to-end (timestamp at sensor, compare
at decision) — then model it explicitly. Always carry the sensor's *capture*
timestamp through the pipeline; compensate per-measurement, not by an
assumed mean. Cheap insurance when you have no timestamp: prefer
*overestimating* τ slightly. And remember extrapolation quality = model
quality: against maneuvering targets or strong drag, long-τ extrapolation
degrades from "exact" to "guess," and τ becomes a real ceiling on
performance.
