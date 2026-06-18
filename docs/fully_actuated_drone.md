# Fully-actuated (tilt-rotor) drone — design & plan

Status: **design / not yet built.** This doc is the plan and the build spec. It
captures why we want it, the specific mechanism (X-frame + radial tilt), the
control math, the simulator caveat, the integration architecture, and the
validation scenarios. Written while the enabling refactor (Drone/Controller
seams) is in flight.

## 1. Motivation — underactuation is the root of the catch pains

A standard quadrotor has **4 inputs** (rotor thrusts) producing **4 controllable
DOF**: total thrust `Fz` plus the 3 body torques. But a rigid body has **6 DOF**.
The missing two are horizontal force: a quad **cannot produce Fx/Fy directly — it
must pitch/roll to tilt its thrust vector**. Nearly every hard problem in the
catch traces back to this one fact:

| Pain | Mechanism | Measured (underactuated) |
|---|---|---|
| **COM sag** | offset gripper makes a steady moment; body tilts to hold against it; tilting steals vertical thrust → it drops | ~0.35 m sag, ±30° pitch transient |
| **Slow lateral tracking** | to move sideways it must pitch *first*, then accelerate | lags ~15–20 cm chasing a 3.3 m/s ball |
| **Arm↔body coupling** | arm reaction pitches the body, and pitch is *also* how it translates, so the two fight | the oscillation of §21 |

A **fully-actuated** drone produces force in any direction and torque
independently, so it **translates without pitching**, **counters the gripper
moment without tilting**, and **decouples position from orientation** — dissolving
all three at once. This is a platform upgrade, not a patch: the parking-lot items
(lateral/corner balls, the rally game) all need this agility.

## 2. The mechanism — X-frame + radial tilt (1 DOF per rotor)

Keep the **existing X/quadrant layout** (props at `(±0.10, ±0.10)`). Add **one
tilt hinge per rotor, oriented radially** — the hinge axis is perpendicular to
the arm from hub to rotor, so the thrust "nods" toward/away from the hub, along
the diagonal.

### Why radial tilt is torque-free
A rotor at `r_i = R·ρ̂_i` (corner position, `ρ̂_i` the outward radial unit vector)
producing a horizontal force `F = h_i·ρ̂_i` makes torque
`r_i × F = R·h_i·(ρ̂_i × ρ̂_i) = 0`. The force is **parallel to its own lever
arm**, so it generates **zero moment — including zero yaw.**

### The allocation decouples into three independent channels
- **Vertical components** `v_i = Tᵢcosβᵢ` → lift + roll + pitch, *exactly* the
  normal X-quad mixing (`Fz = Σv`, `τx`/`τy` from the diagonal `v` differentials).
- **Radial tilts** `h_i = Tᵢsinβᵢ` → `Fx`, `Fy`, touching **nothing else** (no
  torque, by the result above).
- **Yaw** → still the rotor drag-reaction differential, unchanged from a normal
  quad (weak, but we need little).

So the allocator is **closed-form and separable**: solve the vertical mix first
(the controller we already have), then add horizontal force as an independent
step. An X-frame is what buys this; a `+`-frame would mix the axes and lose it.

### Counts and limits
- **8 inputs** (4 thrust + 4 tilt) for **6 DOF** → over-actuated, with freedom to
  spare. Strong authority on `Fx,Fy,Fz,τx,τy`; weak `τz` (same as any quad).
- **Tilt limit caps horizontal force**: `Fx_max = T·sin(β_max)`. At `β_max ≈ 30°`
  that's ~0.5·weight of lateral force → several m/s², plenty for catch
  repositioning. State this as the authority bound.
- Tilting front/back forward drops their vertical component, so they spin up to
  hold `v_i` — which is exactly what keeps `Fx` from disturbing pitch.

## 3. Wash management — the reason X+radial beats `+`-frame

A `+`-frame puts two rotors *on* the catch axis (`y=0`, where the arm sweeps and
the ball falls), so their downwash — and worse, their *steered* downwash — blows
straight down the catch line. The X+radial design keeps the wash off it, via
**three levers**:
- **Baseline column** — quadrant layout puts the static downwash columns at the
  corners, straddling the catch plane (widen the y-offset for more clearance).
- **Steered component** — radial-plane geometry keeps tilt-deflected wash in the
  *diagonal* planes, off the center line.
- **Residual** — `tilt → 0` at contact, so at the catch instant there is no
  steered component near the ball at all.

## 4. Simulator caveat (read this before trusting any "wash" result)

**PyBullet models no propeller aerodynamics** — no downwash, just rigid-body
dynamics + linear drag. Consequences:
- In the current sim, `+`-frame and X+radial are **control-identical** (both give
  the same clean decoupled Fx/Fy). The wash advantage is **invisible**.
- To actually test/exploit the wash design we must **add a downwash disturbance
  model**: each rotor pushes a column of air below it (a force on any object in
  its cone, scaling with thrust, falling off with distance, tilting with the
  rotor). ~half a day; a real sim2real-gap closer. **Deferred** — separate task,
  added on the main tree near the ball/world code, not in the platform agent.

We still build X+radial now (it's the right hardware choice and the existing
layout, at no extra control cost); the wash payoff is validated later if/when we
add the downwash model.

## 5. Architecture & integration

The catch code touches the drone only through a small public API
(`make_solo_drone`, `set_target/step/position/orientation/velocity`, the arm:
`hold_arm/joint_states/gripper_world_position`, the gripper, and
`controller.kp/kd/kI/kI_pos`). The arm/gripper code is **platform-independent**.

Two enabling seams (being refactored now, behavior-preserving):
- `CascadeController.desired_force_world(...)` — the shared position-PD outer loop
  (raw desired world force), called by both the underactuated collapse and the FA
  allocator.
- `Drone._compute_body_wrench() -> (force_world, torque_body)` + `_apply_body_wrench(...)`
  — `step()` becomes compute-wrench → apply-wrench → arm → gripper.

Then:
- **`FullyActuatedDrone(Drone)`** overrides **only** `_compute_body_wrench()`:
  call `desired_force_world(...)`, clamp to the tilt cone, return the force
  vector directly + an **independent** attitude torque (track level, or any
  commanded yaw/attitude — not derived from the thrust direction).
- **Per-drone flag** `make_solo_drone(..., fully_actuated=True)`. The **catcher**
  goes FA; the **thrower stays underactuated** (the bowling throw is tuned and
  fine — nice asymmetry, the catcher is the one that needs agility).
- The underactuation-compensating flags (`arm_reaction_ff`,
  `arm_translational_ff_z`, `attitude_gain_schedule`) **default off** for FA — the
  body no longer pitches from arm reaction, so they're moot.
- Idealized model first (net wrench at CoM, no rotor force-placement); the
  separable closed-form allocator makes this barely more code than a pure wrench,
  so we build the X+radial allocation directly. A realistic version (forces
  applied at rotor positions, gyroscopic terms) is a later fidelity bump.

### What full actuation lets us DELETE
Much of the recent catch complexity exists only to fight underactuation. With a
body that holds level and on-station we can likely strip: the **diagonal
station**, **eventual positioning** (§21), and the **COM feedforward**, and return
to a simple overhead station. Integration is partly a *cleanup*.

### What it does NOT solve
**Cup centering at contact** — the fingers paddling the ball out at the cage rim
(§21b, the finger-cam) is a gripper-geometry / close-timing problem, independent
of the platform. Same work either way.

## 6. Validation — test scenarios

Common harness: both drones load the **real `quadrotor_gripper.urdf`**, arm in the
catch pre-pose; each scenario runs twice (`underactuated` baseline vs
`fully_actuated`) and logs the metric + a side-by-side video. Deterministic, so
no downwash model needed for these (they are pure rigid-body control metrics).

**Tier 0 — allocator unit checks**
- **U1 wrench fidelity** — command test wrenches, measure actual net force/torque. Pass: matches within ~1% (unsaturated).
- **U2 yaw decoupling** — command pure Fx, then Fy. Pass: net `τz ≈ 0` (confirms the torque-free claim).
- **U3 saturation** — ramp Fx past `T·sin(β_max)`. Pass: clamps gracefully (no flip/NaN); report `Fx_max`.

**Tier A — actuation sanity (bare, no arm)**
- **A1 hover hold** — Pass: pos error < 2 cm, level.
- **A2 translate without pitching** — 1 m lateral step. Metric: **peak tilt**. Expect FA < 5° vs underactuated ~20–30°.

**Tier B — drifted-CoG pains (with the gripper arm — the point)**
- **B1 offset-CoM sag** — hold the pre-pose, settle 4 s. Metric: **steady z-sag + peak pitch**. Baseline 0.35 m / ±30°. Pass: FA < 5 cm / < 5°. Run two FA sub-modes (hold-level vs let-it-tilt); report which sags less.
- **B2 lateral reposition with arm** — 1 m step, arm held. Metric: **settle time to ±5 cm + peak pitch**. Expect FA faster, < 5° pitch.
- **B3 arm-sweep coupling** — hold station, sweep the shoulder at catch speed. Metric: **body displacement + pitch excursion**. Pass: FA body within ~3 cm, < 5°.
- **B4 track at ball speed (closest catch proxy)** — command the body to follow a lateral position ramp at **3 m/s for 0.5 s**. Metric: **tracking lag**. Baseline ~0.18 m. Pass: FA < 5 cm. *The single most catch-relevant number.*

**Reporting (the go/no-go artifact):** one table —

| metric | underactuated | fully-actuated |
|---|---|---|
| A2 peak tilt (1 m step) | … | … |
| B1 sag / peak pitch | 0.35 m / ±30° | … |
| B2 settle / peak pitch | … | … |
| B3 body disp / pitch | … | … |
| B4 lag at 3 m/s | ~0.18 m | … |

plus the A2/B1/B3/B4 side-by-side videos and the U1–U3 pass/fail.

**Out of scope for the platform agent:** no catch attempt, no perception/IK/
fingers, no downwash model. It only *adds* `FullyActuatedDrone` + these scenarios
in a **git worktree**, never editing the underactuated path, the throw, or the
catch tests.

## 7. Open decisions

1. **Downwash model** — in the agent's scope, or added here later? Lean: later,
   here (it touches the ball/world, near the catch work).
2. **Parallel catch work** — keep pushing the COM-FF catch on the underactuated
   drone as a baseline, or pause behind the prototype?
3. **B4 as the headline pass/fail**, or weight all scenarios equally?
4. **Promote FA project-wide** (throw + demo) eventually, or keep it catcher-only?

## 8. Learning note (project objective)

This introduces **control allocation for over-actuated systems** — the dual of the
underactuated control we've practiced. The separable closed-form allocator (from
the +-frame/radial geometry) makes it a transparent artifact rather than a
black-box pseudo-inverse. When built, add a concept note
(`docs/concepts/12-actuation-and-control-allocation.md`) on the underactuation ↔
full-actuation spectrum and what each costs in actuators vs control complexity.
