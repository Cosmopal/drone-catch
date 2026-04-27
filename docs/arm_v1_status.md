# 2-link Arm v1 — current state and open issues

**Status as of commit `5fb28cd` (WIP).** This doc captures where the arm work
stands, what's built and verified, what's broken, and what to investigate
next session. Companion to:

- [`throw_planning.md`](throw_planning.md) — planner math (still applies; the
  arm changes how `release_vel` is delivered, not what it should be)
- [`iteration_findings.md`](iteration_findings.md) — engineering log of the
  pre-arm tuning loop
- The plan file at `~/.claude/plans/next-up-is-the-quiet-dusk.md` — the
  design we set out to build

## What's built and verified

### URDF (`assets/quadrotor.urdf`)
2-link arm grafted onto the existing quad chassis. New entities:

| Element | Purpose |
|---|---|
| `shoulder_housing` (fixed link) | mounting stub on top of base, gives shoulder a sensible pivot point |
| `shoulder_joint` (revolute) | rotates `upper_arm` about body-`-y` (positive shoulder = forward sweep) |
| `upper_arm` (link) | thin cylinder, hangs along body `-z` at shoulder=0 |
| `elbow_joint` (revolute) | rotates `forearm` about body-`y`, lower limit 0 = extended, upper limit 3.2 ≈ π |
| `forearm` (link) | second thin cylinder |
| `j_ee` (fixed) | attaches `end_effector` to forearm tip |
| `end_effector` (link) | small green sphere at the arm tip; ball gets gripped here |

Joint dynamics: `damping=0.005, friction=0.001, effort=2.0, velocity=20`.
Loaded total mass = 0.625 kg (0.546 base + 0.004 props + 0.075 arm).

### Drone class (`src/drone.py`)
- **Joint discovery** in `__post_init__` finds `shoulder_joint`,
  `elbow_joint`, `end_effector` indices by name (no hardcoded indices).
- **End-effector state** queries via `p.getLinkState`: `ee_state()`,
  `gripper_world_position()`, `gripper_world_velocity()`. The velocity
  query already includes drone-body motion + arm rotation (PyBullet
  computes it correctly), so `release()` just hands that velocity to the
  ball — no manual `ω × r` accumulation needed.
- **Arm motor control**: `hold_arm(s, e)` (POSITION_CONTROL),
  `spin_arm(s_vel, e_vel)` (VELOCITY_CONTROL), `extend_arm()`,
  `fold_arm()`. `step()` calls `_apply_arm()` after the body
  force/torque application.
- **Grasp at end-effector** (was: at base COM): `grasp()` creates the
  fixed constraint with `parentLinkIndex = ee_link`,
  `parentFramePosition = [0,0,0]`. Ball physically follows arm tip
  through any joint motion.

### System-CoM thrust compensation (`Drone._system_com_world` + `step`)
**Critical fix discovered while building.** Without this, articulated
arm motion creates a spurious pitch torque on the body.

- Old behaviour: thrust applied at base link origin (LINK_FRAME with
  `posObj=[0,0,0]`).
- Articulated arm shifts system CoM away from base origin as joints
  move (e.g., extending arm forward shifts CoM ~2.4 cm forward).
- Force at base origin × system-CoM offset = spurious torque about
  the body, ~0.14 N·m for arm-fully-forward.
- Cascade controller has 0.5 N·m budget so it COULD absorb this,
  but only with steady-state body tilt of several degrees — drone
  visibly drifts.

Fix: every `step()`, compute `system_com_world = Σ m_i · pos_i / Σ m_i`
over base + all child links via `getDynamicsInfo` + `getLinkState`.
Apply thrust as `applyExternalForce(... force_world,
posObj=system_com_world, WORLD_FRAME)`.

Verified: arm extended fully horizontal, hover for 3 s.
- Before: drone drifts to (2.04, 0, 1.56), tilts -7.5°.
- After: drone at (0.002, 0, 1.499), tilts -0.7°. ~1000× tighter.

The held ball is NOT included in the system-CoM sum — that's a known
small (~10%) error we tolerate. Gravity feedforward already accounts
for held mass via `_held_mass()`.

### Config (`src/config.py`)
New `ArmConfig` dataclass holds arm geometry (mass, length), motor
limits (`arm_max_torque`, `arm_kp`, `arm_kd`), throw timing
(`spin_omega`, `spin_window_s`, `min_spin_time`,
`follow_through_s`), and release-trigger thresholds
(`release_align_cos_min`, `release_mag_frac`,
`release_decline_threshold`). Lives on `GameConfig.arm`.

`floor_margin` bumped 0.2 → 0.8. Reason: extended arm reaches 38 cm
below drone, plus PD overshoot during descent ~30 cm. Without the
bump the ball clips the floor mid-backup and the drone gets stuck.

`thrower_play_min_offset.z` and `catcher_play_min_offset.z` adjusted
to match (z lo = 0.8 m).

### Controller (`src/controller.py`)
`max_thrust` bumped 12 → 20 N (T/W ≈ 3.3, racing class). The bowling
throw with shrunken floor runway demands more thrust budget than the
no-arm version had headroom for.

Otherwise unchanged — the cascade is stateless and treats arm-bearing
drone correctly via PyBullet's multi-body solver.

### Stationary throw (`src/main.py`)
The "v1" choreography is deliberately simplified relative to the plan:

1. Drone hovers at planner's `release_pos`.
2. Skip backup, skip approach, skip drone runup. Just spin the arm.
3. Compute required `omega = |release_vel| / L_arm`, cap at URDF limit
   (18 rad/s).
4. `spin_arm(omega)` to start arm rotation about body-y.
5. Multi-condition release trigger from plan §F:
   - Gates: `t_since_spin > min_spin_time`,
            `cos(v_ee, release_vel) > 0.5`.
   - Triggers: `v_proj >= 0.7·|release_vel|` OR
               `v_proj past peak (v_proj < v_proj_max - 0.1)` OR
               safety timeout.
6. After release: refold arm, raise `max_tilt_deg` to 180 for evade
   flip-brake, `go_home()`.

This sacrifices the planned drone-translation + drone-pitch
contributions to ball velocity. Setting up the stationary version
first lets us verify arm spin → ball release in isolation before
re-introducing the runup.

### Verified subsystems

| Test | Result |
|---|---|
| URDF loads, 8 joints (6 fixed + 2 revolute) | ✓ |
| Joint discovery finds all by name | ✓ |
| Hover with folded arm, 5 s | drift < 1 mm |
| Hover with arm fully extended forward (worst-case CoM offset) | drift 2 mm, tilt 0.7° |
| Hover with ball gripped at EE (arm always extended) | drift < 1 mm over 2 s |
| Arm extends and refolds on command | ✓ |
| Throw fires (multi-condition trigger) | ✓ (fires on `past_peak` typically) |

## What doesn't work yet

### 1. Throw under-delivers ~50% of target velocity

For target `release_vel = (4.26, 0, 4.65)` (|v| = 6.31 m/s), actual EE
world velocity at release is ~3 m/s. About half of expected.

Trace from one run (peak detected at t=4.17, fired at t=4.21):

| t | drone_pos.z | shoulder | shoulder_vel | EE world vel | v_proj |
|---|---|---|---|---|---|
| 4.000 | 1.36 | 0.02 | 5.4 | (2.02, 0, -0.34) | 1.11 |
| 4.042 | 1.36 | 0.65 | 15.8 | (3.06, 0, -0.44) | 1.74 |
| 4.083 | 1.34 | 1.30 | 15.8 | (3.61, 0, -0.30) | 2.22 |
| 4.125 | 1.31 | 1.96 | 15.8 | (3.86, 0, +0.12) | 2.69 |
| 4.167 | 1.26 | 2.62 | 15.8 | (3.62, 0, +0.82) | **3.05 (peak)** |
| 4.208 | 1.18 | 3.27 | 15.8 | (2.72, 0, +1.55) | 2.98 |

Math says: ω=15.8 rad/s × L=0.4 m = 6.3 m/s tip tangent velocity. Add
drone vel (~+1 m/s in x, dropping in z). So world EE vel should be
~6.3 m/s magnitude with phase varying as arm sweeps. Observed peak is
half that.

**Possible diagnoses (untested):**
- Drone is FALLING during spin (vz goes from -0.08 to -2.20 m/s in
  0.21 s). The arm-rotation contribution to vz is partially cancelled
  by the drone's downward translation. World-frame EE vz never gets
  high.
- Maybe the arm reaches commanded `shoulder_vel` (PyBullet reports
  15.8) but the EE link's actual angular rate in world frame is lower
  because the drone body itself is rotating.
- Possibly `getLinkState`'s velocity convention differs from what I
  assume; the index 6 is documented as "world position derivative of
  urdf link COM" but I haven't verified empirically.

### 2. Drone destabilizes during spin
- Drone z: 1.36 → 1.18 over 0.21 s of spin (drops 18 cm).
- Drone tilts in unexpected directions (small y-component appears in
  EE vel even though throw direction is purely in xz).
- Arm reaction torque is in pitch (about body y), which the cascade
  CAN handle, but apparently not perfectly during the 100-200 ms
  transient at spin start.

The drone falling problem manifests AFTER spin start, suggesting the
arm motor's reaction torque is larger than the cascade compensates
for transiently. CoM compensation is already on, so it's not the
static CoM issue.

### 3. Original bowling-style choreography untested
The plan was:
1. Drone backup deep+low into play area
2. Drone approach forward at hover height with arm extending
3. Drone brake-pitch + arm spin (synergistic)
4. Release at peak EE world velocity

Tried this and hit cascading failures: drone failed to climb back to
release_z after backup descent (lost in z-runway), constraint
instability with folded arm (inverted pendulum, separately fixed),
arm extending mid-flight overwhelmed cascade, etc.

The stationary throw is what's running now. Re-layering the runup is a
follow-up once the stationary throw delivers planned `release_vel`.

## Open puzzles for next session

In likely order of investigation:

1. **Why is EE world velocity half of `ω·L`?** Add explicit instrumentation:
   log `getLinkState(ee_link)[7]` (link angular velocity in world frame)
   alongside `joint_states()[1]` (joint velocity). If they differ, the
   issue is somewhere in the joint-to-world rotation. If they match,
   the issue is the rotation contribution being cancelled by drone
   body motion.

2. **Why does drone fall during spin?** Probably arm reaction torque
   destabilizes the cascade transiently. Could log `omega_drone` over
   the spin window to see if drone is rotating + drifting from arm
   reaction. Mitigation candidates:
   - Stiffer attitude gains during throw window (`kR`/`kw` bump).
   - Pre-pitch the drone slightly nose-up before spin (so arm reaction
     reinforces rather than fighting an upright pose).
   - Feed-forward the arm reaction torque into the cascade's body-torque
     command (would need the cascade to know about arm dynamics).

3. **Decide stationary vs bowling-style for v1 demo.**
   - If we can get stationary throw to deliver planned `release_vel`
     within 10%, ship it as v1 and add bowling-style as v1.5.
   - If stationary throw can't reach planned vel even with arm at URDF
     max ω = 20 rad/s, we MUST add drone translational contribution
     (i.e., return to the bowling-style design).

4. **Catcher with arm.** Currently catcher still uses the body-COM grasp
   (we changed Drone class but main.py only updated thrower's flow).
   The catcher's grasp call still works because we kept backward-compat
   semantics, but it ignores the EE link entirely. Once thrower throw
   works, give catcher symmetric arm and use it to extend-and-receive.

## Lessons captured (append to iteration_findings.md after v1 ships)

- **Articulated bodies need system-CoM thrust application.** Apply
  external force at base origin only when base = system CoM. If you
  add child links, compute system CoM each step.
- **Folded position is an inverted-pendulum trap if EE goes above the
  joint pivot.** Always-extended is safer in sim. Real hardware needs
  a different folding mechanism (telescope, sliding, retract-into-body).
- **Mass-ratio-to-floor-runway is a hidden coupling.** Adding a 38 cm
  arm forces the floor margin up by ~30 cm, which forces `max_thrust`
  up by ~30% to maintain matched-t backup feasibility. Cascade of
  compromises that has to be planned, not discovered.
- **`getLinkState` velocity vs commanded joint velocity.** Don't assume
  the joint motor's `targetVelocity` is what `getLinkState` reports for
  the linked link's velocity. Verify empirically.
