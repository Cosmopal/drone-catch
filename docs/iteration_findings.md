# Iteration findings: throw-and-catch tuning

Companion to `docs/throw_planning.md`. That doc explains *how* to plan a throw;
this one is the meta-level engineering log of what surprised us, what we
measured, and what we decided to defer. Audience is future-us (and any new
collaborator) trying to push the sim further.

The numbers below are from instrumented runs (`scripts/check_run.py` and
`scripts/plot_windup.py`) of the throw-windup-evade-catch loop in `src/main.py`,
with the cascade controller in `src/controller.py` and the planner in
`src/planner.py`.

---

## 1. The Lee SO(3) attitude controller has a near-singularity at large angles

The geometric controller's vee-mapped error magnitude is roughly
`|e_R| = 0.5 * |sin(angle_to_R_des)|`. That's mathematically obvious in
hindsight, but it has practical consequences we walked into.

- At a full 180° rotation, `sin(180°) = 0`, so `e_R = 0`. The controller
  literally cannot tell which way to rotate. This is the failure mode
  already documented in the deferred-work section of `CLAUDE.md`.
- The *near*-singularity bites earlier than you'd expect. At 159° (the kind
  of angle you hit when commanding a brake pose from a forward-tilted
  windup), `sin(159°) = 0.358`, so `e_R = 0.18`. With `kR = 0.3` (our
  current value), that's a torque of `0.054 N·m` against a maximum of
  `0.5 N·m`. The angular acceleration is `~23 rad/s²` instead of the
  available `~217 rad/s²` — about an order of magnitude weaker than the
  drone's actual capability.

What we observed in practice: rotating from a 30°-forward windup pose to a
130°-back brake pose took ~500 ms. During that window the drone effectively
coasts at its release velocity. Visually it looks like the ball is still
attached after release, because the body keeps drifting forward instead of
braking.

Workarounds, ranked by effort:

1. **Pre-flip during the last ~100 ms of windup** — what we did. Cheap and
   eliminates most of the visible lag. See section 2.
2. **Cap desired tilt at ~100° during the evade.** `sin(100°) = 0.985` gives
   nearly full `e_R`. You give up a bit of theoretical brake authority but
   get the controller out of the weak-error regime.
3. **Switch to a quaternion-error formulation.** The principled fix; on the
   deferred list. Worth doing once the workaround stops being enough.

## 2. Pre-flip windup choreography

The pre-flip is implemented in the throw-windup loop in `src/main.py`. In the
last ~100 ms of windup, we switch the drone's target to `home_pos` with
`vel_target = release_vel` and bump `max_tilt_deg` to 180°. The cascade then
computes a thrust vector pointing back-and-down (toward home, against the
current forward momentum), which means the drone starts rotating into the
brake pose *before* the ball is released — paying the rotation lag during a
phase where it doesn't matter.

Trade-off:

- Throw velocity drops by ~17% because the drone is being braked a little
  during the final windup ms.
- In return, peak post-release intrusion into the opponent half went from
  **1.55 m to 0.71 m** — more than a 2× tightening of the evade footprint.

We took the trade. The throw is still energetic enough; the evade is what
made the sim look broken.

## 3. The cascade delivers far less brake than its theoretical max

On paper, a quad at 90° tilt with full thrust gets about
`g * tan(90°) → ∞` in the limit, but bounded by available thrust we'd quote
~21.8 m/s² horizontal deceleration as the headline number.

Empirically, averaged over a brake period: **3–5 m/s²**. About 5× lower.

Two reasons:

1. The rotation lag from section 1 — the drone spends a meaningful fraction
   of the brake window not yet at brake attitude.
2. Controller transients — even after reaching attitude, thrust ramps up
   over the cascade's response time.

The planner originally trusted the 21.8 figure and consequently predicted
brake distances ~4× shorter than reality. The drone overshot release by
2–3 m into opponent territory.

Fix: `brake_decel` is now an explicit field on `PlannerInputs` in
`src/planner.py`, defaulted to **10 m/s²**. That's a deliberate compromise
between the theoretical ceiling and the observed floor. Bump it back up
toward 21.8 once the controller gets a real trajectory tracker that
pre-flips along the entire windup arc, not just the last 100 ms.

## 4. The underactuated quad has asymmetric x/z response

Position gains live in `src/controller.py`: `kp_z = 12`, `kp_x = 6`. Vertical
is twice horizontal. The reason is structural, not arbitrary:

- Vertical thrust is direct — body z is approximately world z in normal
  flight, so commanded z-thrust shows up as z-acceleration immediately.
- Horizontal thrust requires the body to tilt first. The tilt itself takes
  time (and shares authority with attitude tracking), so horizontal
  response lags vertical.

Net effect: when the planner targets a release point with matched-time
trajectories on both axes, the drone reaches `release_pos.x` with
`z ≈ release_pos.z + 0.2 m`. The ball is consistently released ~0.2 m above
plan. Visually, this reads as the drone "lifting and dropping" the ball
rather than tossing it from a stable hover height.

Candidate fixes (deferred):

- Rebalance gains. Risky because the current values are tuned for general
  flight and dropping `kp_z` to match `kp_x` will hurt hover.
- A proper trajectory tracker with position+velocity feedforward that knows
  about the asymmetry and biases the z target down to compensate.

## 5. Two-mode catcher: predict-landing OR direct pursuit

The original catcher always chased `predict_landing(target_z=HOVER_Z)` —
the XY where the ball would cross the catch height. Two failure modes:

1. The ball passes through `HOVER_Z` very briefly. With `vz = -4 m/s` you
   get ~30 ms at the catch altitude. Our control loop and grasp check
   simply don't sample fast enough to catch on a single frame.
2. If the ball drops *below* `HOVER_Z` before the catcher arrives at the
   predicted XY, `predict_landing` returns `None` (no real root for that
   target z anymore). The catcher's target then freezes at the last
   prediction and the ball falls past untouched.

Fix: when within 1 m of the ball, switch to direct 3D pursuit of the ball's
current position. Now the catcher converges on wherever the ball actually
is, regardless of altitude. The grasp threshold was loosened from 0.3 m to
0.5 m to match the new approach geometry.

Result: catcher catches consistently even from off-home start positions.
Predict-landing is still the right behavior for the long approach (gives
the catcher a stable lookahead), but pursuit is the right behavior for the
final tens of cm.

## 6. The min_tz vertical-thrust floor

The cascade in `src/controller.py` enforces a floor
`min_tz = 0.5 * total_mass * g` on the vertical component of the desired
thrust vector. This prevents the position controller from commanding the
body into a no-vertical-authority regime — a tilt past 90° where body z is
horizontal or pointing downward and the drone falls.

This floor is necessary in normal flight: a strong horizontal error with a
small vertical error can otherwise demand a tilt past 90°, and the drone
falls out of the sky chasing an XY target.

It also has to be dropped during the evade, because the whole point of the
evade is to actively push down — flip past 90° to brake vertical momentum
aggressively. The implementation: if `max_tilt_deg >= 90°`, the floor is
dropped. So bumping `max_tilt_deg` for the evade implicitly removes the
floor in the same call. One knob, two effects, intentionally coupled.

## 7. Empirical beats theoretical, every time

The biggest meta-lesson. Several paper estimates were off by integer
multiples once we measured them:

| Quantity              | Paper estimate | Measured        | Ratio |
| --------------------- | -------------- | --------------- | ----- |
| Brake decel           | 21.8 m/s²      | 3–5 m/s²        | ~5×   |
| Rotation lag (30→130°)| ~120 ms        | ~500 ms         | ~4×   |
| Drone climb in windup | 1.5 m planned  | 1.7 m actual    | ~1.13×|

The paper estimates assumed best-case actuator usage; the measurements
include the controller's actual trajectory through state space, including
the Lee error weakness (section 1) and the x/z asymmetry (section 4).

Lesson: validate paper estimates with one quick instrumented run before
trusting them in the planner. `scripts/check_run.py` was the high-leverage
tool that surfaced these — once it existed, every change came with a
measurement instead of a prediction.

## 8. Process: visualization markers as the debugging substrate

Before we added persistent markers, debugging looked like: print numbers,
read terminal, build a mental model of the geometry, hope it's right. After
we added them, you could pause the GUI and immediately *see* the geometry.

The current marker palette:

- White sphere — drone target
- Blue — catcher target
- Magenta — planner-committed release point
- Orange — actual release point (pinned at the moment the ball leaves)
- Yellow — ball aim point

The orange marker in particular surfaced the "drone trails the ball" issue.
Once you have a fixed reference point at the release moment, the gap
between it and the drone's later position is impossible to miss — and
that gap *is* the rotation lag from section 1.

Recommendation: when adding any new automated phase, also add a marker that
pins the planner's intent for that phase. Cost is ~5 lines of PyBullet
debug-draw; payoff is "I can see the bug" instead of "I think I see the
bug."

## 9. Process: diagnostic scripts unlock fast iteration

Two scripts ended up earning their keep:

- `scripts/check_run.py` summarizes a JSONL log: phase timeline, release
  state, post-release peaks, catch and cube-pickup outcomes. Run it after
  every sim. Avoids re-writing the same one-off `pandas` query each time.
- `scripts/plot_windup.py` plots planned vs actual position and velocity
  during the windup phase. The single image where the actual trajectory
  diverged from the planned trajectory made the controller-tracking-error
  issue obvious in a way no terminal output ever did.

Together they shortened the change-measure-decide loop enough that we tried
~10 variations of the pre-flip timing in an afternoon. Without them we'd
have tried two and called it done.

## 10. What we deferred and why

Not all known issues are fixed; some are mitigated and tracked. The
authoritative list lives in `CLAUDE.md`'s deferred-work section. Highlights
relevant to this iteration:

- **Quaternion-error attitude controller.** The principled fix for the Lee
  singularity (section 1). Worth doing when the `e_R` weakness starts to
  dominate the remaining error budget. Currently mitigated by the pre-flip
  workaround (section 2).
- **Proper trajectory tracker** with full pos+vel+accel feedforward over the
  windup arc. Would eliminate the matched-t-vs-actual mismatch (section 4)
  and let `brake_decel` move back toward its theoretical value (section 3).
  Currently mitigated by the matched-t single ramp + pre-flip combo.
- **Soft catch (velocity-matched grasp).** Already in `CLAUDE.md`. Catcher
  currently snaps a fixed constraint at grasp time; on real hardware that
  impulse would shock the airframe. Sim hides it.
- **Real catch geometry** (gripper-position aware, not body-COM aware).
  Already in `CLAUDE.md`.
- **Closing the loop.** Catcher should throw the cube back to the thrower
  for an actual play-catch, not just a one-shot throw + catch + pickup.
  The throw planner is now general enough to support this — the work is
  symmetrizing the demo phase machine.

## 11. Compliant capture: stop velocity-matching, start impulse-spreading

The rigid constraint snap forced a rel-vel gate (≤1.5 m/s) on the catch
trigger, and the velocity-matched arm sweep alone couldn't hit it: at the
matched instant the arm tip's centripetal acceleration (ω²L ≈ 53 m/s² toward
the shoulder) opposes the ball's gravity vector, so the tangency window is
~27 ms for the rel-vel gate, ~74 ms for the 15 cm distance gate. No amount of
sweep tuning widens that — it's curvature mismatch between a circle and a
parabola.

The fix was to delete the rel-vel gate and absorb the residual through
compliance (`tests/arm_catch_solo.py`, M5):

- **`soft_grasp`**: point-to-point constraint capped at 8 N. The ball
  decelerates over ~m·Δv/F_max (≈60–80 ms, ~10 cm stroke) instead of one
  solver step. Stands in for foam pad + compliant fingers on hardware.
- **Back-drivable shoulder**: during absorption the sweep keeps its velocity
  target but with `torque_cap=0.3` N·m (vs 2.0 max), so the joint yields
  under ball load — most of the absorption stroke happens here.
- **Two-stage lock**: when rel_vel < 0.3 m/s, `firm_grasp` ratchets the
  constraint stiff and the shoulder brakes to ω=0 in velocity mode (the
  documented-safe transition).

Validated across an adversarial incoming-velocity grid (vx 2.5–5.5,
vz −2.0 to −4.5; speeds 3.2–7.1 m/s, descent angles 20–61°): **12/12
caught and retained**, contact rel-vel up to 4.6 m/s, peak constraint force
8–11.3 N, impulse matching m·Δv within the gravity contribution.

Lessons earned along the way:

- **Ramp integral must equal the rotation.** The absorption sweep ramps
  ω from 0 to Ω over the window T, so it covers ∫ω dt = Ω·T/2 — not Ω·T.
  Size T = 2·Δθ/Ω so the shoulder lands on the velocity-matched angle
  exactly at intercept. Both "arrive late" (fixed 100 ms window) and
  "arrive early" (margin factor > 1) turn catches into misses; the failure
  pattern across the grid flips between fast-shallow and steep arrivals,
  which is the diagnostic signature for a timing (not force) problem.
- **Recompute the ramp from t_intercept every tick.** A one-shot engagement
  that latches full ω overshoots the catch angle long before the ball
  arrives.
- **Tests run in the DEFAULT room (8 m → walls at ±4); the demo overrides
  to 10 m.** A launch point computed at x = −4.3 spawns the ball inside the
  west wall and it never arrives. If a test's "closest approach" is ~5 m,
  check the spawn geometry before the controller.

## 12. Noise + positioning: the catch is information-and-stiffness limited, not arm-limited

Extended `arm_catch_solo` (M5b) with the question "does compliant capture
survive realism?": stereo-class sensing noise + 50 ms latency (the demo's
`BallPerception`, now shared via `src/perception.py`), wind gusts (OU
process, ~5% of weight), catcher pre-position error, and — separately —
intercepts the ball is NOT aimed at (lateral offsets up to 1 m, crossing
balls with vy up to ±0.8 m/s, ±0.3 m depth offsets).

Results after fixes: **96/96** across four grids (velocity envelope ×
{clean, noise}, positioning envelope × {clean, noise}, 3 seeds per noisy
cell). What it took, and what we learned:

- **Latency compensation is mandatory, and trivial.** Acting on the raw
  50 ms-delayed measurement costs rel_speed·latency ≈ 23 cm at nominal —
  more than the whole 15 cm catch radius. An alpha-beta filter on the
  delayed state, extrapolated forward by the latency under gravity
  (`BallEstimator`), brought estimate error at contact to 0.2–0.7 cm.
  Estimation was never the bottleneck after this.
- **Miss anatomy beats hypothesizing.** Logging the miss *vector* at
  closest approach showed noisy-positioning failures were 10–21 cm in
  **y** with sub-cm estimate error: pure body-positioning lag, not
  sensing. This killed two attractive wrong fixes (see below) and answered
  the "do we need the elbow?" question: **no** — both arm joints rotate
  about y, so lateral error is body-only; no arm DOF can recover it.
- **Velocity-target carrots are gain changes in disguise.** The cascade's
  outer loop is accel = kp·err + kd·(vtgt − v). Commanding vtgt = K·err is
  algebraically a kp increase of kd·K with no matching kd: ζ fell 0.82 →
  0.58 and the body oscillated through the catch window (clean grid 12/12
  → 0/12). Commanding vtgt = dist/t_remaining is worse: the kd term
  *punishes* exceeding the just-in-time average, capping the body at a
  crawl, and any fade-out brakes it while still off-station. If the loop
  is too slow, retune the loop.
- **The actual fix was two numbers.** Catcher-local kp [6,6,12]→[12,12,14],
  kd [4,4,6]→[7,7,7]: ωn 2.45→3.5 rad/s at ζ≈1.0. Bonus: static gust
  offset (F/(m·kp)) halved to ~4 cm. Attitude inner loop at ~11 rad/s keeps
  ≥3× separation, and gain scheduling holds that across arm poses.
- **PyBullet constraint maxForce caps each axis independently** — observed
  peak force saturates at 8·√3 ≈ 13.9 N with an 8 N "cap". Budget for the
  √3 factor when reasoning about airframe loads.

The elbow stays in the parking lot: it becomes relevant for in-plane
terminal correction when tolerances tighten (3-finger gripper contact
geometry), not for making the current catch robust.
