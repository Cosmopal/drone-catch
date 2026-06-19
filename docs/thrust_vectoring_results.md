# Thrust-vectoring platform — validation results

Built per `docs/thrust_vectoring_drone_buildspec.md` (concept: `concepts/12`,
decision: `iteration_findings §22`, parking-lot #11). The over-actuated
`ThrustVectoringDrone` (radial tilt servo per rotor → 8 inputs vs 6 DoF) is
validated against the underactuated `Drone` baseline. Both run the **same real
caging gripper** (the TV variant loads the radial-tilt URDF), arm in the catch
pre-pose. The underactuated baseline gets its **full compensation stack**
(arm-reaction FF, gain scheduling, translational-z FF, position integrator, 60°
tilt cap) — it is the strongest underactuated drone, not a strawman.

Reproduce:
```
python assets/make_tv_gripper_urdf.py            # (re)generate the URDF
python tests/thrust_vectoring_solo.py --headless --videos runs/tv
```

## Go/No-Go table

| metric | underactuated | thrust-vectoring | read |
|---|---|---|---|
| **U1** wrench fidelity (max rel err, unsat) | — | **0.000 %** | PASS (<1 %) |
| **U2** yaw decoupling (max \|τz\| on pure Fx/Fy) | — | **2.1e-17 N·m** | PASS (radial tilt is torque-free) |
| **U3** saturation (Fx ramp, β_max=60°) | — | **Fx_max 7.1 N, finite, no flip** | PASS (graceful clamp) |
| **A1** hover hold (err / tilt) | 0.03 cm / 0.1° | **0.00 cm / 0.0°** | both hold |
| **A2** 1 m lateral step — **peak tilt** | **45.8°** | **0.3°** | **TV translates without pitching** |
| **B1** static offset-CoM sag / pitch | 0.0 cm / 0° | 0.0 cm / 0° | already solved in-sim (see note) |
| **B2** 1 m step w/arm — settle / peak pitch | 3.6 s / 45.7° | **1.43 s / 0.1°** | **TV settles 2.5× faster, level** |
| **B3** arm-sweep coupling — body disp / pitch | 2.8 cm / 8.8° | **2.2 cm / 2.7°** | **TV holds tighter AND 3× more level** |
| **B4** track 3 m/s ramp — lag / **peak tilt** | 74 cm / **60°** | 41 cm / **0.3°** | see B4 verdict |

### B4 verdict (headline)

The literal **"position lag < 5 cm" gate is NOT met by either platform** — and
this is a finding about the *metric*, not the platform. Accelerating a drone
from rest to 3 m/s within 0.5 s is **acceleration-bound**: even the idealized
net-wrench-at-CoM allocator (unlimited per-rotor force) lags ~12 cm, because
reaching 3 m/s costs ~1.5 m of runway. The underactuated drone is actually
*competitive on raw position lag* (and on a pure step reposition, slightly
better) because **it can vector its *entire* thrust by tilting the whole body**,
whereas realistic ±60° tilt servos redirect only a fraction of thrust laterally.

The real, catch-relevant discriminator is the second column: **TV holds the body
level (0.3°) while translating; the underactuated drone pitches to 60°.** A
60°-pitched body points the planar 2R arm's cup 60° off-axis — the catch fails
regardless of where the body's x-coordinate is. So full actuation does not buy
*faster* repositioning; it buys **repositioning with the gripper presentation
intact**, which is exactly the pitch-to-translate coupling §22 set out to kill
(the §20 station-keeping fight, the tilt-cap-vs-maneuver tension).

## Allocator (the one genuinely new piece)

Desired wrench `[Fx,Fy,Fz,τx,τy,τz]` → 8 commands (4 thrusts + 4 tilts), using
the **separable closed form** the design predicted:

- **Vertical sub-problem** — `[Fz,τx,τy,τz] → v_i` (per-rotor vertical thrust) is
  the standard quad X-mixer (yaw via rotor-drag differential). 4 eqns, 4 unknowns,
  solved exactly each tick from CoM-relative rotor positions.
- **Horizontal sub-problem** — `[Fx,Fy] → h_i` (per-rotor radial thrust) is
  under-determined (2 eqns, 4 unknowns → the 2-dim null space), solved min-norm
  by pseudo-inverse. The null space is left unused in v1.
- Recombine: `T_i = hypot(v_i,h_i)`, `β_i = atan2(h_i,v_i)`.

Radial tilt is **torque-free** (force through the hub ⇒ `r×F=0`, incl. zero
yaw): U2 measures `τz = 2e-17 N·m`. So the two sub-problems don't fight, and U1
is exact (0.000 %) when unsaturated.

Per-rotor forces are applied as world-frame vectors at each rotor position
(PyBullet integrates the net force + the torque-about-CoM from the application
points); the cosmetic rotor disks are driven to `β_i` so the render visibly
vectors thrust. An `allocator="ideal"` mode (net wrench at CoM) is included as a
controller sanity.

**Saturation (U3 / stability):** vertical-**priority** clamp. `Fz/τ` are always
realized exactly (`v_i` only clipped to `[0, rotor_max]`); lateral force is
best-effort, limited so each rotor stays within both its tilt limit
(`|h|≤v·tanβ_max`) and its thrust cap. This was load-bearing: the naive
"clamp β and T independently" let vertical thrust balloon to ~27 N (4× weight)
under a large lateral demand and launched the body. Priority-clamping fixed it.

## Findings / surprises

1. **The design doc's "hinge axis along the arm" is a slip.** A hinge literally
   along the arm (radial axis) tips thrust *tangentially* (pure yaw) — the option
   §22 rejects. The load-bearing property (radial force ⇒ zero yaw torque, U2)
   needs a **tangential** hinge axis. Every other claim in concepts/12 ("nods
   toward/away from hub", "horizontal thrust along the arm", wash plane through
   center `x+y=0`) is consistent with that. The URDF hinges tangentially;
   documented in `make_tv_gripper_urdf.py`.

2. **Thrust vectoring ≠ more lateral acceleration.** Realistic ±60° tilt servos
   redirect *less* horizontal force than a body that tilts wholesale to point all
   thrust sideways. The over-actuated win is **decoupling** (translate while
   level, U2/A2/B2), not raw agility. This reframes B4: the right metric is
   level-hold, not position lag.

3. **B3 (arm-sweep coupling): a test artifact masqueraded as a TV weakness.**
   First pass had TV at 55 cm vs UA 9 cm. Tracing it: up to mid-sweep the TV held
   *beautifully* (≤1.5 cm, ≤5° at 8 rad/s) — then the sweep drove the shoulder to
   ~170° (the **inverted-pendulum trap**, CLAUDE.md), where gravity yanked the
   arm back at >30 rad/s and produced an **8 N·m reaction torque no quad can
   deliver**. That is arm instability, not body control. With a realistic
   absorption sweep (downward toward the stable straight-down pendulum bottom,
   same 8 rad/s), the result inverts: **TV 2.2 cm / 2.7° vs UA 2.8 cm / 8.8°** —
   the TV holds tighter and 3× more level. Two FFs make this work, both
   disturbance predictors orthogonal to underactuation: the **arm-reaction
   torque** FF (does the level-hold) and a **full 3-axis recoil-force** FF
   (`arm_translational_ff_full`) — the over-actuated body cancels the sweep's
   body-x recoil directly, which the underactuated drone (z-only FF) cannot do
   without tilting. Also fixed an FF ordering bug (the torque FF must run before
   the translational FF, which reads the shoulder-accel predictor it advances).

4. **B1 (static offset-CoM sag) is already solved in this sim** — for *both*
   platforms — by the always-on system-CoM thrust application
   (`Drone._system_com_world`). Even the uncompensated underactuated drone holds
   0 cm / 0°. The "0.35 m / 30°" reference predates that compensation. The
   offset-CoM pain that motivates TV is the **dynamic** case (B3/B4), not static
   hover.

5. **Underactuation-compensation flags stay OFF for the TV by design**
   (`arm_reaction_ff`, `arm_translational_ff_z`, `attitude_gain_schedule`,
   position integrator), confirming the platform doesn't need the pitch-to-
   translate workarounds. The arm-disturbance FFs are *wired* (available) and
   used only for the B3 sweep, where the disturbance is mechanical, not
   actuation-structural.

## Videos (side-by-side: underactuated | thrust-vectoring)

`runs/tv/A2_sidebyside.mp4`, `B1_sidebyside.mp4`, `B3_sidebyside.mp4`,
`B4_sidebyside.mp4`. A2 and B4 are the clearest: the left (UA) body visibly
pitches over while the right (TV) translates flat.

## Scope honored

No catch attempt, no perception/IK/finger logic, **no propwash model** (the wash
claim is explicitly out of scope — PyBullet can't test it; §22). Additive only:
new URDF generator + URDF, new `ThrustVectoringDrone` module, the
`make_solo_drone(thrust_vectoring=…)` flag, and this test. The underactuated
`Drone`/`CascadeController`, the throw, and the catch tests are untouched —
regression gate `tests/elbow_catch_solo.py` still prints `caught=True held=True`.
