# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

PyBullet sandbox for prototyping a two-drone "play catch + arm pickup" indoor scenario. Pure Python, no ROS, no Gazebo. Intended for control / planning prototyping. We've moved well past the v1 "fixed gripper offset" toy and now have a full 2-link arm, cascaded attitude controller with feedforward, decomposed bowling-style throw, and a working end-to-end demo (throw → catch → cube pickup).

## Environment

Always use the `robots` conda env. Do not `pip install` against system Python.

```bash
conda activate robots
python src/main.py             # full demo with GUI
python src/main.py --headless  # no viewer; CI/sanity
python src/main.py --headless --duration 22 --runs-dir runs/m4
```

`src/main.py` imports siblings as top-level modules (`from world import setup`); run with `src/` as cwd or invoke the file directly.

## Architecture

### Core modules

| File | Role |
|---|---|
| `src/world.py` | PyBullet setup: floor, four walls, ceiling, gravity, 240 Hz timestep. |
| `src/drone.py` | `Drone` dataclass: state queries, cascade controller call, force/torque application, arm motor control, EE-aware grasp/release. **Now models real underactuated quadrotor dynamics + 2-link arm.** |
| `src/controller.py` | `CascadeController`: outer position PD → desired thrust vector → inner Lee SO(3) attitude PI(D). Tilt cap, max_thrust/torque. **Has integrator on attitude error and accepts feedforward torque.** |
| `src/ball.py` | Ball spawn, ballistic prediction (`predict_landing`). |
| `src/planner.py` | Original grid+Pareto throw planner (matched-t backup). **Largely obsolete** — superseded by `throw.py` + decomposition. Kept for historical/baseline use. |
| `src/throw.py` | Throw decomposition: given a target release_vel + arm length + release angle, computes (drone vx, ω, α). With pitch-correction option. |
| `src/config.py` | `GameConfig` + `ArmConfig`: scene geometry, play areas, cube position, arm motor caps, FF inertia constants. |
| `src/perception.py` | `BallPerception` (stereo-class noise + 50 ms latency, distance-scaled) + `BallEstimator` (alpha-beta filter + latency compensation via ballistic extrapolation). Shared by demo and isolation tests. |
| `src/sim_setup.py` | Shared scaffolding for isolated tests: world, marker bundle, video, logger, tick wrapper, ball-at-EE spawn helper. |
| `assets/make_gripper_urdf.py` | Generator for `quadrotor_gripper.urdf` (quadrotor + 2-link arm + 3 two-segment caging fingers). Tune finger count/length/mount here, regenerate. |
| `src/main.py` | Full demo orchestration: thrower charges + bowls; catcher predicts + soft-catches; cube pickup. Multi-cam video. |

### Quadrotor URDF (`assets/quadrotor.urdf`)

Box base 0.18×0.18×0.04 m + 4 cosmetic prop disks + 2-link arm:

- `shoulder_housing` (fixed) — mounting stub at top of base
- `shoulder_joint` (revolute about body -y) — positive shoulder = forward sweep
- `upper_arm` (cylinder, 0.20 m, ~0.030 kg)
- `elbow_joint` (revolute about body +y) — kept at 0 always (arm always extended; folded-back inverts to inverted-pendulum trap)
- `forearm` (0.20 m, ~0.030 kg)
- `j_ee` (fixed) — attaches `end_effector` to forearm tip
- `end_effector` (small green sphere, ~0.005 kg) — gripper attachment point

Total mass 0.625 kg (drone class hardcodes `MASS = 0.625` — must match URDF).

### Demo flow (`main.py`)

1. **Setup**: world, two drones (thrower + catcher), cube, ball spawned at thrower EE, multi-cam video, noisy ball perception (`BallPerception`).
2. **Plan**: ballistic to (catcher_home, hover_z) with aim-offset compensation. Decompose into (drone_vx, ω, release_α) via `throw.decompose_throw`. Auto-position thrower at the spin-trigger point.
3. **Settle/preposition**: thrower flies to auto-start x; catcher pre-positions at intercept (body L_arm forward of predicted landing so backward-pointing EE is on the intercept).
4. **Throw choreography**: closed-loop carrot cruise (drone_pos as pos target + ramped vel target) → adaptive spin trigger (when `drone_x + vx · sweep_time ≥ release_x`) → arm sweep at ω with 200 ms ramp → release at α=70° → arm brake (vel-mode hold at 0).
5. **Catcher tracking**: see Soft-catch strategy below.
6. **Carry**: catcher flies above cube at hover_z, releases ball.
7. **Descend + pickup**: catcher extends arm down, descends to cube_z + L_arm + 5 cm, grasps cube.
8. **Lift**: catcher elevates with cube.

## Controller stack (built across M1–M4)

The cascaded controller has accumulated several layers — each addresses a specific failure mode we documented. All are toggleable per-drone.

| Layer | Toggle | Purpose | Status |
|---|---|---|---|
| Lee SO(3) attitude inner | always on | body torque from desired R_des | Working; has 180° singularity (avoid yaw=π) |
| Position outer | always on | desired thrust vector from pos+vel error | Working |
| Tilt cap (`max_tilt_deg`) | always on | clip horizontal thrust component | 35° default; bumped to 60° during throw + catch maneuvers |
| Vertical-thrust floor | always on (when tilt < 90°) | drone always pushes up ≥ ½·g | Prevents nose-flip into no-vertical-authority regime |
| **Arm-reaction torque FF** (`arm_reaction_ff`) | per-drone | predict body torque from commanded shoulder ω, pre-cancel | Works. Rate-limited finite difference of commanded ω, predicted τ = I_arm · α, applied as opposite body torque. Has a clamp at motor torque cap. See `Drone._arm_reaction_ff_body_torque`. |
| **Attitude gain scheduling** (`attitude_gain_schedule`) | per-drone | rescale kR_y, kw_y to keep ω_n + ζ constant across arm-pose inertia changes | Works dramatically. Keeps cascade critically damped (ζ≈0.91) regardless of arm angle + held mass. M1b post-settle dropped 33 cm → 0.5 cm with this on. |
| **Body-z translational FF** (`arm_translational_ff_z`) | per-drone | predict body-z disturbance from arm centripetal+tangential, add canceling thrust | Works. F_body_z_dist = −m_eff·(α·sin(θ) + ω²·cos(θ)). Drone holds altitude through sweep instead of dipping. |
| **PI integrator on attitude** (`controller.kI`) | always (default kI=[0.05, 0.05, 0]) | absorb steady-state biases (gravity-on-arm, wind, model error) | Default on, low gain. Helps in compound disturbances but couldn't fix M1b alone (gain scheduling did). Yaw term defaults 0; the finger-gripper catcher sets it (else the gripper's steady yaw throws the EE sideways). |
| **Position integrator** (`controller.kI_pos`) | per-drone (default 0) | null steady-state position offset under a persistent disturbance (COM-offset gripper, unmodeled held mass) | Default OFF (existing tuning unchanged). Finger-gripper catcher turns it on to kill the ~12 cm gripper COM hover sag. Anti-windup clamp `pos_integral_clamp`; needs ~2.5 s to settle. |

What is **NOT** built (open):
- Body-x translational FF (the "drone tilts forward during sweep, redirects arm tip vz to vx" coupling). We discussed it; chose to plan around it via `cruise_speed_for_release` + an empirical `EXPECTED_PITCH_RAD` correction in throw decomposition. The 30 cm aim offset in M3 plan_ballistic absorbs the residual.
- Quaternion-error attitude controller (would fix the 180° singularity properly).
- Disturbance observer (real-time wind / model-error rejection).

## Throw decomposition (`src/throw.py`)

The actual throw: drone provides forward velocity `v_drone`, arm provides vertical + extra horizontal via tip tangent. At release angle α from straight-down:

```
ω · L · sin(α) = vz_target
v_drone + ω · L · cos(α) = vx_target
```

We pick α from config (default π/3 = 60°; bumped to 70° in main demo). Solve for ω and v_drone.

Pitch-correction option (`expected_pitch_rad`): drone tilts forward ~5–10° during sweep; tilt rotates body-frame arm tip velocity in world frame. Pre-rotate target by −α_pitch so body-frame plan compensates. Empirical 7° correction halves residual aim error.

`cruise_speed_for_release(decomp)` returns the cruise speed needed pre-sweep so that, after the sweep's natural translational push (centripetal force integral along the sweep arc), the drone arrives at release with `v_drone_horiz`. Approximates Δvx_during_sweep = −m_eff·ω·cos(α) / m_drone.

## Soft-catch strategy (current state — work-in-progress)

The catcher's job: position so EE is at predicted ball intercept (xy at z=hover_z, with body L_arm forward because EE is L_arm behind body in catch pose). Then absorb ball momentum without a hard constraint snap.

### What's implemented

1. **Pre-positioning during throw choreography**: catcher target = predicted intercept + L_arm offset. By the time ball is released, catcher is already at the catch point.
2. **Ball perception with distance-scaled noise + latency** (`BallPerception`): models stereo-camera-class measurement (pos σ = 0.5 cm + 0.5%·dist, vel σ = 5 cm/s + 6%·dist, latency 50 ms). Catcher reads through `perception.observe(viewer_pos)` instead of god-mode `state(ball)`.
3. **Phased catch**:
   - **Phase A (no soft-catch)**: catcher holds at pre-positioned intercept (zero vel target). Engaged until ball is *committed* (vz < −0.5 AND past the centerline x > 0).
   - **Phase B (soft catch)**: when time-to-intercept ≤ T_LEAD (250 ms), ramp catcher's xy vel target from 0 to ball's measured xy velocity at intercept. Linear ramp → constant accel.
4. **Predicted-xy EWMA smoothing** (α=0.15) once ball-committed gate trips, to suppress per-tick noise jitter that whips the carrot around.
5. **Catcher tilt cap bumped to 60°** for the catch maneuver (matching ball at ~4 m/s xy needs ~14 m/s² → 55° tilt).
6. **Catch trigger**: `ee_to_ball < 0.15 m AND rel_vel < 1.5 m/s` → snap constraint via `catcher.grasp(ball, max_distance=0.15)`.

### Compliant capture (validated in isolation — `tests/arm_catch_solo.py`)

The velocity-matching approach hit a geometric wall: at the matched instant the arm tip's centripetal acceleration (ω²L ≈ 53 m/s², pointing up toward the shoulder) nearly opposes the ball's gravity vector, so the circle-vs-parabola tangency window is ~27 ms for a 1.5 m/s rel-vel gate. The replacement (per the adversarial-game decision: don't depend on the thrower throwing catchable balls) is **compliant capture** — drop the rel-vel gate entirely, trigger geometrically (d < 15 cm), and spread the momentum transfer:

1. **Absorption sweep** (reduces rel-vel at contact): shoulder ramps to ω over a window sized T = 2·Δθ/ω so it lands on the velocity-matched angle (tip tangent ∥ ball velocity) exactly at intercept.
2. **`soft_grasp`** (`drone.py`): point-to-point constraint capped at 8 N — ball decelerates over ~60–80 ms / ~10 cm instead of one rigid solver step. Stands in for foam pad + compliant fingers.
3. **Back-drivable shoulder**: `spin_arm(..., torque_cap=0.3)` during absorption so the joint yields under ball load.
4. **Two-stage lock**: at rel_vel < 0.3, `firm_grasp()` stiffens the constraint and the shoulder brakes to ω=0 in velocity mode.

Validated 12/12 over the adversarial envelope (arrival speeds 3.2–7.1 m/s, descent 20–61°; `--grid`), contact rel-vel up to 4.6 m/s, peak constraint force ≤ 11.3 N (logged via `grasp_force()`). See `docs/iteration_findings.md` §11 for the failure modes found en route.

**M5b — noise + positioning (also validated)**: the same test passes with stereo-class sensing noise + 50 ms latency, wind gusts, pre-position error (`--noise`), and with intercepts the ball is NOT aimed at — lateral offsets to 1 m, crossing balls ±0.8 m/s, depth offsets ±0.3 m (`--grid-pos`). **96/96** across all four grids (3 seeds/noisy cell). The three load-bearing pieces: `BallEstimator` latency compensation (acting on raw delayed measurements costs 23 cm at nominal speeds — estimate error at contact is 0.2–0.7 cm after), catcher-local stiffer position gains (kp [12,12,14], kd [7,7,7] → ωn≈3.5, ζ≈1.0 — defaults lag 15–20 cm on 1 m repositions inside one ball flight), and compliance absorbing the residual. Decisions read only the estimate, never truth. See `docs/iteration_findings.md` §12, including why velocity-target carrots are the wrong fix (they're gain changes in disguise) and why the elbow can't help with lateral misses (both joints rotate about y).

### What's NOT yet working

- **Integration into `main.py`**: the demo still uses the rigid `grasp` + 1.5 m/s rel-vel gate and does NOT currently catch (closest approach ~13 cm at rel-vel ~5 m/s). Port the compliant capture + sized sweep window from `arm_catch_solo.py` into the demo's phased catch. Keep the perception commitment gate (descending + past midline) — the isolation test dropped it because its launch is ground truth.
- **3-finger gripper**: still the eventual hardware-honest mechanism (the soft constraint is its behavioral stand-in). URDF needs 3 revolute finger joints driven by single "close" command; catch detection becomes contact-force-based instead of distance-based.

## Multi-cam video

`VideoRecorder` in `main.py` renders 4 viewpoints per frame and concatenates as 2×2 grid (1280×960 total; each cell 640×480):
- TL: side spectator view (static)
- TR: thrower POV (camera mounted on thrower body, looking +x)
- BL: catcher POV (looking -x toward incoming ball)
- BR: ball-follow (camera trails ball at -y offset)

Playback speed: 0.5× (slow-mo, set in `VideoRecorder.__init__`).

## Play area geometry (current `main.py` overrides)

- **Room**: 10 m × 10 m × 3 m (walls at ±5)
- **Thrower**: home (-2, 0, 1.5), play x ∈ [-3.0, -0.5], y ∈ [-1.0, +1.0], z ∈ [0.8, 2.6] (2.5 m wide)
- **Catcher**: home (+2, 0, 1.5), play x ∈ [+1.0, +3.0], y ∈ [-1.0, +1.0], z ∈ [0.4, 2.6] (z down to 0.4 so extended arm reaches cube)
- **Gap**: x ∈ [-0.5, +1.0] (1.5 m of "no-fly" zone for the ball to travel through)
- **Cube**: (1.5, -0.7, 0.05) — inside catcher's play area

## Engineering log

Living docs covering specific iterations:

- `docs/throw_planning.md` — ballistic math, planner algorithm, matched-t single ramp insight (largely historical now).
- `docs/iteration_findings.md` — Lee SO(3) singularity, paper estimates off by integer multiples, choreography tricks, marker palette.
- `docs/arm_v1_status.md` — where the 2-link arm work *was* (mid-development snapshot). Largely superseded by what's described in this CLAUDE.md, but useful for understanding why specific things were built.
- `docs/concepts/` — **learning companion** (a standing project objective: accrue transferable robotics/estimation/control knowledge). One short note per concept we use: what it is, where it lives in this codebase, what our experiments showed, what transfers to larger projects. Add a note whenever a new concept enters the work; keep the engineering narrative in iteration_findings.md and the conceptual reference here.

Subsystem isolation tests (validated foundations):

- `tests/arm_hover_spin.py` — M1 + M1b: drone hovers, arm sweeps -π/2 → +π/2. With FF + gain scheduling, passes both with-ball and without-ball variants.
- `tests/arm_cruise_spin.py` — M2 + M2.1 + M2.1b: drone cruises forward, arm sweeps mid-flight. Tight choreography (sweep starts during accel, no wait for cruise to settle) outperforms the settled version.
- `tests/throw_solo.py` — M3: solo throw to a target landing. Adaptive spin trigger + closed-loop cruise + pitch correction + 30 cm aim offset → throws land within 5 cm across 3.5–6.5 m range.
- `tests/finger_catch_solo.py` — M6: **feasibility probe** for a physical caging-finger catch (no constraint). Cages a ball placed in the cup; the in-flight catch is not yet reliable (~7–10 cm rendezvous miss). Not a PASS/FAIL gate — it's the experiment documenting why contact catching needs the elbow. `--grid`, `--vx/--vz`. See iteration_findings §13.
- `tests/arm_catch_solo.py` — M5/M5b: compliant capture under realism. Ball launched to arrive at a chosen intercept with chosen velocity; absorption sweep + soft constraint + back-drivable shoulder + two-stage lock. `--grid` (velocity envelope), `--grid-pos` (offset/crossing intercepts the catcher must fly to), `--noise` (sensing+latency+estimation+gusts+pre-position error), `--seeds N`. All four grid combinations pass 96/96. Single point: `--vx/--vz/--vy/--ox/--oy/--seed`.

## Open design questions / parking lot

1. **Integrate compliant capture into `main.py`** (next priority). The mechanism is validated in isolation (M5, see Soft-catch section); the demo still runs the old rigid grasp + rel-vel gate and doesn't catch. Port: soft_grasp trigger (geometric only), sized sweep window, back-drivable shoulder, two-stage lock — while keeping the perception commitment gate.
2. **3-finger caging gripper (M6) — built and probed; blocked on 2-DOF rendezvous.** `assets/make_gripper_urdf.py` + the `Drone` finger API + `tests/finger_catch_solo.py` exist and work as a *mechanism* (cages a ball placed in the cup). The in-flight catch does NOT yet succeed: after fixing a cascade of platform issues (finger-motor yaw-singularity excitation, gripper COM/yaw steady offsets needing integrators, model-mass, sweep-lag from doubled arm inertia, cup-depth targeting), the dynamic closest approach plateaus at ~7–10 cm of cup-to-ball miss, ~speed-independent. Root cause: a single shoulder DOF sweeps the cup through an arc and can't reliably land on the ball at the intercept instant. See `docs/iteration_findings.md` §13 and `docs/concepts/09`. **This is the critical-path motivation for #3.**
3. **Unlock the elbow for catch-time tracking** (now critical path for the finger catch, not just nice-to-have). 2-DOF arm lets the EE servo to a *point* and track it for ~250 ms instead of sweeping a 1-DOF arc through it — converting the knife-edge rendezvous-timing problem (#2) into a tracking problem, and widening the catchable approach-direction envelope. Needs 2-link IK on a moving base + FF/gain-schedule extension to elbow angle. Keep elbow range limited (~[0°, 100°]) to stay out of the inverted-pendulum trap.
4. **Catcher facing the thrower / yaw=π**. Current geometry only works because catcher faces world +x while ball comes from -x — the EE backward-pointing pose happens to align. For corner balls / general direction, we'd need yaw control + a singularity-free attitude controller. Quaternion-error formulation is the standard fix.
5. **Turn-by-turn rally game**. Discussed. Mechanically: after catch, swap roles, catcher (now thrower) plans throw back. Needs role-symmetric arm choreography + arm-swing-back as the role-switch (instead of yaw rotation, which hits the singularity).
6. **Adversarial / cooperative game objectives**. Longest rally vs. beat-your-opponent. The latter is a planning problem (throw to opponent's reachable-area edge); the former is cooperation around accuracy.
7. **Sim2real gap**. PyBullet's contact model is rigid; air drag is constant linear damping (no Re-dependent drag). Real drones have battery-state thrust falloff, motor delay, sensor noise, gimbal latency. Honest port to hardware would need PX4 SITL via Gazebo+ROS2.
8. **Vision-based ball perception**. Currently god-mode + Gaussian noise + latency. A real version would render stereo from catcher's POV and run actual stereo + detection + filtering. Big jump in realism but probably right answer is to keep noise-model abstraction and validate with real data when we have it.
9. **Body-x translational FF**. The remaining cascade-fights-recoil coupling that we plan around rather than cancel. The principled fix is FF; the user-preferred path was to plan around it (let drone gain forward velocity from sweep naturally, plan cruise lower so net at release is correct).
10. **Catcher's noisy perception jitter** when ball is far. EWMA smoothing helps; gating by `ball_committed` (vz<−0.5 + past midline) helps more. Could add a Kalman filter for principled best-estimate.

## Tuning gotchas

- `MASS` in `drone.py` and `<mass>` in URDF must agree.
- When carrying via constraint, gravity feedforward must include held mass (`_held_mass()`). The `_system_com_world` thrust application depends on this for translational accuracy.
- Switching motor mode `spin → hold` (`spin_arm` → `extend_arm`/`hold_arm`) generates a 1-step torque kick that FF doesn't track. Always brake to ω=0 in velocity mode and stay there. We learned this the hard way (the "violent jerk at end of arm sweep" episode).
- Cascade gains are tuned for body-only inertia. With held ball + extended arm, system inertia is 6× higher, ζ drops from 0.91 to 0.37 (ringy). Gain scheduling fixes this.
- `set_target` clips to play area. If your throw needs the drone past `play_x_max`, widen the play area or lower the release point.
- Isolation tests run in the DEFAULT room (8 m → walls at ±4); `main.py` overrides to 10 m. Spawn/launch math that assumes ±5 walls puts objects inside a wall — if a test's "closest approach" is meters off, check spawn geometry before blaming the controller.
- Ramped arm choreography covers ∫ω dt = ω_max·T/2, not ω_max·T. Size the window from the rotation needed (T = 2·Δθ/ω_max) and recompute the ramp from time-to-intercept every tick — a one-shot engagement that latches full ω overshoots the target angle.
- Don't "speed up" the position loop via `vel_target` carrots. The outer loop is accel = kp·err + kd·(vtgt−v); vtgt = K·err is a hidden kp increase with no matching kd (ζ collapses, body oscillates), and vtgt = dist/t_remaining caps the cascade at a just-in-time crawl. Retune kp/kd together (per-drone — `controller.kp/kd` are instance fields).
- PyBullet constraint `maxForce` caps each axis independently — an "8 N" soft grasp can apply up to 8·√3 ≈ 13.9 N vector force. Budget the √3 when reasoning about loads.

## Tests / lint

No formal test suite. Verification path:
- Subsystem tests in `tests/` (arm_hover_spin, arm_cruise_spin, throw_solo, arm_catch_solo) print PASS/FAIL; `arm_catch_solo --grid` is the compliant-capture envelope check (must hold 12/12).
- **Known-failing as of 2026-06**: `arm_hover_spin` and `arm_cruise_spin` FAIL (sweep-window drift ~14 cm + post-sweep ringing). Predates the compliant-capture work (verified by A/B-neutralizing the new torque-cap path — identical failure); likely broken by M3/M4-era tuning or the arena resize. Needs a bisect-style look at thresholds vs. behavior.
- Full demo: `python src/main.py --headless --duration 22 --runs-dir runs/m4` then check for `caught ball` and `picked up cube` log lines.
- Multi-cam video at `runs/m4/run_*.mp4` — eyeball the four views.
