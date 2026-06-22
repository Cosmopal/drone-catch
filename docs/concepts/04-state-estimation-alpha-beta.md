# State estimation: the alpha-beta filter

## What it is

You never sense the true state — you get noisy, delayed measurements. An
**estimator** maintains an internal belief of the state and updates it in
a two-step rhythm every tick:

1. **Predict**: advance the belief with your dynamics model
   ("balls fall under gravity": v += g·dt, p += v·dt).
2. **Correct**: blend in the new measurement, weighted by trust:

```
p ← p + α·(p_measured − p)        # α: position correction gain, 0..1
v ← v + β·(v_measured − v)        # β: velocity correction gain
```

That's the whole **alpha-beta filter**. α=β=1 means "trust measurements
completely" (you get raw noise back); α=β=0 means "trust the model
completely" (you drift on model error). In between, the model carries the
state and the measurements trim its drift. With measurements at 240 Hz we
use α=β=0.2: convergence time constant ≈ dt/β ≈ 21 ms, and steady-state
velocity noise is cut to roughly a third.

**Relation to the Kalman filter**: a Kalman filter is this exact
predict/correct structure, but it *derives* the optimal α, β each tick
from explicit noise covariances (and handles correlations, multiple
sensors, time-varying trust). An alpha-beta filter is a Kalman filter
with the gains frozen at sensible constants — vastly simpler, and
adequate when dynamics are clean and rates are high, like here.

## Where we use it

`src/perception.py` — `BallEstimator`. Inputs are `BallPerception`
measurements (distance-scaled noise + 50 ms latency, modeling a stereo
camera). All catcher decisions — predicted landing, time-to-intercept,
catch trigger — read the estimate; nothing reads ground truth.

## What we learned here

- Estimate error at the moment of catch: **0.2–0.7 cm**, from measurements
  with ~1–2.5 cm noise. Filtering works.
- We instrumented the *miss vector* before blaming the estimator — and the
  estimator was innocent (failures were body positioning). Measure which
  stage owns the error before fixing any of them.
- High measurement rate is what lets fixed gains work. At 10 Hz
  measurements you'd want a real Kalman filter with proper covariance
  bookkeeping (it's also the principled way to fuse multiple sensors).

## For larger projects

The predict/correct decomposition is the master pattern of all estimation
(KF, EKF, UKF, particle filters differ only in how belief is represented
and how the blend weight is computed). Two transferable habits: write
down your dynamics model explicitly — it's doing most of the work; and
log estimate-vs-truth error in sim so you know your error budget by
subsystem.
