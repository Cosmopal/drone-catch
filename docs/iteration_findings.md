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
