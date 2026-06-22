# Over-actuation, thrust vectoring & control allocation

> Status: **design study, not yet built.** This note records a concept we
> reasoned through (and a layout/tilt decision we made) for a future
> thrust-vectoring drone. The current sim is still a fixed-rotor quad. See
> iteration_findings §22 for the discussion that produced it.

## What it is

A standard quadrotor is **underactuated**: 4 actuators (rotor speeds), 6
rigid-body DoF (3 translation + 3 rotation). The 4 inputs buy you total
thrust + 3 body torques — but thrust only ever points along body-z. To
translate horizontally you *must* tilt the whole body first. That single
fact is the root of most of our controller stack: the cascade
(position → desired tilt → attitude, concept 02), the Lee-SO(3) 180°
singularity, the tilt cap fighting throw/catch maneuvers, and the body-x
recoil coupling we plan around rather than cancel.

**Thrust vectoring** breaks that coupling by giving each rotor a tilt DoF
(a servo), so thrust direction is commandable, not welded to body-z.

### The wrench

The clean way to think about *any* flight controller's job: it decides one
desired **wrench** — a 6-vector bundling the net force and net torque on
the body:

```
wrench = [ Fx, Fy, Fz,   τx, τy, τz ]
           └── force ──┘  └─ torque ─┘
          (move the COM)  (rotate body)
```

One force + one torque component per DoF. The actuators' only job is to
*produce* that wrench. Underactuated → the achievable wrench set is
crippled (`F` only along body-z, so lateral force is chained to attitude).
Fully/over-actuated → you can command all 6 independently.

### Control inputs vs. DoF (the bookkeeping that confused us)

For a tilt-rotor quad with **one tilt servo per rotor**:

| Per rotor | meaning | count |
|---|---|---|
| rotor spin | thrust magnitude | 1 input |
| tilt servo | thrust direction (1-DOF) | 1 input |

So **4 rotors → 8 control inputs**. That "8" is *not* "2 tilt axes per
rotor" — each rotor has exactly **one** tilt servo; the two inputs are
*how hard it pushes* and *which way it tips*. (A 2-DOF gimbal would be 2
servos/rotor = 8 servos = omnidirectional; we don't need it.)

```
8 control inputs  >  6 body DoF  →  over-actuated, null space = 8 − 6 = 2
```

The 2 surplus dimensions are the **null space**: a family of different
actuator combinations that all produce the *exact same* wrench. The body
can't tell them apart, so they're free to optimize a secondary objective
(minimize power, keep tilts small, steer wash — see below).

## Control allocation

The new computational piece. Given a desired wrench, solve for the 8
actuator commands:

```
desired wrench (6)  →  [ allocation ]  →  8 actuator commands
```

The map is nonlinear (lateral force = thrust · sin(tilt)). With 8 > 6 it's
under-determined, so allocation = pseudo-inverse (or a small QP) **plus** a
null-space secondary objective. Critically, this *replaces* the cascade:
no inner/outer loop, no thrust-direction→attitude inversion, **no 180°
singularity** — you command position and attitude independently and the
allocator finds tilts + thrusts. The architecture gets *simpler*; the
allocation is the one genuinely new subproblem.

## Layout & tilt-axis decisions (what we settled on)

Two design choices, both driven by **rotor downwash on the incoming ball**
(a real hardware effect; PyBullet models none of it — see Sim caveat):

### 1. Quadrant (X) layout, not plus (+)

Rotors at body-frame `(±0.10, ±0.10)` — on the diagonals. The catch happens
in an axis-aligned plane (x-axis catch → ball in the `y=0` plane). With the
rotors in the quadrants, that plane **threads the gap between the two near
rotors** (each `0.10 m` off-axis, disk radius `0.04` → nearest edge `0.06 m`
away): the downwash columns *straddle* the ball path instead of sitting on
it. A `+`-config would put a rotor dead on the catch axis — worst case.
Bonus: by symmetry the quadrant layout straddles for *both* x and y catches.
(Cost: a diagonal catch aligns with an arm — acceptable, we catch on axes.)

### 2. Radial tilt, not tangential

A single tilt servo can hinge two ways. Sighting down the arm from the hub:

| | hinge axis | rotor motion | horizontal thrust |
|---|---|---|---|
| **Radial** *(chosen)* | along the arm | nods toward/away from hub | along the arm |
| Tangential | ⊥ arm | rocks sideways across arm | perpendicular to arm |

We chose **radial** for two reasons:

- **Wash stays off the catch line.** Radial thrust points through the hub,
  so its wash plane *passes through the center* — one of the diagonal planes
  `x = ±y`, all 45° off the catch axes. Tangential thrust tips perpendicular
  to the arm, so its wash plane is *offset out to the rotor ring* and slices
  the catch region. Concretely, for the near rotor at `(−0.10, +0.10)`, where
  each tilt-wash plane crosses the `y=0` catch plane:
  ```
  radial:     x + y = 0     → crosses y=0 at x = 0      (body center — clear)
  tangential: x − y = −0.20 → crosses y=0 at x = −0.20  (right at the EE!)
  ```
- **Yaw decoupling.** A radial force points through the hub → zero moment arm
  → **radial tilts produce no yaw torque.** So `4 tilts → clean Fx, Fy`
  (pure lateral translation, no yaw cross-talk) and `4 thrusts → Fz, τx, τy`
  + yaw via drag-torque differential (exactly like the current quad).
  Tangential is the opposite: each tilt is pure yaw. Radial's only cost — no
  tilt-based yaw authority — is free for us, since we yaw on drag torque today
  and don't need fast direct yaw for axis-aligned catches.

Reachability check: radial spans the full plane (front pair tilt outward +
rear pair inward → `+Fx`; the mirror gives `+Fy`).

## Division of labor (where the arm stops and the body starts)

Our 2R arm is planar in the body x–z plane (shoulder + elbow **both** rotate
about body-y), so it can only move the EE in x–z; it **cannot** make a
lateral (y) adjustment. The folded catch pose (concept 10, iteration §20)
reaches ~0.30 m back-and-down, aiming the approach tangent and reserving
joint travel for the absorption sweep. So:

| job | who |
|---|---|
| in-plane (x, z) approach tangent + momentum absorption | the folded 2R arm |
| lateral (y) positioning, body level | the over-actuated body |
| baseline downwash | quadrant layout (straddle the catch plane) |
| steered (tilted) downwash | radial-plane geometry + tilt→0 at contact |

The arm and the over-actuated body are **complementary**, not redundant.

## Sim caveat

PyBullet has no fluid model — air drag is constant linear damping per body,
and there is **no aerodynamic coupling between one body's rotor and another
body**. So *none* of the wash analysis above is testable in the current sim:
a tilted rotor has exactly zero effect on the ball. To study it you'd add a
crude propwash disturbance (a momentum-jet force on the ball when it enters a
cone behind a tilted rotor, falling off with distance + off-axis angle), which
would also let you test null-space wash-steering. Until then the wash reasoning
is a hardware/sim2real design argument, not a validated result.

## For larger projects

- **Control allocation is universal** for any over-actuated platform
  (redundant manipulators, multi-thruster spacecraft/AUVs, omni-wheel bases):
  desired generalized force → null-space-resolved actuator commands. The
  pseudo-inverse-plus-secondary-objective pattern transfers directly.
- **Under- vs fully-actuated is a structural property, not a tuning knob.**
  Counting inputs against DoF tells you up front whether a coupling (like
  "tilt to translate") is *fundamental* (fix it with mechanism) or merely
  *unmodeled* (fix it with control). We spent a lot of the cascade era
  fighting a fundamental one.
- **The null space is a resource.** Once you have more inputs than DoF, every
  "extra" actuator is a free secondary objective (efficiency, limit-avoidance,
  disturbance-shaping). Designing *what* to put in the null space is its own
  lever — here, steering wash away from a delicate manipulation.
