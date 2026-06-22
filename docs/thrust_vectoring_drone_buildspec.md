# Thrust-vectoring (over-actuated) drone — build & validation spec

**This doc is the build plan + test scenarios.** The *concept* (under/over-
actuation, the wrench, control allocation, null space, the quadrant-layout +
radial-tilt reasoning and wash geometry) lives in
[`concepts/12-overactuation-thrust-vectoring-allocation.md`](concepts/12-overactuation-thrust-vectoring-allocation.md);
the *decision record* is `iteration_findings.md §22`; the parking-lot pointer is
CLAUDE.md item #11. Read those first — this doc does not re-derive them, it says
**what to build and how we'll know it works.**

Decisions inherited from §22 (do not re-litigate): one tilt servo per rotor
(**8 inputs vs 6 DoF**, 2-dim null space); **quadrant (X) layout** (existing
URDF); **radial tilt** (zero yaw-torque, wash in the central diagonal planes).
The allocation **replaces the cascade** — command position and attitude
independently, no thrust→attitude inversion, no Lee 180° singularity.

## 1. Status of the enabling refactor (done)

The shared seams a `ThrustVectoringDrone(Drone)` subclass overrides are in place
(commit `233e6fe`, behavior-preserving, verified byte-identical on the catch
tests):
- `CascadeController.desired_force_world(...)` — the position-PD outer loop (raw
  desired world force). The new platform reuses this for the **force** half of
  the wrench.
- `Drone._compute_body_wrench() -> (force_world, torque_body)` and
  `_apply_body_wrench(...)` — `step()` is now `compute-wrench → apply-wrench →
  arm → gripper`. The subclass overrides **only** `_compute_body_wrench()`.

## 2. What to build

1. **URDF**: add one **radial tilt joint per rotor** to a thrust-vectoring
   variant of `quadrotor_gripper.urdf` (keep the quadrant prop positions). The
   joint hinge axis is along the arm (hub→rotor) so thrust nods toward/away from
   the hub.
2. **Per-rotor force application**: apply each rotor's thrust as a vector at its
   rotor position (not a single net wrench at the CoM) — this is what makes the
   tilt physical and is the honest model (§22 / CLAUDE.md #11).
3. **Allocation matrix**: desired wrench `[Fx,Fy,Fz,τx,τy,τz]` → 8 actuator
   commands (4 thrusts + 4 tilts). Use the separable closed form where it holds
   (vertical components → Fz/τx/τy as the current X-mix; radial tilts → Fx/Fy,
   torque-free) and a pseudo-inverse + null-space objective for the rest. The
   null space (keep tilts small / steer wash) is optional for v1.
4. **`ThrustVectoringDrone(Drone)`**: override `_compute_body_wrench()` —
   `desired_force_world(...)` for the force, an independent attitude PD for the
   torque, then the allocator; return the realized `(force_world, torque_body)`
   (or apply per-rotor forces directly and return zero net for `_apply_body_wrench`
   to no-op — implementer's choice, document it).
5. **`make_solo_drone(..., thrust_vectoring=True)`** flag. The **catcher** uses
   it; the **thrower stays underactuated** (the bowling throw is tuned — leave it).
   The underactuation-compensation flags (`arm_reaction_ff`,
   `arm_translational_ff_z`, `attitude_gain_schedule`) default **off** for it.

Optional fast sanity before the full allocator: an idealized net-wrench-at-CoM
mode gives the same *control* result (PyBullet applies any force), useful to
de-risk the controller before the per-rotor URDF work. Not a substitute for #1–3.

## 3. Validation scenarios

Common harness: both drones load the **real gripper URDF**, arm in the catch
pre-pose; each scenario runs twice (`underactuated` baseline vs
`thrust_vectoring`) and logs the metric + a side-by-side video. Deterministic —
no propwash model needed (these are pure rigid-body control metrics; the wash
claim is explicitly **out of scope**, see §4).

**Tier 0 — allocator unit checks**
- **U1 wrench fidelity** — command test wrenches, measure actual net force/torque. Pass: within ~1% (unsaturated).
- **U2 yaw decoupling** — command pure Fx, then Fy. Pass: net `τz ≈ 0` (the radial torque-free claim).
- **U3 saturation** — ramp Fx past `T·sin(β_max)`. Pass: clamps gracefully (no flip/NaN); report `Fx_max`.

**Tier A — actuation sanity (bare, no arm)**
- **A1 hover hold** — Pass: pos error < 2 cm, level.
- **A2 translate without pitching** — 1 m lateral step. Metric **peak tilt**: expect TV < 5° vs underactuated ~20–30°.

**Tier B — drifted-CoG pains (with the gripper arm — the point)**
- **B1 offset-CoM sag** — hold pre-pose, settle 4 s. Metric **steady z-sag + peak pitch**. Baseline 0.35 m / ±30°. Pass: TV < 5 cm / < 5°. Run two sub-modes (hold-level vs let-it-tilt); report which sags less.
- **B2 lateral reposition with arm** — 1 m step, arm held. Metric **settle time to ±5 cm + peak pitch**. Expect TV faster, < 5°.
- **B3 arm-sweep coupling** — hold station, sweep the shoulder at catch speed. Metric **body displacement + pitch excursion**. Pass: TV body within ~3 cm, < 5°.
- **B4 track at ball speed (closest catch proxy)** — command the body to follow a lateral ramp at **3 m/s for 0.5 s**. Metric **tracking lag**. Baseline ~0.18 m. Pass: TV < 5 cm. *The single most catch-relevant number.*

**Go/no-go artifact:**

| metric | underactuated | thrust-vectoring |
|---|---|---|
| A2 peak tilt (1 m step) | ~20–30° | … |
| B1 sag / peak pitch | 0.35 m / ±30° | … |
| B2 settle / peak pitch | … | … |
| B3 body disp / pitch | … | … |
| B4 lag at 3 m/s | ~0.18 m | … |

plus A2/B1/B3/B4 side-by-side videos and U1–U3 pass/fail.

## 4. Scope boundaries for the platform agent

- **No catch attempt**, no perception/IK/fingers, **no propwash model** (the wash
  claim is a hardware/sim2real argument PyBullet can't test — §22; a propwash-cone
  disturbance is a separate task added here later, near the ball/world code).
- Works in a **git worktree**; only *adds* the TV variant + these scenarios.
  Never edits the underactuated path, the throw, or the catch tests.

## 5. After it reports — integration & the cleanup payoff

If the A/B table clears go/no-go: flip the catcher to thrust-vectoring (per-drone
flag), retune position gains, and **delete the underactuation workarounds** —
the diagonal station, "eventual positioning" (§21), and the COM feedforward all
exist to fight pitch-to-translate and should fall away with a body that holds
level on-station. The remaining gap full actuation does **not** close is
**cup-centering at contact** (fingers paddling the ball out at the rim, §21b) —
a gripper-geometry/close-timing problem, same work either way.

## 6. Open decisions (need a call)

1. Propwash model in the agent's scope, or added here later? (Lean: later, here.)
2. Keep pushing the COM-FF catch baseline on the underactuated drone in parallel, or pause behind the prototype?
3. B4 as the single headline pass/fail, or weight all scenarios equally?
4. Promote thrust-vectoring project-wide eventually, or keep it catcher-only?
