---
tags:
  - agent-loop
---

# Grasp Goal-2 — dynamic catch milestone (spec + lead handoff)

> Written 2026-09-19 by the LEAD session (`grasp-iter-lead`) so this milestone
> survives a restart. The chronology lives in [[goal2-run-log]]; the loop's rules
> live in [[grasp-goal2-loop-spec]]; the harness's operating knowledge lives in
> [[grasp-harness-operating-notes]] (written by the worker); the team's
> roles/resume guide is [[team-workflow]]. **This document is the forward-looking
> plan** — what we build next, why, what is already decided, and what is still
> open. A successor lead should be able to run the milestone from this plus those.

## 1. Status at handoff ^1

| milestone | state |
|---|---|
| M-A (setup + regression) | **CLOSED.** Gate A (`arm_catch_solo --grid`) robust: 12/12, and 108/108 under solver × velocity-nudge attack. Gate B (`elbow_catch_solo`) demoted to informational — marginal on both platforms, not a platform regression. |
| M-B (adaptive re-centering, static) | **CLOSED AND SCOPED** by human decision, 2026-09-19. No usable positive result. See [[#^2::§2]]. |
| Dynamic catch (this doc) | **DESIGNED, PRE-REGISTERED, NOT BUILT.** All rulings landed ([[#^6::§6]]). Prereg: `goal2-prereg-dynamic-catch.md` (sealed from worker and gates). |
| M-C / M-D as written in the loop spec | Superseded in shape by this milestone; the intent of [[grasp-iteration2-spec#^2::§2]] deliverable 6 (dynamic, kept strictly separate from static) is preserved. |

Environment: Windows, conda env `robots` = Python 3.11.16, numpy 2.4.6,
pybullet 3.2.5 (conda-forge). The old WSL env is gone and deliberately not
restored. **Do not change these versions mid-study** — it invalidates paired
comparisons.

Everything for this study lives on branch `grasp-iter2`, worktree
`.claude/worktrees/grasp-iter2`, **not merged to main**. `docs/cage_frames/iter2/`
does not exist on main at all. A convenience copy of the M-B review videos sits at
`mb-evidence/` in the main checkout (untracked, disposable).

## 2. What M-B concluded, and why it is limited ^2

The honest epitaph: **failed as science, succeeded as metrology.**

No convergent-positive pull-in advantage for either adaptive strategy anywhere
tested. Two apparent positives (`prb_pulse` at 4.5 cm, `prb_active` at 5.0 cm) did
not survive joint perturbation — but the joint corner that killed them is itself
the single anomalous cell in the convergence grid, so **neither the headline nor
its refutation is trustworthy**. At 4.5–5.0 cm the harness cannot resolve ~1 cm
pull-in differences.

What it did establish, all of it about the instrument:

- The [[grasp-iteration2-spec#^2|§2.3]] convergence battery is
  **one-axis-at-a-time** and therefore blind to joint corners. Fine timestep ×
  soft contact breaks results that no single axis touches.
- **Convergence certificates are per-property, not per-harness.** 1/960 was
  certified in [[iteration_findings#^26|§26]] against the caged/escaped *binary*;
  it was silently assumed valid for *pull-in*, a continuous sub-centimetre
  quantity. A finer metric means a stronger burden; certificates never transfer
  downward.
- **Escape-margin is censored**, not measured: `A_MAX_ESCAPE` is a search cap, so
  "10 g" means "did not escape at the highest disturbance tested."
- A **solver blow-up** at fine substep × stiff contact × 5.0 cm, outside every
  prior convergence table (the battery sweeps substep {2,4,8} only).
- **The placement is invalid above ~3.5 cm.** The ball is spawned *inside* a
  finger — −1.98 mm at 1.5 cm rising to **−34.21 mm at 5.0 cm on a 30 mm-radius
  ball**, with a first-tick normal force of 124 N at default stiffness against a
  0.25 N·m tendon budget. So `pull_in = offset − seat_off` measures from a
  position the ball never settles at, and offset is confounded with penetration
  depth. Human ruling: scope it, keep the small-offset nulls, annotate
  [[iteration_findings#^29|§29]], do not re-baseline.

**The design-level reason M-B was the wrong experiment:** a 4-finger cage is
axisymmetric about its approach axis, so a *lateral* offset attacks the one
direction where the geometry has gaps between fingers. The study varied the
mechanism's weakest axis and reported a worst-case probe as a characterization.

## 3. The next milestone: axis-aligned dynamic catch ^3

### 3.1 The question

**Feasibility and envelope, NOT comparison.** Given that a ball actually arrives,
what speed × misalignment × miss-distance envelope does a simple passive hand
catch and retain? The deliverable is an envelope, which doubles as **the
specification the flight and arm system must hit**.

This must not be read as evidence that this hand beats some alternative. The test
is deliberately configured to give the mechanism its best axis, so a favourable
result is weak evidence and an unfavourable one is strong. See [[#^5::§5]].

### 3.2 Testbed shape

**Fixed base.** No drone, no cascade, no tracking, no IK — a dynamic counterpart
to `cage_harness.py`, not a variant of `elbow_catch_solo.py`.

The reason is not convenience. M6's in-flight catch
([[iteration_findings#^13|§13]]) failed at a ~7–10 cm **rendezvous** miss, and
M7/M8's remaining failure is **velocity matching**. Both are *delivery* problems.
Nothing in this project has ever isolated the hand question from the delivery
question. This test asks only: given the ball arrives where it should, does the
hand catch it?

It also sidesteps the placement defect entirely — the ball starts far away and
flies in, so there is no spawn overlap.

### 3.3 Configuration (decided)

| element | decision | rationale |
|---|---|---|
| Hand | **passive `prb` only** | M-B resolved no difference between passive/pulse/active; [[14-hardware-envelope::concepts/14]] favours the simple single-actuator topology, which Yale's Model T proves is real hardware |
| Palm | **dished, in the baseline** | human ruling; the convex 12 mm sphere actively de-centres a 30 mm ball |
| Orientation | **cup mouth faces the incoming ball** — anti-parallel to arrival velocity, about 46° from vertical for the nominal throw, leaning toward the thrower | the cup does not point *along* the velocity; it points *into* it |
| Gravity | **ON** throughout | the dish only re-centres because weight drives the ball downhill; gravity-off makes it an inert bowl |

Reach note: the arrival-aligned pose reaches **further** than a vertical cup —
0.373 m folded at ≤45° tilt versus 0.209 m vertical. The realistic pose is the
easier one.

**What the dish is FOR, and what it is not for** (human ruling, 2026-09-22).
Retention is the **cage's** job — the 4-finger × 3-segment hand with the long
proximal phalanx was built to survive **full inversion** ([[iteration_findings#^13|§13]] → [[iteration_findings#^15|§15]]), which
is exactly why the 2-segment version was rejected. Form closure holds the ball at
any orientation with no help from gravity. **The dish exists only to stop the palm
actively DE-centring the ball during capture** — the current convex 12 mm sphere
against a 30 mm ball is an unstable equilibrium. Do not design any pose, hold, or
control behaviour that depends on the dish for retention, and do not ask the arm
to maintain an awkward attitude to keep gravity seating the ball. After capture
the arm returns to its natural carry pose and the cage does the work.

**Recorded cost of dishing the baseline:** dish and axis-alignment change
together, so no effect can be attributed to either alone. Disqualifying for a
comparison; acceptable for an envelope. Must not be written up as though the dish
were isolated.

### 3.4 The grid (approved) ^34

A **coarse factorial with deliberate adverse corners** — explicitly *not* staged
one-axis-at-a-time, because that is the structure whose joint corner hid M-B's
failure.

| variable | values |
|---|---|
| approach speed | 1.5, 2.8, 4.0 m/s |
| misalignment magnitude | 0°, 10°, 20°, 30° |
| misalignment azimuth | toward-finger, toward-gap |
| lateral miss | 0, 1.5, 3.0 cm |

Plus cells where all three adverse factors coincide, and **at least one cell
deliberately beyond expected capability** (the uncovered-cell rule — see
[[#^5::§5]]).

**Why azimuth is finger-vs-gap and not in-plane-vs-out-of-plane:** the hand has
4-fold symmetry about the cup axis, so by C4 only two azimuths are distinct — 0°
(toward a finger) and 45° (toward a gap). In-plane versus out-of-plane is a
property of the *arm*, not the hand, and is meaningless in a fixed-base test. It
matters only when *interpreting* the result: an in-plane error the 2R arm could
learn to correct; an out-of-plane error it cannot, without yaw control and a
singularity-free attitude controller (parking-lot #3/#4). Same tolerance,
different engineering consequence — so report the two azimuths separately.

Sanity on the ranges: the splayed mouth is ~10 cm across against a 6 cm ball, so
lateral tolerance is bounded near 2 cm before the ball strikes a finger rather
than entering; and at 2.8 m/s a 20° misalignment puts ~0.96 m/s *across* the cup
axis, which is the component that would carry the ball out through a gap. The
ranges should bracket the boundary rather than sit wholly inside or outside it.

### 3.5 Metrics — and what is retired

**Retired:** pull-in (a static-study artifact, and its origin is fictitious above
~3.5 cm); lateral offset as the independent variable; the static placement.

**In use — ball side:** captured (ball arrested inside the cage); retained
(survives a disturbance or lift); peak contact force; and seated quality at rest,
which is meaningful for the first time because gravity is on and the ball actually
settles.

**In use — ARM and BODY side (added 2026-09-22, and these may bind first):**

- **Peak joint torque at shoulder and elbow, per cell.** The impulse to arrest the
  ball is fixed at m·v whatever the hand does; compliance lowers peak FORCE by
  spreading that impulse over time (~70 ms in M5), and it does not change the
  impulse. Torque is a third and separate quantity: `τ = r × F`, so identical
  force produces wildly different joint load depending on where the ball strikes
  and which way the contact normal points. At 0° misalignment the force line runs
  down the forearm and passes near the elbow axis (axial compression, trivial); at
  20° it is offset and the motor must react a real moment.
  **This is a CAPTURE failure mode, not merely an actuator-sizing concern:** an
  underactuated tendon hand does not break when torque exceeds its cap, it
  **back-drives** — joint yields, fingers open, ball leaves. That is exactly the
  M-A failure (fingers pinned at their 0.5 N·m cap, splaying, ball gone at
  t = 3.9417). So torque above cap breaks a catch that ball-side numbers would
  call fine.
- **Peak base reaction force and torque.** The base is fixed, so what it absorbs
  is precisely what a drone would have to absorb instead. This is the input
  specification for the flight controller and is currently unknown — every catch
  number the project has is about the ball, none about what the catch does to the
  aircraft.

**Consequence: the envelope has three limits, not one** — what the HAND tolerates
before the ball escapes, what the ARM tolerates before joint torque exceeds a
buildable actuator (STS3215 class, ~55 g, ~19.5 kg·cm at 7.4 V; sim joint cap
0.6 N·m), and what the DRONE tolerates before the reaction exceeds its control
authority. **The adversarial game is bounded by whichever is tightest, and it is
not safe to assume that is the hand.**

**Validity guard, mandatory before a cell's numbers count:**
`n_contact_fingers > 0` **and** `score > 0`. Escape-margin alone cannot
distinguish a weak grasp from an absent one — both give small numbers, and the
blow-up cells produced perfectly well-formed numbers describing an empty hand.

### 3.6 Reference numbers

From the committed M5 regression log (`reg_arm_catch.txt`). `rel@hit` is the
relative velocity at contact **after** the absorption sweep has already run:

| launch vx / vz | rel @ hit | peak force |
|---|---|---|
| 3.3 / −3.2 (nominal) | **2.78 m/s** | 8.35 N |
| 2.5 / −2.0 | 2.15 m/s | 11.31 N |
| 5.5 / −4.5 (worst tested) | 4.64 m/s | 8.59 N |

So ~2.8 m/s is the number to design against, and 4.6 is the corner. It cannot go
much lower, for a geometric reason: the arm tip travels a **circle** and the ball
a **parabola**, so they are tangent only instantaneously — the window under
1.5 m/s is ~27 ms. That is why the project abandoned velocity-matching gates for
compliant capture: reduce what you can, then spread the rest over ~70 ms and
~10 cm.

## 4. Known sim-fidelity limits to carry ^4

- **There is no deformable body anywhere.** Compliance is modelled as (a) a
  penalty spring-damper at the contact interface (`contactStiffness` 1e4 N/m,
  `contactDamping` 3e2 N·s/m) and (b) lumped torsional springs at the joints in
  `yale_prb.actuate()`. PRB is a legitimate named method for flexures; it is *not*
  a model of a dished pad conforming to a ball. "Make the palm compliant" has
  exactly one knob here — contact stiffness — and that is the axis on which this
  study's results are least trustworthy.
- **`spin_arm(torque_cap=...)` is a current limit posing as mechanical
  compliance.** Per [[14-hardware-envelope|concepts/14]], no cheap hobbyist
  actuator back-drives. This is the same stand-in defect as `yale_hand.py`, one
  subsystem over — D9 has only ever been pointed at the hand.
- **No propwash model**, so any inter-rotor-corridor argument is design reasoning,
  not a sim result.
- `Drone.MASS = 0.625 kg` is the envelope's most at-risk parameter; realistic AUW
  is 900 g–1.1 kg, and a real hand is 150–250 g (actuator-driven) against the
  sim's implied ~12–16 g.

## 5. Protocol in force ^5

Earned during M-A and M-B. Not optional.

1. **Numbers trace to committed CODE**, not merely a committed log. Build the flag
   as you go — cheaper than retrofitting.
2. **Convergence includes the solver-iteration axis, and joint corners** — not
   one-axis-at-a-time.
3. **Video alongside stills**, in a non-rotating directory, with parameters in the
   filenames.
4. **Name falsifiers before running.**
5. **Scope claims to what was tested.** If a property is inferred from a structural
   difference rather than measured, say so in those words.
6. **Paired comparisons share declared numerics**, or the comparison states the
   difference.
7. **Evidence coverage attaches to a claim when it becomes DECISION-DRIVING**, not
   when its cell was planned.
8. **Uncovered-cell rule:** the evidence set must contain at least one element
   whose selection was independent of the hypothesis — naming the referent each
   time (independent of the *prediction*, the *scoring*, or the *design*).
9. **Brief-anchoring rule:** a gate brief states what to TEST and what would
   FALSIFY, never what the lead expects. Naming an untested *alternative* is
   allowed and valuable; stating a preferred *outcome* is not. The test: would the
   framing survive being read back to the gate after it reported?
10. **A grounded role that cannot state the mechanism from its own evidence
    reports UNDETERMINED**, not a verdict. (Watch item, adopted as practice,
    deliberately not promoted at n=1.)

### 5.1 The human's pre-registration — isolation and scoring ^51

The human recorded, before this experiment runs: *"a very simple hand with just
compliant material will be decently performative when doing the catch."*

**Keep this OUT of the worker's and the gates' contexts** per
[[grasp-goal2-loop-spec#^0|§0.3]]. It is the first time the isolation rule
protects a *human* prior.

**Scoring asymmetry, fixed in advance so nobody can adjust it after seeing the
envelope:**

- A **refutation** is strong evidence — a narrow envelope, in a design chosen to
  favour the mechanism, by someone who expected it to perform.
- A **confirmation** is weak by construction, and must never be written up as
  "human prior confirmed" unqualified.

**The limit of the isolation, which must be stated:** the human did not only state
the prior, they *designed the experiment* — point the hand along the approach
axis, drop the lateral probe. The prior is therefore encoded in the design, and no
context isolation can strip it out. Isolation protects the judges; it cannot
protect an experiment from the person who chose its shape.

## 6. RESOLVED — the hold-angle ruling ^6

**Ruling (human, 2026-09-22): NO vertical-hold condition.** The question largely
dissolved rather than being answered, because it rested on a wrong premise of the
lead's — that the dish contributes to retention. It does not; the cage does (see
[[#^3::§3]].3). Catch in the arrival-aligned pose, then let the arm return to its
natural carry pose with form closure retaining the ball. Do not put the arm under
sustained load to hold an attitude the cage makes unnecessary.

**A narrower real question survives, and it is already covered.** Between the ball
being arrested and the fingers closing — tens of milliseconds — the cage is not
yet firm. At ~46° with gravity on, does the ball roll toward the dish's rim before
the fingers arrive? That is a *capture* question, folded into the close-timing
variable; it means close timing matters more than first credited, and interacts
with dish curvature. No extra condition needed.

**Lead error recorded with the ruling**, because it recurred: having found that at
the nominal pose the contact force line passes near the elbow axis, the lead began
citing that as a design rationale. That is M-B's mistake again — a favourable
property of ONE point offered as a characterization, while the whole purpose of
the misalignment sweep is that the pose will not be nominal. Worse, if the load
path is benign only at 0°, joint torque grows exactly where robustness is needed.
Corrected by the human: *"our ultimate aim is an adversarial game, which means the
drone has to be robust even with error margins — it is only for now, constructing
an isolated experiment, that we give the hand such controlled situations."*
**The controlled setup is scaffolding, not the design target.**

---

*Historical — the superseded framing, kept because the reasoning is still the
record of how the ruling was reached.* (The human's hand-drawn pose that started
this is committed at `docs/agents/underarm-drawing.png`.)

The cup's two jobs want different angles. Aligned with arrival (~46°) is best for
absorbing the impact down the cup axis; **vertical** is best for gravity seating
the ball to the cup axis, because at 46° gravity pulls it to the dish's *downhill
rim* instead of its centre — which defeats the reason for adding the dish.

The differential/common-mode decomposition makes a change of cup angle cheap on
this arm: since the forearm's absolute angle is `a2 = θ1 − θ2`, the
**differential** sets cup orientation and the **common mode** sets cup position,
so orientation is controllable independently of position.

Three options, in the order they were considered:

1. **Two-phase pose, scripted** — meet the ball at ~46°, then rotate toward
   vertical for the hold, as a person does. Cheap if designed in, awkward to
   retrofit. Cost: it adds a *timing parameter* and a moving part to an
   experiment whose whole point is to isolate the hand — if a catch then fails,
   hand-failure and mistimed-rotation are not separable, which is the very
   attribution confound the fixed-base design exists to remove.
2. **Defer entirely** — hold at 46°. Cost: retention is then measured with
   gravity pulling the ball to the rim, i.e. **a configuration nobody would
   build.** That is the same error class as M-B's downward-facing cup.
3. **RECOMMENDED — make the hold angle a CONDITION, not a transition.** Run the
   catch at ~46°, then evaluate retention twice: once with the cup left at 46°,
   once reoriented to vertical. Two cells, no timing parameter, nothing moving
   during the catch.

Option 3 separates two questions the binary framing conflates: *does cup angle
matter for retention?* — a hand question, in scope here — and *can the arm
execute the transition in time?* — a control question, out of scope for a
fixed-base hand test and properly belonging to the drone milestone. If the two
conditions come out the same, the two-phase pose is unnecessary complexity we
avoided; if vertical is much better, we have quantified what the transition buys
before anyone builds it.

## 7. Roles and routing ^7

Unchanged from [[grasp-goal2-loop-spec#^1|§1]]. The worker runs one milestone and
stops; the lead routes through verifier → reviewer → critic; a failed gate routes
BACK, never forward. Gates get fresh context. The pre-registration is never passed
to verifier or reviewer; the lead runs the predicted-versus-observed diff after
the gates have scored blind. Escalate to the human only on
[[grasp-goal2-loop-spec#^4|§4]] triggers — notably anything requiring
physical-realism judgment, which this run confirmed is where human input is most
consequential.

**Method note worth carrying:** three of this run's deepest defects — the cup
facing downward, the baseline changing at the joint corner, and the placement
overlap — were each found by *looking at rendered frames*, and none by any gate
reading numbers. Every detector we have audits the EXECUTION of an experiment;
none audits its DESIGN. In pipeline terms, PROPOSE has no gate.
