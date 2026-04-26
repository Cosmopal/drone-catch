# Planning a drone-to-drone throw

How to pick a release state for the thrower drone, and how to plan a windup
that physically delivers the drone to that release state. The audience here
is "us, six months from now": the goal is to keep the *reasoning* — not just
the formulas — recoverable.

The throw choreography lives in `src/main.py`. The planner that picks
`(release_pos, release_vel, backup_pos, t_ramp)` lives (or will live) in
`src/planner.py`.

---

## 1. Problem framing

Two drones hover in an indoor room. One holds a small dense ball, throws it,
the other catches. Inputs to the planning problem:

| Quantity | Symbol | Our value |
|---|---|---|
| Drone mass | `m` | 0.55 kg |
| Drone max thrust | `T_max` | 12 N (T/W ≈ 2.22) |
| Drone max tilt (software cap) | `θ_cap` | 35° |
| Ball mass | `m_b` | 0.065 kg |
| Ceiling | `z_ceil` | 3.0 m (residential) |
| Hover height | `HOVER_Z` | 1.5 m |
| Catcher position | `p_c` | given (e.g. `(2.5, 0, 1.5)`) |
| Thrower play area | — | back half of room |

Everything else — release point, release velocity, backup point, windup
duration, apex, etc. — is for the planner to choose.

The job is to pick `(release_pos, release_vel)` such that:

1. The *ball*, launched from `release_pos` with `release_vel`, ballistically
   arrives at `p_c`.
2. The *drone* can physically reach `release_pos` with velocity
   `release_vel` from some feasible backup point inside the play area,
   subject to thrust and tilt limits.

These two halves couple. Ballistic targeting alone is trivial. Drone
trajectory generation alone is well-studied. Co-solving them — "the drone
*is* the launcher, and its body has to deliver position *and* velocity
simultaneously at release" — is the interesting part.

This sits in the lineage of aerial manipulation work: Mellinger & Kumar
(2011) on minimum-snap quadrotor trajectories, Hehn & D'Andrea (ETH 2011)
on quadrotors juggling balls, the Flying Machine Arena demos, MIT
TossingBot for robot-arm throwing. The "drone is the launcher" framing
is recognised but less mature; what we have here is a deliberately
simplified take.

---

## 2. The ballistic part (the easy half)

Assume a **symmetric throw**: `release_z = catcher_z = HOVER_Z`. The ball
returns to its release height with the same speed magnitude — by energy
conservation, neglecting drag.

For horizontal range `R = |p_c.xy − release_pos.xy|`:

    t_flight = 2·vz / g
    R = vx · t_flight  ⇒  vx · vz = R · g / 2

So `(vx, vz)` lies on a hyperbola in velocity space — every point on it
hits the same landing spot, just with different arc shapes.

The ceiling caps the apex. Apex height above the release is `vz² / (2g)`, so

    vz_max = √(2g · (z_apex_max − release_z))

With `z_ceil = 3.0` and a 0.4 m margin → `z_apex_max = 2.6`. From
`HOVER_Z = 1.5`, `vz_max = √(2·9.81·1.1) ≈ 4.65 m/s`.

For a 5 m range, sweep `vz` along the curve:

| `vz` (m/s) | `t_flight` (s) | `vx` (m/s) | apex above release (m) | `|v|` (m/s) | tilt @ az=0 (deg) | `T/m` needed (m/s²) |
|---|---|---|---|---|---|---|
| 4.65 | 0.948 | 5.27 | 1.10 | 7.03 | 20.0 | 15.4 |
| 4.00 | 0.815 | 6.13 | 0.82 | 7.32 | 22.4 | 14.9 |
| 3.50 | 0.714 | 7.00 | 0.62 | 7.83 | 24.6 | 14.6 |
| 3.00 | 0.611 | 8.18 | 0.46 | 8.71 | 27.2 | 14.5 |
| 2.50 | 0.510 | 9.81 | 0.32 | 10.12 | 29.9 | 14.6 |
| 2.00 | 0.408 | 12.26 | 0.20 | 12.42 | 32.6 | 14.9 |

Two things to read from this:

- **45° release minimises `|v|`** (and so minimises arrival KE for a
  symmetric throw — soft-catch friendly). At 5 m range, true 45° wants
  `vz = vx ≈ 4.95 m/s`, but our ceiling caps `vz` at 4.65 — so the
  energy-optimal feasible release is the top row.
- Pushing `vz` *down* trades apex margin for higher `vx` and a flatter,
  faster ball. Tilt and total thrust grow modestly. Apex margin is the
  big lever.

**Asymmetric throws** (`release_z ≠ catcher_z`) add one parameter — the
height delta — and let you e.g. release low and catch high if the geometry
demands. We defer this; symmetric is simpler and the optimum for soft
catching.

---

## 3. The drone trajectory part (the harder half)

The cascade controller is Lee-style geometric attitude on SO(3) (see
`src/controller.py`):

1. Outer loop: position PD computes a desired specific force vector
   `f_des = m·(kp·e_p + kd·e_v) + m·g·ẑ`.
2. Clip the *direction* of `f_des` so the angle from vertical is at most
   `θ_cap = 35°`.
3. Inner loop: build `R_des` so body-z aligns with the (clipped) `f_des`,
   apply attitude PD on `SO(3)`.
4. Thrust scalar = `f_des · body_z`, clipped to `[0, T_max]`.

Quads are underactuated: thrust is only along body-z. To accelerate
sideways you tilt; tilting trades vertical thrust for horizontal thrust.

The two equations to keep in your head:

    General:           ax = (T/m)·sin θ
                       az = (T/m)·cos θ − g

    Holding altitude:  T = m·g / cos θ
                       ax = g · tan θ

Two ceilings on tilt:

| Limit | Formula | Numeric (m=0.55, T_max=12) |
|---|---|---|
| Software cap | `θ ≤ θ_cap` | 35° |
| Thrust cap (must support weight) | `cos θ ≥ m·g / T_max` | `θ ≤ acos(0.45) ≈ 63°` |

Software is binding for us. Were we flying a heavier payload or a wimpier
quad, the thrust cap would bite first.

At `θ_cap = 35°` and altitude-hold, the available horizontal accel is
`g·tan(35°) ≈ 6.87 m/s²`. For the climbing throws of section 2 we want
both `ax > 0` and `az > 0`, which costs more thrust than altitude-hold —
hence the `T/m ≈ 14–15 m/s²` numbers in the table (vs. `T_max/m ≈ 21.8`).

---

## 4. The matched-t single ramp (the connective insight)

We want the drone, starting from rest at `backup_pos`, to arrive at
`release_pos` with velocity `release_vel`. The simplest feasible plan is a
**linear velocity ramp** of duration `t_ramp`:

    vel_ref(t) = release_vel · t / t_ramp
    pos_ref(t) = backup_pos + ½ · release_vel · t² / t_ramp

Position is just the integral of velocity — the area of the v-t triangle.
At `t = t_ramp` the displacement is `½ · release_vel · t_ramp` (triangle
area = ½ · base · height).

For both `pos_ref(t_ramp) = release_pos` and `vel_ref(t_ramp) =
release_vel`, the backup point is **forced**:

    backup_pos = release_pos − ½ · release_vel · t_ramp

This is the matched-t condition. **Why it matters**: if you don't
co-design `backup_pos` and `t_ramp` to be consistent, the position and
velocity references at every step ask for inconsistent things. We
discovered this empirically — the early throws drifted high (vz reference
exceeded what the constant accel could deliver while still tracking pos),
or undershot release speed (vel ramp arrived at release_vel but the drone
had already braked because it overshot pos). Both failure modes vanish
once `backup_pos` is derived from `release_vel · t_ramp / 2`.

Geometric reading: a chosen `(release_pos, release_vel)` pair defines a
ray going *backward* from `release_pos` in the `−release_vel` direction.
`t_ramp` slides `backup_pos` along that ray. Larger `t_ramp` → backup
further behind release → lower required acceleration but more runway. The
play-area boundary clips `t_ramp` from above; thrust/tilt clip it from
below.

The constant acceleration during the ramp is

    a_ramp = release_vel / t_ramp

with magnitude `|release_vel| / t_ramp`. Add `g·ẑ` for the specific force
the controller has to produce, then convert to thrust/tilt via section 3.

---

## 5. Free variables for the planner

A specific throw is fully determined by surprisingly few choices. Pick:

| Choice | Range | Notes |
|---|---|---|
| `release_x, release_y` | thrower's play area | x affects ballistic range, y affects throw line |
| `release_z` | ~`[1.0, 2.5]` m | symmetric (= `HOVER_Z`) is energy-optimal |
| `vz` | `(0, vz_max]` | vz_max set by ceiling |
| `t_ramp` | `(t_min, t_max]` | bounded by thrust below, runway above |

Everything else falls out:

- `vx, vy` from the ballistic constraint (range and direction to catcher).
- `release_vel = (vx, vy, vz)`.
- `backup_pos = release_pos − ½ · release_vel · t_ramp`.
- Required specific force: `release_vel / t_ramp + g·ẑ`.
- Required thrust = `m · |that|`; tilt = angle from vertical.
- Apex above release = `vz² / (2g)`; apex margin = `z_ceil − apex_z`.
- Arrival KE at catcher = `½ · m_b · |release_vel|²` (symmetric throw).

So the search space is really 4-D (or 3-D if we fix `release_y` on the
throw line and `release_z = HOVER_Z`).

---

## 6. Hard constraints

A candidate must satisfy all of these or it's discarded:

| Constraint | Formula |
|---|---|
| Ballistic reach | `vx · vz = R · g / 2` (built in) |
| Apex below ceiling | `release_z + vz²/(2g) ≤ z_ceil − margin` |
| Thrust budget | `m · |release_vel/t_ramp + g·ẑ| ≤ T_max` |
| Tilt budget | `atan2(|a_horiz|, g + a_vert) ≤ θ_cap` |
| Backup in play area | `backup_pos.xy` inside thrower's region, `backup_pos.z ≥ z_floor + margin` |
| Release in play area | same check on `release_pos` |

Concrete numbers for our setup: `T_max/m = 21.8`, `θ_cap = 35°`,
`z_ceil = 3.0`. With the row-1 throw (`release_vel = (5.27, 0, 4.65)`)
and `t_ramp = 1.0 s`, required `T/m = 15.4`, used 71% of thrust, tilt 20°.
All comfortably inside the budget.

Halving `t_ramp` to 0.5 s doubles the demanded acceleration; required
`T/m` jumps to ~22 (saturates) and tilt to ~29°. So `t_ramp ≈ 1.0 s` is
about the right order of magnitude for our drone — fast enough to fit in
a 5-second episode, slow enough to leave headroom for disturbance
rejection.

---

## 7. Soft objectives (the multi-objective part)

Among feasible candidates we want to *prefer* certain ones. Four
objectives, none dominant:

| Objective | Formula | Why we care |
|---|---|---|
| Minimise arrival KE | `½ · m_b · |release_vel|²` | Soft catch — easier on the catcher |
| Maximise thrust margin | `T_max − T_required` | Headroom for tracking error and disturbance |
| Maximise tilt margin | `θ_cap − θ_required` | Same — and avoids attitude-controller singularities |
| Maximise apex margin | `z_ceil − apex_z` | Ceiling clearance for unexpected overshoot |

These trade off. Lower-KE throws are higher-arc (more apex, less apex
margin). Larger `t_ramp` gives more thrust/tilt margin but pushes the
backup point further back, which may leave the play area. There is no
single best throw; there's a Pareto frontier.

---

## 8. Optimisation approach

For an interactive sandbox, **grid search + Pareto filter** is the right
hammer:

1. Enumerate candidates over `(release_x, release_z, vz, t_ramp)` on a
   reasonable grid (say 10×5×8×5 = 2000 candidates).
2. For each, compute everything in section 5–7.
3. Drop infeasible (section 6).
4. Drop Pareto-dominated (section 7).
5. Pick from the frontier.

Why grid + Pareto, not a gradient optimiser?

- **Visibility.** We can plot the frontier and see the trade structure.
  Useful while we're still building intuition for what "good" means.
- **Debuggability.** A failed candidate fails for a *named* reason
  (apex, thrust, tilt, runway) and we can show that.
- **Cost.** 2000 closed-form candidate evaluations is microseconds —
  pre-computed once at episode start, not in the control loop.

For real-time replanning at 100 Hz with state feedback, you'd switch to
`scipy.optimize` (SLSQP), CasADi, or a hand-rolled QP. Not now.

**Picking from the frontier.** Two reasonable policies:

- *Random.* Pick uniformly from the frontier each episode. Gives
  behavioural variety, useful for stress-testing the catcher.
- *Scalarise.* Weighted sum, e.g.
  `score = w_KE · norm_KE + w_T · norm_T_margin + …`, then take the min.
  The weights *are* the policy — making them explicit forces us to say
  what we want.

We'll start with random and scalarise once we have data.

---

## 9. Pareto frontier — concept and algorithm

**Definition.** Candidate A *dominates* B iff A is no worse than B on
every objective and strictly better on at least one. A candidate is
Pareto-optimal iff no other candidate dominates it. The frontier is the
set of Pareto-optimal candidates.

**Geometric picture.** Plot any two objectives — e.g. arrival KE on x,
thrust margin on y (with both signed so "lower is better"). The frontier
is the lower-left envelope of the cloud. Anything above-and-to-the-right
of another point is dominated and gets dropped.

**Algorithm.** O(n²) brute pairwise check is fine for hundreds of points:

    frontier = []
    for a in candidates:
        if not any(dominates(b, a) for b in candidates if b is not a):
            frontier.append(a)

For thousands, sort by one objective and sweep. We're not there yet.

---

## 10. Multi-phase considerations (deferred)

The throw is phase 2 of a three-phase choreography:

1. **Backup positioning.** Drone moves from current pose to `backup_pos`,
   facing release direction, at rest.
2. **Throw windup.** Linear velocity ramp over `t_ramp` to release state,
   then `release()` hands the ball off with `release_vel`.
3. **Post-release evade.** Drone decelerates, recovers, gets out of the
   ball's path (and out of the catcher's path).

For now we treat these sequentially: the planner solves phase 2, and we
trust phases 1 and 3 individually. The honest fix is **joint
optimisation across all three phases** — a multi-phase optimal control
problem with continuity constraints at the phase boundaries. The right
tools for that are TrajOpt, Drake, or Acados. We're not there yet, but
worth flagging because phase 3 *will* eventually constrain phase 2 (e.g.
"don't release with so much forward speed that you can't decelerate
before the wall").

---

## 11. Open questions / future work

- **Asymmetric throws** (`release_z ≠ catcher_z`). Frees one more
  parameter; useful when thrower and catcher hover at different heights,
  or to deliberately throw "downhill" for higher speeds at lower apex.
- **Joint throw + evade optimisation.** As above — phases 2 and 3 share
  state and shouldn't be solved in isolation.
- **Trajectory tracking inside the windup.** Right now we feed the
  controller a static lookahead position target plus a linear `vel_ref`
  ramp. A cleaner approach: generate a full reference trajectory
  `(pos_ref(t), vel_ref(t), acc_ref(t))` from a polynomial (Mellinger-style
  minimum-snap), and feed *consistent* triples each step. Should let us
  hit tighter plans without the lookahead hack.
- **Soft-catch via velocity-matched grasp.** Already in the deferred list
  in `CLAUDE.md`. Relevant here: low-KE throws (top of section 2 table)
  are exactly the ones the velocity-matched catcher will handle best, so
  KE minimisation pulls double duty.
- **Replanning under tracking error.** If the drone gets blown off the
  reference during the windup, the planned `release_vel` is stale. A
  closed-loop replan at release time (using current state as the new
  initial condition) would make the throw robust.

---

## Cross-references

- `src/main.py` — phase machine that runs the throw choreography.
- `src/controller.py` — the geometric cascade controller whose limits set
  `θ_cap` and `T_max`.
- `src/ball.py` — `predict_landing` for the catcher side; used to close
  the loop on the ballistic prediction the planner makes.
- `src/planner.py` — to be written; this doc is its spec.
