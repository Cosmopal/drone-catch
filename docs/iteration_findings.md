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

## 13. Finger (caging-gripper) catch: feasibility probe — mechanism works, dynamic rendezvous doesn't (yet)

The force-limited constraint ("foam stick", §11–12) is a *behavioral* stand-in
for a real gripper: it can snap to a ball 15 cm away at any relative velocity.
To test whether a physically honest catch — fingers caging the ball, held by
friction, no constraint — is feasible, we built a 3-finger gripper
(`assets/make_gripper_urdf.py` → `quadrotor_gripper.urdf`, two-segment
fingers) and `tests/finger_catch_solo.py`.

**Verdict: the gripper cages reliably when the ball is placed in the cup, but
the in-flight rendezvous can't yet put the cup on the ball.** Getting even
this far required fixing a cascade of platform problems the foam stick hid —
which is itself the answer to "is the foam stick a good proxy?": no.

What broke, in order, and why:

1. **Finger motors excite the attitude yaw singularity.** With the arm
   extended horizontally (catch pose) and the gripper open, a stiff or
   velocity-driven finger servo injects a dynamic disturbance that drives the
   body's yaw toward ±90–180°, straight into the Lee SO(3) singularity (§1) —
   the drone flips and flies away (180 cm error). Diagnosis was decisive:
   freezing the fingers kinematically → 2 cm error, 0° yaw; motorizing them →
   180 cm, 179° yaw. Fix: **gentle pure position control** on the fingers
   (positionGain 0.6; higher gains are *also* unstable — PyBullet's explicit
   joint-motor PD goes numerically unstable at high gain on near-massless
   links). The static asymmetric gripper is fine (its gravity torque is pure
   pitch, which the cascade rejects); only the *motor dynamics* hurt.

2. **Two steady offsets the demo never needed.** The gripper's COM offset
   gives a ~12 cm hover position sag (no position integrator existed), and the
   residual finger yaw torque leaves an ~18° steady yaw (attitude `kI` had a
   zero yaw term) — and since the arm points body-−x, 18° of yaw throws the
   EE 12 cm sideways. Both became direct EE-to-ball miss. Fixes: a
   position-error integrator (`controller.kI_pos`, default off) and a nonzero
   yaw integral. Both null their offset to ~1–2 cm but need ~2.5 s to wind up,
   so the catcher now settles longer before the throw.

3. **Mass was hardcoded.** `MASS=0.625` vs the gripper's real ~0.646 kg →
   gravity-FF undershoot. Replaced with `self.mass` summed from the model at
   load (negligible change for the plain drone; correct for the gripper).

4. **The fingers ~double the arm's rotational inertia** (≈0.004 kg·m² added at
   the tip), so the velocity-matched absorption sweep lags — and the timing is
   *sensitive*: ±0.2 in the sweep-start margin swings the closest approach by
   ~7 cm, and at the closest instant the shoulder is at −54° or −23° rather
   than the intended −44°. Torque doesn't help (the sweep is ω-limited, not
   torque-limited).

5. **Cup depth, not palm rim.** The fingers converge ~4 cm beyond the
   end_effector link, not at it. Targeting the EE-link onto the ball left the
   ball at the rim; a stationary-ball cage test found the sweet spot
   (`cup_depth=0.04` → 3 fingers, caged; 0.06 → ball falls through behind the
   closing fingers). Targeting now uses an effective arm length `L+cup_depth`.

After all five, the static cage works (ball placed at the cup → held), the
contact relative velocity at close drops to ~0.5 m/s (good velocity match),
but the **dynamic closest approach plateaus at ~7–10 cm of cup-to-ball miss,
roughly independent of ball speed (1.8–4.6 m/s)** — so it's not a
contact-window problem, it's a *rendezvous-precision* problem. The single
shoulder DOF sweeps the cup through an arc, and landing that arc on the ball
at exactly the intercept instant — with the heavier arm's lagging dynamics —
is too tight. The miss is dominated by vertical and the swept-angle error.

**The clean implication: this is what the elbow is for.** A 2-DOF arm can
servo the EE to a *point* (and track it for a window) instead of sweeping a
1-DOF arc through it — turning a knife-edge timing problem into a tracking
problem. That moves parking-lot item "unlock the elbow" from nice-to-have to
the critical path for a contact catch. The constraint-based compliant capture
(§11–12) remains the working catch for the demo; the finger gripper is a
validated *mechanism* waiting on 2-DOF terminal guidance.

Reusable infrastructure landed regardless: the URDF gripper generator, the
`Drone` finger API (`open_gripper`/`close_gripper`/`fingers_touching`/
`set_finger_dynamics`), model-derived mass, and the position + yaw integrators
(all default-off, so existing tests are unaffected — re-verified).

## 14. Unlocking the elbow: 2-DOF tracking turns the catch from tangency into rendezvous (M7)

§13 ended with the 1-DOF finger catch stuck at a ~7–10 cm rendezvous miss:
one shoulder joint sweeps the cup through an *arc*, and landing that arc on
the ball at the exact intercept instant is a knife-edge. Unlocking the elbow
gives the end-effector 2 planar DOF — so instead of sweeping through the ball,
the arm **servos the cup onto the ball and tracks it**.

Foundation: `src/arm_kinematics.py` — forward + inverse kinematics for the
2-link arm in the body sagittal (xz) plane. Both joints rotate about ±y, so
the arm is a planar 2R manipulator; with equal 0.2 m links the IK is closed
form (`r = 2L·cos(θ₂/2)`, take the θ₂≥0 elbow-forward branch, cap below the
inverted-pendulum fold). **Verified exact (0.0 mm) against PyBullet's
`getLinkState`** across poses, which also confirmed the elbow sign (forearm
absolute angle = θ₁ − θ₂).

Catch strategy (`tests/elbow_catch_solo.py`): station the body so the
shoulder sits ~0.32 m *above* the intercept (arm hangs into the ball's path);
each tick, IK the desired cup position (ball + small ballistic lead) to
(shoulder, elbow) and command both via `hold_arm`; body holds the x-station
and tracks the ball's y (the arm is planar — can't move laterally); fingers
cage as in §13.

**Result: it works.** Nominal (4.6 m/s arrival): the cup tracks to **0.9–1.3
cm** of the ball (vs 7–10 cm for the 1-DOF sweep), 3 fingers cage, held
through a 30 cm lift. That is the headline — 2-DOF tracking converts the
rendezvous-precision wall into a solved tracking problem at the design point.

**Robustness across the full velocity envelope is not there yet: 4/12 held**
(`--grid`). The mechanism is sound everywhere — several misses get the cup to
1–3 cm — but two control-quality gaps remain:
- *Tracking accuracy* degrades for the fastest/steepest balls (cup miss
  7–11 cm): the arm slews at its joint-rate limit and the ball is in the disk
  only briefly. A continuous pre-aim (extend the arm toward the ball, clamped
  to the reach boundary, before it enters the disk) *hurt* — the arm chases a
  moving clamped point — so the fix is proper feedforward tracking, not a
  geometric hack.
- *Capture timing*: some cells reach ~2 cm cup-miss but still don't cage —
  the ball crosses the cup with too much relative velocity for the fingers to
  wrap in time. Needs the cup to **velocity-match** (track the ball's velocity,
  not just position) at contact, plus possibly a faster finger close.

So M7 validates the elbow as the right unlock and clears the §13 blocker at
the design point; making it hold across the adversarial envelope is a
tracking-control problem (velocity-matched IK tracking + capture timing),
not a kinematics or mechanism one. Open items: extend the arm-reaction FF and
gain schedule to the elbow angle (currently shoulder-only, so the FF is
approximate with the elbow bent — the body integrators have been absorbing
the residual), and add lateral (y) approaches once a singularity-free
attitude controller exists.

## 15. Caging gripper that actually cages: 3-joint long-proximal fingers (M8)

§13 left the finger gripper *containing* a ball in an upright cup but not
*caging* it — a screenshot review exposed that the 2-segment fingers, with a
mount ring (2.5 cm) smaller than the ball radius (3.0 cm), folded back over
the wrist instead of enclosing. The honest gate is the **inversion test**:
close on the ball, rotate 180°, does it stay? The 2-segment hand failed it in
every one of ~58 configs (mount radius, lengths, angles, force, friction,
soft contact) — 3 thin rigid fingers achieve *force closure* (friction at a
few points, orientation-fragile), not *form closure*.

The fix (user's idea) was **3-joint fingers with a long proximal phalanx**,
human-like: a long proximal (≈55 mm) reaches down past the ball's equator,
then shorter middle (≈32 mm) + distal (≈25 mm) curl UNDER it to meet
beneath — geometric trapping. Mount ring raised to 3.4 cm (> ball radius so
fingers start outside the ball). With this, **8/… configs pass the inversion
test**; 4 fingers is the most robust (more enclosure, more contacts). The key
was the long proximal — equal/short segments curl into a loop near the mount
and never reach down to the ball.

Productionized into the real catcher (M8):
- `make_gripper_urdf.py` generalized to N-segment fingers (`finger{i}_seg{k}`);
  default 4 fingers × 3 segments, `SEG_LENS=(0.055,0.032,0.025)`.
- `Drone` finger API generalized: `finger_joints` is now a list of per-finger
  segment lists; open/close drive per-segment angle tuples (`config.finger_open`
  / `finger_close`). `fingers_touching` unchanged.
- **12 PD finger joints on a floating base diverge the body (~80 cm)** — the
  default contact solver can't hold them (the *static* hand is fine; it's the
  motor loops). Two fixes: `numSolverIterations=150` (→ 4.9 cm) and, better,
  **pin the fingers kinematically while OPEN** (`resetJointState` each step →
  1.2 cm hover) and only motorize to close. Pin-open is now the default in
  `_apply_gripper`; the catch test also bumps solver iterations. The old yaw
  singularity (§13) does not recur with this.
- Validated on the drone: hover stable, 4 fingers close on a ball at the cup,
  **held through a 30 cm lift** (static-ball).

**Dynamic catch status (`tests/elbow_catch_solo.py` with the new hand):** the
2-DOF IK tracking puts the cup on the ball to **2.0 cm** and all **4 fingers
contact** — but it does NOT yet retain: the ball arrives at ~2.3 m/s relative
and punches through the cup before the fingers firm. Position tracking is
solved; **velocity matching is not.** To cage a *moving* ball the cup must
move WITH it at contact (match velocity, not just position), which needs
Jacobian-based joint-velocity control on the 2R arm — the M7 frontier, now
the single critical-path item for a retained physical catch. The pin-open
(tight station-keeping) and firm-grip-after-cage + gentle-lift pieces are in
place; they're necessary but not sufficient without velocity matching.

## 16. Pre-positioning lands the first retained physical catch (M8b)

The M8 catch tracked the cup to ~2.7 cm and caged the ball with 4 fingers but
did NOT retain it. Diagnosis (per a video review):
- **The arm engaged ~90 ms before contact** — it sat in a READY pose until the
  ball entered TRACK_RANGE, then *snapped* to the tracking IK solution
  (shoulder 0°→−25°, elbow 51°→96° in ~0.1 s). Violent, and late.
- **The ball seated at the cup RIM (~3 cm off-center), not the center.** The
  static cage (ball placed at center) held through inversion + lift; a
  rim-seated ball gets only partial form closure → it works loose in ~1 s and
  any acceleration ejects it.
- **The post-catch logic ejected it.** Firming the grip to 2.0 N·m produced
  100–166 N contact forces on a 0.64 N ball (rigid sphere in rigid cage) and a
  lift jolted the rim-seated ball out. Removing the firm-grip → held ~1 s in
  place, but the gentle lift still lost it.

**Fix: pre-position the cup at the PREDICTED intercept from the start and hold
it there, refining to the actual ball only when close.** Result on the
nominal throw: cup-to-ball **0.7 → 0.5 cm**, the ball seats at cup-center, 4
fingers cage it, and it is **HELD through the lift — caught=True, held=True.**
First retained physical catch. No snap (the arm is already in place; the
prepos→track transition is smooth because the ball arrives where it was
predicted).

**Why this works where the M7 "pre-aim" failed.** The two are NOT the same.
M7 pre-*aim* extended the arm toward the *moving ball*, clamped to the reach
circle — which (a) targets the ball's radial projection, a different point
than where its parabola actually enters the disk; (b) chases a point that
races around the circle as the ball nears, at the joint rate limit; (c) parks
the arm at near-full extension, a Jacobian-singular pose, right when it must
retract. Pre-*positioning* at the *fixed predicted landing* has none of that:
the arm sits still at a good pose and waits for the ball to fall into the cup.
The lesson: aim at where the ball *will be* (the intercept), not at where it
*is* (the moving target).

**Still open: full-envelope robustness (2/12 grid).** Off-nominal velocities
arrive at the intercept on different approach lines/timing than the fixed
pre-position + station height anticipate, so the cup misses by 4–12 cm there.
Closing that needs velocity-matched tracking + per-velocity station/pre-
position adaptation. But the mechanism + nominal catch are now real:
4-finger form-closure cage, ball seated at center, gentle grip (no 100 N
squeeze), retained through a lift.

Side notes answering review questions: **4 fingers is not too sparse** — with
the ball seated at center the form-closure cage holds; the earlier slip was
*seating* (rim), not finger count. **Gentle is better than firm** — the
removed firm-grip was the main ejector. **"Arm fully down" is the wrong
default** — the principled start pose is the IK pre-position that puts the cup
at the intercept (arm angled), not straight down (cup straight below body).

## 17. Why the snap is intrinsic, and the cage catch is noise-fragile (M8c)

Two review questions: the arm still *snaps* into place, and does it survive
sensing noise?

**The snap is intrinsic to how this gripper receives the ball.** Traced it:
during "prepos" the arm holds the cup at the intercept (z=1.5); when tracking
engages (ball within TRACK_RANGE, t≈0.82), the cup target jumps to the ball's
actual 3-D position (z≈1.79) and the elbow rockets 45°→96° (~1600°/s). Tried
three ways to remove it, all of which BROKE the catch:
- *Track the predicted landing point* (cup waits at z=1.5, ball falls in):
  the ball grazes the upward-splayed OPEN finger tips ~8 cm above the cup,
  deflects, and the prediction jumps → cup chases away. Clean miss.
- *Track the ball's xy at intercept height* (cup slides under the ball, no z
  rise): same graze — the ball lands on the finger tips, not in the cup.
- *Slew-limit the joints*: the arm lags the fast descending ball → miss.

Root cause: the cup must RISE to **meet** the ball and descend WITH it, so the
cup *mouth* faces the incoming ball and the ball enters cleanly. A stationary
or below-the-ball cup presents the finger tips, which deflect it. The "snap"
is that rise. TRACK_RANGE=0.45 is a sweet spot (later → ball deflects before
the cup arrives; earlier → cup chases the ball from out of reach). A genuinely
smooth version needs **velocity-matched tracking from apex** — the cup follows
the ball's predicted trajectory down continuously, matching its velocity, so
there's no engagement step. That remains the open problem (the M7/M16
frontier); the snap and the noise-fragility below are two faces of it.

**The cage catch is precision-tight and noise-fragile.** Added perception
(`--noise`: stereo-class noise + 50 ms latency + `BallEstimator`). The nominal
catch that holds cleanly on ground truth **fails 0/3 under noise** — min
cup-to-ball blows out to ~22 cm because the chase tracks the jittery
*estimate* of the ball's instantaneous 3-D position, and the descent flag
(est_v_z<0) flickers, oscillating track/prepos. Contrast the constraint-based
**compliant capture (§12): 96/96 under the same noise.** The difference is the
catch *radius*: the soft constraint snaps anything within 15 cm, forgiving the
estimate error; the finger cage needs the ball seated at the cup CENTER
(~1–3 cm), which sensing noise destroys. **The hardware-honest gripper is far
less noise-tolerant than the behavioral soft-constraint stand-in** — caging
demands precision the constraint didn't. Closing this needs (a) velocity-
matched tracking on the *smoothed* estimate (track the predicted landing/
trajectory, not the instantaneous noisy position) and (b) possibly a more
forgiving cage (bigger mouth / more fingers / compliant pads) so center-
seating isn't required to sub-cm. Both are the same lesson as the snap: track
where the ball *will be*, smoothly, not where the noisy estimate says it *is*.

### 17b. Tried "glide the arm in early" — the snap is an active SCOOP, not wasted motion

Review idea: the arm sits idle for ~0.8 s then does everything in 0.1 s — so
glide it into the pre-aim pose over the available flight time instead of
snapping. Implemented it properly: pre-position the cup at the MEETING point
(where the ball crosses MEET_Z=1.62 on its descent, above the intercept) and
let the arm glide there over the whole flight, so the final move is a small
correction. **It missed (7–8 cm), same graze.** With a tracking latch it
chased the deflected ball out to x=1.48.

The reason is mechanically important: the working "snap" gives the cup
**upward velocity** at the instant it meets the ball — the cup mouth *scoops*
the descending ball inward. A stationary or gently-gliding cup, even correctly
positioned at the meeting altitude, presents the upward-splayed open finger
TIPS to the falling ball, which deflects off them. So the snap is not wasted
motion to smooth away — it's the active scoop that makes this gripper catch.
Every "slow it down" variant (slew-limit, track-landing-point, track-xy-at-
height, meeting-point glide) removed the scoop and grazed.

Implication: a gentle/smooth catch needs either (a) a passive basket-style
end-effector (mouth-up funnel the ball simply falls into — no scoop needed),
or (b) velocity-matched tracking where the cup is already descending WITH the
ball so contact has ~zero relative velocity and no graze. The current 3-finger
caging hand is an active scooper; that's the trade for its form-closure grip.

## 18. Velocity-matched tracking: infrastructure built, but it doesn't beat the scoop yet (M8d)

Chose option 2 (velocity-matched tracking) over a passive basket, to keep the
arm multi-purpose. Built the foundation:
- `arm_kinematics.jacobian(θ1,θ2,le)` — 2×2 Jacobian of the arm tip (le =
  L2+cup_depth to control the cup). Verified exact (2e-7) vs finite-diff.
- `arm_kinematics.ik_velocity(...)` — damped-least-squares J⁻¹·v → joint
  velocities for a desired cup velocity.
- `Drone.hold_arm(..., shoulder_vel, elbow_vel)` — joint-velocity feedforward
  through PyBullet POSITION_CONTROL's targetVelocity (defaults 0; no effect on
  existing callers — verified arm_catch_solo unaffected).

But naive use did NOT improve the catch, for two compounding reasons traced
in sim:
1. **Position-loop slew swamps the velocity FF.** Engaging the velocity-matched
   track from the intercept pre-pose leaves a ~47 cm position error (cup at
   z=1.5, ball at z=1.79); the position PD slews the joints to ±89 rad/s to
   close it, so the actual cup velocity is nothing like the commanded ball
   velocity (rel-vel at contact 8.8 m/s, WORSE than the scoop's 2.3).
2. **The fix for #1 — pre-position at the meeting altitude so there's no
   position error — puts the arm at a near-SINGULAR pose.** The ball enters
   the reachable disk at its boundary (full extension), where the Jacobian is
   rank-deficient; pre-positioning the cup there sent it to z=2.2 (IK blew up).

So clean velocity matching needs the cup to *co-move with the ball through the
reachable disk from a good (non-singular) pose* — a proper task-space
trajectory controller (feedforward the whole descending arc, blend position +
velocity with consistent targets), not a per-tick position-IK + velocity-FF
bolt-on. That's the real next step. The committed catch remains the SCOOP
version (§17b): nominal caught + held, with the snap, noise-fragile. The
Jacobian/velocity infrastructure is in place for the trajectory controller.

## 19. The catch runs near full extension — the solver under-models the movement (M8e)

Human-catch review: position the arm partly FOLDED, let the joints ABSORB the
ball's momentum, and sweep so the arm trajectory OVERLAPS the ball's (redirect
it out of the parabola), instead of meeting at a point. Asked: are we
under-modeling the movement in the solver? **Yes.** Traced the working catch:
the arm runs at **84–93% extension** (elbow 44–66°) through the whole approach
— nearly straight, right where the Jacobian is singular. The IK optimizes ONE
term (cup position) with nothing for: staying folded (it clamps to 98% reach
when chasing), compliance (stiff position control, no give), or trajectory
overlap (tracks a point, not the path).

Tried the fixes; each hit the same wall:
- **Compliance** (back-drivable arm at contact, `hold_arm(torque_cap=...)`):
  broke the nominal catch. The current catch is a SCOOP (§17b) — it needs the
  arm FIRM to drive up and meet the ball; compliance fights that. Absorption
  needs a non-scoop catch.
- **Stay folded** (lower the station, raise the elbow-fold limit): also broke
  it. The arm reach (0.40 m) vs the catch distance (~0.32 m to the intercept)
  means the catch is *inherently* ~90% extended; lowering the station needs
  more fold than the arm allows, and raising the fold limit makes the IK fold
  the arm UP at close range and miss.

**Root cause (the user's intuition, made precise): the arm operates too close
to full extension because it is barely long enough for this catch geometry.**
That single fact causes all three symptoms — the Jacobian singularity that
swamps velocity matching (§18), the lack of fold that blocks compliance, and
the scoop (the only way to reach the fast ball at the boundary). The clean
fixes are *geometric*, not control tweaks:
1. **Longer arm links** (e.g. 0.25+0.25 = 0.50 m reach) so the same catch is
   ~64% extension — folded, well-conditioned Jacobian, room for the joints to
   give. (Costs: re-tune throw/mass/inertia for the longer arm.)
2. **Reach diagonally toward the incoming ball** (body offset so the arm
   reaches a shorter distance into the ball's path) rather than straight down
   to a far intercept.
Either makes the folded + compliant + velocity-matched (trajectory-overlap)
catch geometrically feasible. The Jacobian/velocity-FF (§18) and the
back-drivable `hold_arm(torque_cap=)` are the control pieces, waiting on the
geometry. The committed catch stays the scoop (nominal caught+held).

## 20. Diagonal velocity-matched catch: built the human-inspired geometry; body won't hold the station (M9, WIP)

The user corrected my "arm too short" framing (§19): the drone CAN position
better, and the right placement is the one the throw-side `arm_catch_solo`
already used — **station the body up-and-forward of the intercept so the arm
reaches FOLDED, back-and-down, and its swing is TANGENT to the ball's path**
(sweep ALONG the ball, not scoop up into it). Why this is the right idea:
- The 90% extension is from the SCOOP reaching up to the high/fast ball, not
  the catch distance (straight-down is only 72%). Confirmed: body-tracking the
  ball's x did NOT reduce extension — the drone is too slow to follow 3.3 m/s
  horizontally, and the ball is near/above the shoulder during the approach.
- Diagonal placement: shoulder R_FOLD (0.355 m) from the intercept,
  perpendicular to the arrival velocity. The arm is then FOLDED (~74%, elbow
  ~1.3 rad) at the tangent — well-conditioned Jacobian, so velocity matching
  (§18) isn't swamped, and room for the joints to give (§19 compliance).

Built it (`tests/elbow_catch_diagonal.py`): diagonal station, fold pre-pose,
track the tangent point with Jacobian velocity feedforward sweeping the cup
along the ball. The arm IS folded at the tangent (the geometry works). **But
it does not catch (~12 cm miss): the body can't hold the forward-diagonal
station** — it settles ~0.35 m low and oscillates ±13 cm during flight, so the
cup never sits steadily at the tangent. The forward COM offset + the
folded-back arm make a bigger pitching disturbance than the overhead station;
the position loop (tuned for overhead) doesn't hold it.

So the geometry is right and the control pieces (Jacobian FF, back-drivable
joints) are in place — the remaining blocker is **station-keeping at the
diagonal pose**: retune the position loop / add a COM-offset feedforward for
the forward-and-tilted hold, then the tangent catch + absorb should follow.
The committed working catch stays the SCOOP (`elbow_catch_solo.py`, nominal
caught+held); the diagonal version is the WIP toward the smooth folded catch.

## 21b. Startup ceiling-launch: a feedforward firing on the arm's init snap

User asked why the catcher rockets ~1 m up at t=0. A/B isolated it cleanly:
`arm_translational_ff_z` ON → peak z-error **+1.01 m**; OFF → **+0.01 m**.

Mechanism: the `Drone` inits the arm at its folded rest pose (shoulder −π/2).
`hold_arm(pre_pose)` then drives it ~85° to the catch pre-pose. The arm inertia
is tiny (~0.004 kg·m²), so even the 2 N·m motor cap gives α ≈ 500 rad/s² — it
slews the 85° in ~0.1 s (and overshoots). `arm_translational_ff_z` predicts the
body-z disturbance from arm motion and pre-cancels it; it's meant for the
*throw's* controlled sweep, so it reads this violent init slew as a giant
disturbance and slams in upward thrust → launch. (Answers a second user
question — *yes*, the motors really can snap it that fast; the arm is light, the
cap isn't the limit.) Fix: `resetJointState` the arm to the pre-pose at init so
there's no slew. Removes the launch (peak +0.01 m).

Side effect worth noting: removing the launch made the diagonal catch's miss
*consistent* (~11.5 cm across all kI_pos/kd) instead of a lucky 3 cm — the
3 cm had depended on the launch transient putting the body at a fortunate
settle phase. The honest state: the body settles to a steady COM-sag offset and
the cup lands ~11 cm low/back. That steady, known offset is precisely what a COM
feedforward cancels (§21) — feedback tuning can't, it only moves the phase.

Finger-cam (user request) confirmed the capture-side failure: the ball sits at
the cage RIM, off-center, and the closing fingers on the near side *paddle it
out* rather than wrapping it (the cup must seat the ball past the fingertips —
§09 sweet spot). So there are two independent gaps to a retained catch: body
station-keeping (COM FF) AND cup-centering at contact.

## 22. Design study: a thrust-vectoring drone to kill the underactuation (decision, not yet built)

The user asked whether an **over-actuated** drone (rotors with tilt DoF) would
fix the root cause behind most of our pain: a fixed quad is underactuated
(4 inputs, 6 DoF), so it *must* pitch the whole body to translate — which is
exactly what fights the arm (§20 station-keeping), forces the cascade, and
gives the Lee 180° singularity. Conclusion: yes, and it's worth doing. Full
reasoning + the transferable concepts are in `concepts/12`. The decisions we
landed on (so future-us doesn't re-derive them):

- **Mechanism**: one tilt servo per rotor → 8 control inputs vs 6 DoF →
  over-actuated, 2-dim null space. (NOT 2 servos/rotor — that's an 8-servo
  omnidirectional gimbal we don't need.) Replaces the cascade with a single
  wrench → control-allocation map: command position AND attitude independently,
  no thrust→attitude inversion, no 180° singularity. The allocation
  (pseudo-inverse + null-space objective) is the one new subproblem; the rest
  of the architecture *simplifies*.
- **Layout: quadrant (X), not plus (+).** Rotors at `(±0.10, ±0.10)`. The
  axis-aligned catch plane (`y=0`) threads the gap between the two near rotors
  (nearest disk edge 0.06 m off-axis), so the downwash columns straddle the
  ball path. A `+`-config puts a rotor on the catch axis — worst case. The
  current URDF already *is* quadrant, so no change needed there.
- **Tilt: radial (hinge along the arm), not tangential.** Two clean reasons,
  both worked out by hand: (1) radial thrust points through the hub, so its
  wash plane passes through the *center* (the `x=±y` diagonals, 45° off the
  catch axes) — tangential's wash plane is offset out and slices the catch
  region (crosses `y=0` at `x=−0.20`, right at the folded EE). (2) Radial force
  has zero moment arm → **zero yaw torque**, so tilts give clean decoupled
  `Fx, Fy` and yaw stays on drag-torque differential (like today). Tangential's
  only edge is tilt-based yaw, which we don't need for axis-aligned catches.

How this got decided: it started as "longitudinal (fore/aft) tilt" but the user
flagged that **y (sideways) motion is coming**, which forced the general
tangential-or-radial single-servo design that spans the whole horizontal plane
with 4 servos. The wash question — does a tilted rotor blow the incoming ball
off course — drove both the layout and the tilt-axis choice; the user's instinct
that radial "fixes the planes in which I experience wash" was correct and is now
backed by the `y=0`-crossing geometry above.

**Important caveat:** PyBullet has no propwash model, so *none* of the wash
analysis is testable in the current sim (a tilted rotor has zero effect on the
ball). The wash reasoning is a hardware/sim2real design argument. A minimal
propwash-cone disturbance (§concepts/12) would make it testable and let us
validate null-space wash-steering. Nothing is implemented yet — this section is
the decision record so the URDF + allocation work starts from the right place.

## 23. Methodology: scalar metrics hide failure MODES in a physics sim — you have to LOOK

The most consequential M9 bugs were diagnosed by the USER visually examining
video frames, not from the metrics the work was being steered on. Two rounds:

- The ~11 cm "miss" read (from the numbers) as a position/timing error was
  actually a cup-**orientation** failure: the cup mouth pointed down-and-back
  (forearm ~−65°), so a ball descending from above hit the *upper finger* and
  deflected. Invisible in `min_cup_d`; obvious in one frame.
- `held=True` hid that the grasp was a fragile **fingertip pinch**. Under the
  position uncertainty that always exists, an off-center ball makes a
  *fixed-pose* finger close press *onto* the ball instead of enclosing it, and
  the one-sided contact forces squeeze it back out. The scalar said "success";
  the frames showed it was one perturbation from failure (and motivated the
  move to an adaptive/compliant close — underactuated grasping is robust to
  pose uncertainty *because* it conforms instead of servoing to a shape).

The transferable lesson is about method, not the catch: **in a physics sim the
outcome of a contact/geometry interaction lives in the geometry and contact
dynamics, which scalar logs (`held`, `min_dist`, contact-count) compress away.**
A binary "success" is a lie of omission when the margin is razor-thin or the
mechanism is wrong — verify *how* it succeeded, not just *whether*.

For a text-first agent specifically: rendering a video as an *output for the
human* is not the same as examining it as an *input for analysis*. The agent
*can* read frames (image input) and should extract and study them when
debugging geometric/contact behavior — but note that even with frame access the
human's at-a-glance motion perception still caught modes the agent missed. So
for physical-sim work, keep a human (or a deliberate frame-by-frame pass) in the
verification loop, and don't let the numbers be the only eyes.

## 24. Compliant/underactuated close flips the drone — passive compliance wins on a flying base

Per the grasping literature (Yale OpenHand / SDM hand, concepts/13): adaptation
to object position belongs in the MECHANISM, not the controller. Implemented it
— `close_gripper(compliant=True)`: constant inward torque per joint + damping,
no target pose, so fingers conform on contact instead of servoing to a fixed
shape that shoves an off-center ball out.

**Result: it pitched the body to ~90° (flipped).** The sustained finger torques
react on the airframe (§09/§15 actuator-disturbance) — a position-PD close
reaches its target and stops applying torque; a *constant*-torque tendon never
does. A real Yale hand sits on a fixed arm that absorbs the reaction; a drone
has nothing to absorb it. Fixed-base isolation (the §09 discipline) was
inconclusive — the throwaway harness couldn't reliably seat the ball, of a piece
with ~10 grasp experiments this session that gave noisy/contradictory results.

**Transferable conclusion:** on a flying catcher, **passive structural
compliance (Fin Ray, TPU) beats active underactuation (tendon)** — it conforms
with zero actuation torque, hence zero body reaction, while a tendon hand's
closing torque fights the flight controller. The compliant-close code stays as
an opt-in (default off; the scoop catch is unaffected) but is NOT validated.

Honest state of the grasp: the robust-enclosure-under-uncertainty sub-problem
needs a *reliable* test harness (deterministic ball seating, a real caged metric
via contact normals) + a systematic study — not more quick experiments. The
validated fallback remains the soft-constraint compliant capture (96/96).

## 25. Caging robustness under position uncertainty: a trustworthy harness says the current close already wins (and compliance/FF do not help)

> **⚠️ RETRACTED IN PART — read §26 first.** The off-center conclusions below
> ("gap is the failure mode," the strategy ranking, "compliance doesn't help /
> soft fails") were a **timestep + rigid-contact numerical artifact**. At
> converged numerics (compliant contact pads + 1/960) the close robustly cages to
> ~3.5 cm in ALL directions and strategy makes no difference. The harness
> scaffolding, the self-validated extremes, the tendon-ill-conditioning, and the
> Phase-2 FF result stand; the off-center *rankings* do not.

§24 ended by demanding a *reliable* harness for the robust-enclosure-under-
uncertainty sub-problem, because ~10 quick grasp experiments gave noisy /
contradictory results (the "caged" signal was distance + fingers-touching, and
the ball seating was non-deterministic). Built one (`tests/cage_harness.py`) and
ran the study. Several results overturn the intuitions the noisy experiments had
suggested.

**The harness (Phase 0, the gate).** Fixed-base gripper, arm held rigid in the
catch pose, gravity OFF during the close, ball placed at a controlled
(offset, direction) — fully deterministic. The "caged" metric is NOT distance +
touching; it is a real **form-closure** test: after the close, `saveState`, then
fire a battery of 26 disturbance accelerations (the {-1,0,1}^3 sphere) at ~2.5 g
each, re-applied from the saved state, and count how many the ball survives
trapped within the finger envelope. robustness score = survived / 26.
Self-validation (mandatory, all PASS): determinism (same config 3x -> identical
score), positive control (centered + current close -> 26/26), negative control
(ball 8 cm outside -> 0/26, clean separation: caged ball moves 0.1 cm under
2.5 g, escaped ball >150 cm).

**Phase 1 result — nothing beats the current 4-finger splayed fixed-pose close.**
Sweeping offset {0,1.5,2.5,3.5 cm} x direction {toward-finger, toward-gap} x
strategy {fixed, compliant, soft} x fingers {4,6,8} x ready {splayed, curled}:
- The current close survives a ball offset **3.5 cm toward a finger** (score ~1.0)
  but fails **toward a finger GAP at even 1.5 cm** — the ball slips *between*
  fingers into the gap and is shoved out. This gap-direction weakness is the real
  failure mode, and it is **geometric coverage**, not close compliance.
- **Compliance does not WIN, but it is not a flat negative either (re-examined).**
  First pass: `compliant` (force-limited position to the cage pose) scored *worse*
  off-center than rigid (0.25 vs 0.48 mean at offset>=2.5 cm) and `soft` (soft-PD
  spring) scored **0.00 everywhere** (too soft to resist 2.5 g). But both servo to
  the FIXED pose, so they can't adapt the finger SHAPE — they under-test
  underactuation. A proper **underactuated/differential** model (`under`: low
  force toward a DEEP curl, each joint stalling on contact while the rest curl
  further) **does help the failure mode** — gap-2.5 cm scores **0.50 vs fixed's
  0.00** — but no setting beats fixed overall (aggressive enough to help the gap
  *ejects* centered/finger balls in the gravity-off isolation; gentle settings
  hold centered but lose finger robustness). Caveat: the gravity-off isolation
  (mandatory — the down-opening cup drops a ball under gravity before the close)
  is biased against an aggressive under-tuck; a *dynamic* catch (ball entering the
  cup with downward momentum) would seat it. So the compliance question is *not
  won* on the static metric but is plausibly under-credited by it — the fair test
  is the moving catch. See §25 detail below.
- **More fingers (6,8) trade gap-coverage for finger-direction robustness** with
  no net gain *at the un-retuned close pose* (the cage pose (0.5,1.0,1.3) is
  tuned for 4). Closing the gaps properly needs a close-pose re-optimisation per
  finger count — which the harness now makes tractable.
- **Splayed ready beats partly-curled** uniformly (a curled start doesn't open
  the mouth wide enough to receive, so it often fails to cage even centered).
- A renders-not-metrics check confirmed the mechanism: the fixed close wraps the
  proximal to the equator and tucks middle+distal under (validated cage);
  off-center toward a gap, the same fixed shape paddles the ball out the gap.

So the honest answer to "find a config that clearly beats the current close
off-center" is: **none of the obvious levers WIN on this static metric** — but
underactuation is the most promising and is plausibly under-credited by the
gravity-off isolation (it measurably helps the gap; it loses only because the
under-tuck ejects upward with nothing to seat the ball). The current close is at
the geometric ceiling for a 4-finger ring; the residual gap-direction slip needs
either a denser ring with a re-tuned close pose, or the underactuated close tested
on the *dynamic* catch where gravity/incoming-momentum seats the ball.

**A numerical caveat worth recording:** a *constant joint torque* close ("tendon",
`close_gripper(compliant=True)`) is **numerically ill-conditioned** on this near-
massless 3-link finger chain in PyBullet — a Coulomb-friction-like joint
threshold (small torques produce zero motion until ~1 N.m), sign-flips, and
frozen distal joints. It neither reproduces the cage shape nor gives repeatable
results, and on a floating base it flips the body (the §24 flip). Force-limited
*position* control toward the cage pose is the robust, behaviourally-faithful
stand-in for yield-on-contact compliance.

**Phase 2 — finger-reaction feedforward (the user's hypothesis): a clean
negative.** Implemented `Drone.finger_reaction_ff` (additive, default OFF): pre-
cancel the net body torque from the finger-joint motor torques, the same idea as
`arm_reaction_ff` for the arm sweep (`_finger_reaction_ff_body_torque`). Tested on
a hovering drone (`tests/cage_drone_close.py`). The FF **does not work as hoped**,
and the measurement says why: in the arm-straight-down catch pose the symmetric
finger ring's motor torques **sum to ~0** (the FF predicts ~0), while the *actual*
body disturbance during a close (~0.35 rad/s of pitch in one step) comes from the
**asymmetric finger-link inertial + contact reactions**, which a motor-torque-sum
model can't see. This matches §09's geometry note (near-zero net by symmetry in
the down pose). The constant-torque close still flips the body (numerics, above)
and the FF can't rescue a numerical instability. The Phase-1 *winning* close
(rigid position) needs no FF: on the level-holding thrust-vectoring drone it holds
body pitch to **2.0 deg < 5 deg** during the close (the underactuated drone takes
~7 deg and recovers). The FF stays in as opt-in/default-off (harmless; existing
tests re-verified unchanged).

**Honest gap remaining:** a full end-to-end *retained* catch on the TV drone was
NOT achieved — but the blocker is the pre-existing TV arm-tracking station-keeping
instability (rapid per-tick IK arm slews drive the TV body up into the ceiling;
the repo's TV catch is WIP, §20), not the close strategy. The winning close +
sub-5-deg body pitch on the TV drone are confirmed; the underactuated scoop
(`elbow_catch_solo`) remains the validated retained catch.

## 26. CORRECTION: the §25 off-center findings were a timestep + rigid-contact ARTIFACT (the harness wasn't trustworthy where it mattered)

While investigating a video-smoothness question (sampling the close at a finer
rate), I ran the harness at a finer simulation timestep — and the central §25
finding evaporated. This is the most important entry in this file: **the metric
that §25 trusted was numerically untrustworthy precisely in the off-center band
it was used to study.**

**What broke.** A 65 g rigid ball held by light (~3-4 g/segment, inertia
~3e-6 kg·m²) RIGID fingers, pressed continuously by a PD close in zero gravity, is
an ill-conditioned contact problem — the large ball/finger mass ratio across a
STIFF rigid contact. (The 3-4 g finger mass is realistic, NOT the bug: it matches
a lightweight FDM print / hollow-rib TPU Fin-Ray; a solid print would be ~2-3x
heavier. And tested — scaling finger mass up x3..x100 does NOT fix the artifact,
it caged WORSE; the RIGID CONTACT is the culprit, fixed by compliant pads, which
real fingers have.) At the project's 1/240 timestep the "is the off-center ball
caged or paddled out" verdict is **timestep-fragile**:
- `fixed` gap-3.5 cm: nf=0 at 1/240, **nf=4 at 1/480 and 1/960**, nf=0 at 1/1920
  — non-monotonic; the capture-vs-paddle-out event flips with the step.
- even the "robust" finger-3.5 cm direction fails at very fine steps with rigid
  contact (nf=0 at 1/3840).
- the CENTERED control is rock-stable (nf=4, <0.3 cm across 1/240→1/7680) and the
  8-cm-outside control always escapes — which is exactly why the §0
  self-validation passed: **it only exercised the two stable extremes, not the
  fragile off-center band.** A passing self-test did not certify the off-center
  scores.

**The fix (and it is more physical).** Give the fingers + ball **compliant
contact pads** (`contactStiffness=1e4`, `contactDamping=3e2` — real caging fingers
have foam/rubber) AND a finer substep (1/960). With both, the verdict **CONVERGES
(substep 4 == substep 8)** and the negative control still escapes. This is now the
harness default (`SUBSTEP`, `CONTACT_*` in `tests/cage_harness.py`; `--substep`
to inspect the fragility).

**The corrected, trustworthy result** (full 26-direction battery, converged):
- The current 4-finger fixed close **robustly cages off-center balls to 3.5 cm in
  ALL directions** (gap-2.5, gap-3.5, finger-3.5 all 1.00; centered 1.00; 8 cm
  outside 0.00).
- The real **capture limit is ~4.5 cm** — finger direction holds to ~5 cm, gap to
  ~4 cm (a *small, real* ~1 cm directional difference, not the 1.5 cm "gap fails"
  of the artifact). Beyond ~4.5 cm the ball is outside the basket.
- **Strategy makes no meaningful difference**: fixed / compliant / soft / under
  ALL cage to 3.5 cm (even `soft`, which scored 0.00 everywhere under rigid
  contact, is now ~1.0 — its "too weak / grab-then-release limit cycle" was the
  rigid-contact artifact too) and ALL fail past the ~4.5 cm geometric limit. No
  strategy extends the capture radius.

**So nearly every §25 off-center conclusion is RETRACTED:** "gap is the failure
mode," the strategy ranking, "compliance doesn't help / soft fails," "splayed vs
curled," and the §26-in-§25 underactuation nuance were all reading numerical
noise. What SURVIVES from §25: the harness scaffolding and the *self-validated
extremes* (centered cages; far-outside escapes); the constant-torque "tendon"
close is genuinely ill-conditioned (separate issue); and the Phase-2 finger-
reaction-FF result (it lives on the floating drone, a different sim, and is
unaffected by this contact metric).

**The transferable lesson (the real one):** a deterministic, self-validating
harness can still be *untrustworthy* if the self-validation only covers the easy
extremes while the regime you actually study sits on an ill-conditioned knife
edge. Vary the **timestep** (and contact model) as a convergence check on any
contact-rich result before believing it — determinism is not convergence. This is
the §23 "scalar metrics hide failure modes — you have to LOOK" lesson, one level
deeper: you also have to check the numerics converge in the regime of interest.

## 27. A FAITHFUL Yale-OpenHand underactuated hand: the coupling is real, but in sim it does not beat the rigid close

The `under` strategy (§25/§26) was a per-joint deep-curl stand-in — it had no
COUPLING, the defining feature of a Yale hand. Built the real mechanism
(`src/yale_hand.py`), a numerically-stable POSITION-based tendon:
- **inter-finger whiffletree**: one actuator displacement = the MEAN of the
  per-finger tendon travels; a finger that contacts early caps its travel and the
  freed budget feeds the free fingers (they close MORE) — self-distribution;
- **intra-finger tendon**: a finger's flexion budget is shared distal-biased
  across its 3 joints, and a contacting joint hands its share to the joints below
  (wrap-and-tuck);
- **compliant joints**: a soft position servo that yields on contact; contacting
  joints maintain tendon TENSION (keep pulling toward the cap) so the grip holds.

**Self-distribution VERIFIED (the gate before any scoring).** With a pinned ball
(isolating the coupling from the gravity-off ejection), the per-finger total
flexions come out UNEQUAL for an off-center ball and ~equal for a centered one:
- centered: [2.85, 2.88, 3.00, 2.41] (spread 0.6, ~equal);
- 3.5 cm toward finger 0: **[-0.2, 3.14, 3.14, 3.18]** (spread 3.4 — the near
  finger stalls at the ball, the far three wrap further);
- 3.5 cm toward a gap: [2.15, 1.44, 2.92, 2.98] (the two fingers by the gap close
  less). The whiffletree differential is real, driven by the live contact.

**Static harness (corrected numerics): Yale LOSES to the rigid close.** Centered
0.62 vs 1.00; every off-center cell 0.00. This is the §26 anti-tuck bias made
concrete: gravity-OFF, a free off-center ball is pushed away by the first
contacting finger before sustained contact can cap it, so the differential never
engages and the ball ejects. The static metric is the wrong test for this hand —
exactly as flagged.

**Dynamic catch (the fair test): Yale MATCHES the rigid close at the design point,
does NOT beat it.** Reusing the validated scoop (`elbow_catch_solo`) unchanged and
swapping only the close (via the additive `Drone.external_gripper` hook;
`tests/cage_dynamic_catch.py`):
- at nominal both retain (caught+held) — a TIE;
- the Yale hand needs a FIRMER tendon tension (soft_force 0.7) than the rigid
  close (0.5) to hold the ball through the lift — a gentle compliant close
  captures (sub-cm, 3-4 fingers) but the ball works loose. So it is more complex
  AND needs more grip force for the same result;
- across the ball-velocity grid (off-nominal => more off-center seating): rigid
  **2/5**, Yale **1/5** — Yale is marginally worse, and the off-nominal misses are
  dominated by the SCOOP's own tracking fragility (elbow's baseline is ~2/12),
  not the hand.

**Honest conclusion.** The coupling works and is verified; but in this PyBullet
sim the simple rigid close is already good enough and firmer, so the faithful
Yale hand does not beat it (it ties at nominal, costs more force + complexity, and
the gravity-off static metric is actively biased against it). The Yale hand's real
advantage — adaptation to the position/shape/sensing uncertainty that ALWAYS
exists on real hardware — is precisely what this sim does not model (we inject
only clean offsets, and rigid contact). So this is the expected "no sim benefit;
the benefit is for hardware we don't model" outcome. The model + the
external-gripper hook are committed (opt-in, default off) for the day there is a
hardware testbed or a richer uncertainty model to exercise them.

## 28. Hold-QUALITY metrics (iteration 2): the binary "caged" tied the strategies; quality separates them — but only where convergence allows

§25–27 scored caging with a BINARY form-closure battery ("survives 26 directions
at 2.5 g → caged"). That metric over-credits precarious holds: a ball pinned by
one off-center finger scores the same as a deep symmetric wrap (the iteration-1
miss). Iteration 2 adds CONTINUOUS hold-QUALITY metrics to `tests/cage_harness.py`
(additive/opt-in; the binary `--grid` path is unchanged) and re-scores every
strategy on them, convergence-checking every contact-rich number. The headline:
**quality DOES separate strategies the binary metric tied — but the separation is
real only in the narrow regime where the numbers converge, and the convergence
gate caught our own most-exciting result as a knife-edge before it shipped.**

### The metrics (`--quality`, `--quality-grid`)
- **escape-margin** — min disturbance accel over ALL 26 directions that dislodges
  the ball (bisected per direction; m/s² and g). A continuous margin, not pass/fail
  at a fixed g. Keeps the binary battery as one input (score = #dirs surviving
  2.5 g, derived from the same sweep).
- **pull-in** = injected_offset − residual centering-err. How much the close
  DRAGGED the ball toward the cup center. >0 = re-centered; ~0 = held where it
  landed; <0 = pushed out. THE axis an adaptive/compliant close can win on (a
  fixed close's centering-err just re-reports its input).
- **rattle@2 g** — worst residual displacement under a fixed SUB-dislodging pulse.
  A graded companion INSIDE the caged band, where escape-margin saturates.
- **centering-err**, **# contact fingers** (real `getContactPoints`), **contact
  symmetry** = 1 − |R_xy|, the azimuthal resultant of the unit ball→contact
  directions (1 = surrounded, 0 = one-sided). Azimuthal, not 3D, because the
  down-opening cup always has a −z bias that would swamp lateral one-sidedness.

### escape-margin is BIMODAL in this static sim (an honest limit, not a bug)
A caged ball saturates the 10 g search cap in every direction; a missed ball
collapses to ~0.16 g. So escape-margin robustly CONFIRMS binary caging but does
NOT finely grade precariousness within the caged band. The GRADED quality signals
are centering-err + symmetry + contact-count + pull-in. (This matches §26: at
converged numerics everything within ~4 cm cages.)

### FIXED close — the convergence-backed baseline
Converged (substep 2/4/8, contact ±3×, seed all agree): EM 10 g everywhere,
score 1.00 everywhere — a **reliable trap** to the ~4 cm geometric limit. But it
**pins, it does not seat**: pull-in hovers near 0 (grid −0.4..+0.35 cm; converge
cell +0.03..+1.10 cm), centering-err ≈ injected offset, and **symmetry degrades
with offset** (1.00 centered → 0.43–0.55 at 3.5 cm). Frames:
`docs/cage_frames/iter2/cageQ_fixed_n4_finger_0mm_seated_under.png` (symmetric
X-wrap, symmetry 1.00) vs `..._gap_35mm_seated_side.png` (one-sided wrap,
symmetry 0.32) vs `..._gap_45mm_disturb_side.png` (fingers close on empty air,
ESCAPED — the ~4.5 cm capture cliff).

### SOFT (Fin-Ray flexure stand-in) — re-centers, but only where it converges
The pull-in axis reveals what the binary tie hid: soft's low-stiffness close
**rolls an off-center ball toward the cup center** while the stiff fixed close
pins it. Verified causally (`--migration`, reviewer-D5): a DENSE per-sim-step
trace shows soft's centering-err declines smoothly 2.50 → ~0.07 cm over ~60 sim
steps (~62 ms, largest single step only 3 % of the drop), then damped-settles at
0.57 cm — a GRADUAL physical roll, NOT a one-step teleport (a coarse first pass
mislabeled it "snap"; the dense trace corrected it). Frames
`docs/cage_frames/iter2/migrate_soft_finger_25mm_000pct.png` (ball off to one
side) → `..._010pct.png` (centered, symmetric wrap); fixed stays put over the
same window.

**Win vs null, rendered (so the narrowness is visible, not just tabular):**
- WIN — n4-3.5 cm-finger (the cleanest convergent cell): migration drop soft
  **+2.64 cm** vs fixed **+0.64 cm** (both gradual ~60 ms rolls) — soft re-centers
  ~4× more. Seated frame `cageQ_soft_n4_finger_35mm_seated_under.png` (ball near
  center, CE 1.04 cm) vs fixed `cageQ_fixed_n4_gap_35mm_seated_side.png` (pinned
  off-center, CE 3.68 cm, symmetry 0.32).
- CLEAN NULL — n4-2.5 cm-**gap**: migration drop soft **+0.03 cm**, fixed
  **+0.02 cm** — NEITHER re-centers (both hold ~2.1–2.4 cm off-center). Frames
  `migrate_soft_gap_25mm_*` ≈ `migrate_fixed_gap_25mm_*`. This is the visible
  proof the advantage is direction-specific.
- SUBTLE NULL — n6-2.5 cm-finger: at the NOMINAL substep-4 numerics the migration
  shows soft re-centering **+2.49 cm** vs fixed **+0.35 cm** — it LOOKS like a win.
  But the paired-delta across perturbations straddles 0 (−1.45..+2.17 cm), so the
  apparent advantage is NOT robust. This is itself the lesson: **a single-timestep
  frame can look like a win the convergence gate rejects** — the exact §26 trap,
  which is why the paired/perturbed delta, not one rendered run, decides the verb.

**But the advantage is convergent only in a narrow regime** (the whole point of
the iteration-2 convergence gate). The PAIRED delta (soft.pull_in − fixed.pull_in
at the SAME offset/dir/n/perturbation, 8 perturbations each):
- n4-2.5 cm-finger: **+0.31..+2.17 cm → CONVERGENT POSITIVE** (earned)
- n4-3.5 cm-finger: **+0.91..+2.24 cm → CONVERGENT POSITIVE** (earned; sign also
  robustly positive here, +1.11..+3.48 cm — the cleanest cell)
- n6-2.5 cm-finger: −1.45..+2.17 cm → OVERLAPS 0 (not separable)
- n8-2.5 cm-finger: −2.06..+2.39 cm → OVERLAPS 0
- n4-2.5 cm-**gap**: −0.31..+0.95 cm → OVERLAPS 0 (no re-centering in the gap dir;
  and soft holds WEAKLY there — soft-4-3.5 cm-gap converges as EM ~2.2–3.0 g,
  rattle high, vs fixed's 10 g).
Soft's pull-in SIGN is itself timestep-unstable except at n4-3.5 cm-finger
(n4-1.5 cm-finger sign −2.51..+0.46 = NOT stable; n6, n8 NOT stable), and soft's
ESCAPE-MARGIN is a knife-edge nearly everywhere (soft-4-2.5 cm-finger
CONVERGED=NO: EM swings 2.5/10/7.97 g across substep+seed — **exactly the §26
artifact, caught by the gate this time instead of shipped**). The n4-1.5 cm
sign-instability is reported as an OBSERVATION, not a theory: at a small offset the
re-centering distance is within the timestep/seed noise, so no stable sign appears
— the effect is only legible at offset ≥2.5 cm in our data; we do not claim a
mechanism for that threshold. So the earned claim is narrow: *soft re-centers more
than fixed ONLY at low finger-count (n=4), finger direction, offset ≥2.5 cm;
elsewhere the advantage is not convergently separable and soft's escape-margin is
not a trustworthy number.*

### YALE (faithful underactuated hand) — convergently ejects, but it's the REGIME
Yale convergently EJECTS the off-center free ball (yale-4-2.5 cm-finger
CONVERGED=YES: EM 0.16 g, pull-in −34..−103 cm, 0 contact fingers, score 0, every
perturbation). Centered it does NOT eject (stays, centering-err 0.64 cm) but holds
precariously (EM 1.72 g, rattle 4 cm). Frame
`docs/cage_frames/iter2/cageQ_yale_n4_finger_25mm_seated_side.png` (fingers fully
curled, NO ball). **This is a TESTBED-REGIME limitation, NOT a verdict on the
mechanism** (D6): this sim is gravity-OFF, free/unconstrained, lightweight-ball,
static — precisely the regime that structurally disadvantages an underactuated
tendon hand (the first finger to contact an off-center free ball shoves it out
before the whiffletree differential can cap and engage; centered, first contacts
are symmetric so it stays). The regime that WOULD let Yale show its benefit —
gravity-ON / momentum-seated (ball pressed INTO the cup) / constrained object /
sensing-shape uncertainty — is deferred to the Goal-2 dynamic test (and §27's
dynamic result already had Yale TIE the rigid close there). Do not conclude
against Yale on this sim.

### The fixed-vs-Yale (and soft) answer — does quality change the verdict?
Iteration 1 found a binary "tie." Quality does NOT rescue Yale (it's convergently
worse ON THIS STATIC TESTBED — but that's the regime, deferred). Quality DOES
reveal a distinction the binary hid — the passive SOFT flexure biases the ball
toward center — but the convergence gate then NARROWS that to n=4 / finger /
≥2.5 cm and flags soft's escape-margin as untrustworthy. **Net: no single strategy
is a clean winner that survives convergence. Fixed is the reliable-but-unseating
baseline; soft seats better only in a narrow convergent corner; Yale is deferred.**
That "no clean winner, and here is exactly where each claim is / isn't trustworthy"
IS the iteration-2 result: the convergence gate caught the knife-edge iteration 1
would have shipped as a headline.

### Convergence gate (`--converge`, `--boundary`) and the tooling
Every contact-rich number is checked across timestep (substep 2/4/8), contact
model (stiffness/damping ±3×), and seed (sub-mm ball jitter). `--converge` prints
the per-variation table + an EM-convergence verdict + a pull-in SIGN verdict;
`--paired` runs the soft-vs-fixed PAIRED delta per perturbation (same seed → same
jitter → fair pairing) and rules CONVERGENT-POSITIVE / OVERLAPS-0; `--boundary`
scans the caged→escaped cliff across substeps and flags any timestep-unstable
offset (the §26 band). `--migration` is the causal roll-vs-snap trace;
`--quality-frames` renders the 3-angle (diag/under/side) × 3-moment
(close/seated/post-disturbance) HUD triptychs. Canonical run logs live in
`docs/cage_frames/iter2/logs/` (trust the `*.out` stdout, not the tee'd `*.txt`).

### What I did NOT test (iteration-2 scope was the static quality metric)
- **Gravity-ON / dynamic / momentum-seated capture** — the regime that would give
  Yale (and arguably soft's roll-in) a fair test. Deferred to Goal 2.
- **Non-spherical / deformable objects, real sensing/shape uncertainty** — the
  uncertainty adaptive hands exist to absorb; this sim injects only clean offsets.
- **On-drone (floating-base) quality** — this is the fixed-base harness; the
  finger-reaction on a flying base is §25/concepts-09, not re-tested here.
- **Ready-pose × finger-count interactions at quality resolution**, and
  compliant-strategy convergence beyond spot cells (compliant tracked between
  fixed and soft on the grid; not exhaustively convergence-gated).
- **The escape-margin cap (10 g)** hides how robust the very-robust holds are —
  fine for grading precariousness (the point), not for ranking rock-solid holds.
