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

## For larger projects

Measure your pipeline's latency end-to-end (timestamp at sensor, compare
at decision) — then model it explicitly. Cheap insurance: prefer
*overestimating* τ slightly. And remember extrapolation quality = model
quality: against maneuvering targets or strong drag, long-τ extrapolation
degrades from "exact" to "guess," and τ becomes a real ceiling on
performance.
