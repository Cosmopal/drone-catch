---
tags:
  - concept
---

# Adaptive & underactuated grasping (and why a flying base changes the answer)

## What it is

Robust grasping under **position uncertainty** (you never know exactly where
the object is) is a solved-in-principle problem, and the key idea is:

> **Put the adaptation in the MECHANISM, not the controller.**

A position-controlled rigid hand servos every joint to a fixed shape, so it
assumes the object is where you expected — and shoves it out when it isn't
(see iteration_findings §21, the off-center ball "paddled out"). The field's
answer is **mechanical compliance + underactuation**:

- **Underactuated / tendon-driven hands** — one actuator drives many joints
  through a **differential (whiffletree)** + **compliant (flexure) joints**.
  Each finger closes until *it* contacts, then the shared tendon feeds travel
  to the fingers that haven't. The hand self-distributes around the object with
  no per-finger sensing. (Dollar & Howe, **SDM Hand**; the **Yale OpenHand**
  project — 3D-printable, fishing-line tendons, flexure joints.)
- **Structural compliance** — **Fin Ray** fingers (a flexing rib truss, printed
  in TPU) wrap *further the harder you push*; the compliance is in the plastic,
  no actuation needed to conform.
- **Caging** (Rodriguez, Mason & Ferry, *From Caging to Grasping*) — trap the
  object topologically *with clearance*, then optionally squeeze. Robust because
  it's a topological condition, not a precise-contact one. (Our "loose oval.")
- **Jamming / universal gripper** (Brown et al.) — a granular bag that conforms
  then vacuum-jams rigid. Maximally uncertainty-tolerant, but heavy + needs
  vacuum.

Force vs form closure and the inversion test are in [[09-grasping-caging-and-actuator-disturbance]].

## Where we use it / what we tried

`Drone.close_gripper(compliant=True)` implements the underactuated idea: a
**constant inward torque per joint + light damping, no target pose** (the
"tendon tension"), so each joint stalls on contact and conforms. Config
`finger_tau_close`, `finger_damp`.

## What we learned — the flying base changes the answer

Two findings, the second is the important one:

1. **A fixed-pose close shoves an off-center ball out**; the renders show 4
   fingers leave 66° diagonal gaps (~30% equator coverage). Geometry isn't the
   limit (the fingers are 2× the ball) — the *fixed-target close* is.

2. **Active underactuation (constant finger torque) DESTABILIZES a floating
   base.** On the drone, the compliant close pitched the body to ~90° (it
   flipped) — the sustained finger torques react on the airframe (Newton's
   third law, the [[09-grasping-caging-and-actuator-disturbance|§09]]/[[iteration_findings#^15|§15]] actuator-disturbance problem) and a position-PD close
   that reaches its target and stops applying torque doesn't have this; a
   *constant*-torque tendon never stops. A real Yale hand lives on a fixed arm
   that absorbs this reaction; a drone has nothing to absorb it.

**The transferable conclusion:** on a mobile/flying manipulator, the gripper's
own actuation reaction is a disturbance on the base. So **passive structural
compliance (Fin Ray) is strictly better than active underactuation (tendon)
for a flying catcher** — Fin Ray conforms with *zero actuation torque*, hence
*zero body reaction*, while a tendon hand's closing torque fights the flight
controller. If you do use an actuated underactuated hand on a drone, its
finger-reaction must be fed forward/countered like the arm-reaction FF.

## For larger projects

- **Adaptation belongs in the mechanism.** Trying to make a rigid hand conform
  by *control* fights the contact solver and the platform; compliant mechanics
  get it for free and are robust to the uncertainty that always exists.
- **On a mobile base, budget the end-effector's actuation reaction** as a base
  disturbance — it can flip a flying platform. Prefer *passive* compliance
  where you can; it has no reaction.
- **Test the gripper on a fixed base before coupling it to the moving system**
  ([[09-grasping-caging-and-actuator-disturbance|§09]]) — it separates "is the grasp mechanism right" from "does the platform
  survive the grasp." (We re-learned this the hard way.)

## Update — a trustworthy harness, and the correction that mattered

A deterministic fixed-base harness with a real form-closure metric (26-direction,
2.5 g disturbance battery; `tests/cage_harness.py`) was built to test these
claims. **Important correction (iteration_findings [[iteration_findings#^26|§26]]):** the first round used
RIGID contact at a 1/240 timestep, which made the OFF-CENTER verdict a
timestep-fragile artifact (light ~3-4 g RIGID fingers vs a 65 g rigid ball at the
capture boundary — a stiff mass-ratio contact; the 3-4 g finger mass is realistic
for a light print and is NOT the bug, making fingers heavier does not fix it). At
converged numerics — **compliant contact pads** (more physical) + a 1/960
substep — the picture is simpler than the bullets below
claimed:

- **The cage robustly captures off-center balls to ~3.5 cm in ALL directions,
  regardless of close strategy** (fixed, compliant, soft, and a proper
  underactuated/differential close all score ~1.0). The real capture limit is
  ~4.5 cm (gap direction ~1 cm weaker than toward-a-finger), beyond which NO
  strategy helps. So **compliance neither beats nor loses to the rigid close
  here** — at this offset scale the geometry just works.
- The literature's case for underactuation (adaptation in the mechanism) is about
  LARGER uncertainty and non-spherical objects; this sphere-to-3.5 cm regime
  doesn't stress it. The honest test would be a harder object set / larger
  offsets / the dynamic catch — not this one.

The original (rigid-contact) bullets are kept below for the record but are
**superseded** by the above:

- **Compliance did NOT beat the rigid close on this static metric — but it is
  under-credited, not refuted.** A force-limited "conform on contact" close and a
  soft-spring (Fin-Ray analogue, scored **zero — too soft to resist 2.5 g**) both

- **Compliance did NOT beat the rigid close on this static metric — but it is
  under-credited, not refuted.** A force-limited "conform on contact" close and a
  soft-spring (Fin-Ray analogue, scored **zero — too soft to resist 2.5 g**) both
  servo to the FIXED cage pose, so they can't adapt the SHAPE. A proper
  **underactuated/differential** close (low force toward a DEEP curl, each joint
  stalling on contact while the rest curl further) **does help the failure mode**
  — gap-offset 2.5 cm: **0.50 vs the rigid close's 0.00** — confirming the
  literature's claim that adaptation reaches an off-center object the rigid pose
  paddles out. It still loses overall because, in the **gravity-off** isolation
  (mandatory: the down-opening cup drops a ball under gravity before the close),
  an aggressive under-tuck *ejects* a centered ball upward with nothing to seat
  it. The fair test of underactuation is the **dynamic catch** (ball entering with
  downward momentum), not the static fixed-base metric.
- **Form closure here is a specific SHAPE, not just contact.** The validated cage
  (long proximal to the equator, middle+distal tucked under) is a tuned pose; a
  uniform constant-torque "tendon" close does not reproduce it (it balls up or
  paddles the object out). True underactuation needs a *differential*
  (whiffletree) to distribute travel correctly — one per-joint torque is not it.
- **The failure mode is the finger GAP** (an off-center ball escapes between
  fingers). A denser ring with a re-tuned close pose addresses it geometrically;
  an underactuated close addresses it adaptively (partially — see above). Both are
  open levers, not yet a clean win on the static metric.
- **The finger-reaction feedforward** (predict body torque from finger motor
  torques, pre-cancel — the arm-reaction-FF idea applied to the hand) is a clean
  **negative** on a flying base: in the arm-down pose the symmetric ring's motor
  torques sum to ~0, so the FF predicts ~0, while the actual disturbance is the
  *asymmetric finger-link inertial/contact* reaction the model can't see. The
  rigid winning close needs no FF anyway — on a level-holding (thrust-vectoring)
  body it disturbs pitch < 2.5 deg.

- **A FAITHFUL Yale hand (the COUPLING) was then built** (`src/yale_hand.py`,
  iteration_findings [[iteration_findings#^27|§27]]): a position-based tendon with the inter-finger
  whiffletree (one actuator = mean of finger travels; an early-contacting finger
  caps and feeds the rest) + intra-finger wrap-and-tuck + compliant joints. The
  self-distribution is **verified** (off-center -> per-finger angles differ
  sharply: near finger stalls, far fingers wrap more). But in sim it does NOT beat
  the rigid close: it loses the gravity-off static metric (anti-tuck bias), and on
  the dynamic catch it MATCHES at nominal (needs a FIRMER tendon tension than the
  rigid close to hold) and is marginally worse off-nominal. The Yale benefit is
  for real-hardware position/shape uncertainty this sim does not model.

Transferable: **measure the cage with a disturbance battery, not distance** —
and don't trust a compliance/FF win until a deterministic harness reproduces it.
And: **the mechanism can be right (coupling verified) yet show no benefit in a
sim that doesn't model the uncertainty it exists to absorb** — name that gap
rather than overclaiming the mechanism.

## Update — hold QUALITY, not just binary "caged" (iteration 2)

Binary "caged" (survives a disturbance battery) over-credits precarious holds — a
ball pinned by one off-center finger scores like a deep symmetric wrap. Iteration 2
adds CONTINUOUS quality metrics (iteration_findings [[iteration_findings#^28|§28]]): **escape-margin** (min
dislodging accel over all directions), **pull-in** (injected offset − residual
centering error — how much the close DRAGGED the ball to center), **rattle**
(residual motion under a sub-dislodging pulse), centering-err, #contact-fingers,
and azimuthal **contact symmetry**. Transferable lessons:

- **Pick a metric that can SEE the benefit you're evaluating.** "Is it caged?"
  (binary) cannot distinguish a rigid pin from an adaptive re-seat. **Pull-in**
  (does the close move the object toward the grasp center?) is that axis — it's
  where compliance/underactuation should win. A metric that just re-reports its
  input (a rigid close's centering-err ≈ the offset you injected) hides the effect.
- **Some quality metrics saturate.** Escape-margin is BIMODAL here (caged →
  cap, missed → ~0), so it confirms caging but can't grade precariousness within
  the cage — you need the graded signals (centering, symmetry, contacts) for that.
- **A "MORE than" claim needs a PAIRED, convergence-checked delta.** Our exciting
  result "the soft flexure re-centers the ball" was real — but a single cell's
  soft pull-in band (+0.70..+2.15 cm) OVERLAPPED fixed's (+0.03..+1.10 cm), so
  "soft beats fixed" was not earned there. Testing the **paired delta**
  (soft−fixed at the same perturbation) showed it convergently positive ONLY at
  low finger-count (n=4) / finger-direction / offset ≥2.5 cm, and straddling 0 at
  n=6/8 and in the gap direction. The honest verb is finger-count-dependent, not
  blanket. **Overlapping bands do not earn a comparative — pair-and-perturb.**
- **Determinism ≠ convergence, again.** Soft's escape-margin is a knife-edge
  (CONVERGED=NO: EM 2.5/10/7.97 g across timestep+seed) — the same [[iteration_findings#^26|§26]] artifact,
  caught by the gate this time. Only the pull-in SIGN (and only in the narrow
  convergent corner) is a trustworthy number.
- **The mechanism-fidelity trap (the one that bit us — see the iteration-2 redo
  below).** The [[iteration_findings#^28|§28]] "Yale convergently EJECTS the off-center ball" result was run
  on a **contact-reading STAND-IN** (`yale_hand.py` scripts the redistribution from
  `getContactPoints`) — not a mechanism, a puppet, and it fails the faithfulness
  test (does a finger stall because the *ball* is in its way, or because software
  told it to?). When a **faithful** pseudo-rigid-body hand (physical tendon, no
  contact reads) was built and re-scored, the verdict **reversed**: it cages *and*
  re-centers. **Before scoring a mechanism, prove it IS the mechanism** — evaluate
  a hand model on physics, not on a software abstraction wearing the hand's name.
- **Cross-check every number against a rendered frame, and verify the causal
  story before asserting it.** The soft "re-centering" first looked like a
  one-step snap (coarse sampling); a dense per-sim-step trace showed a gradual
  ~62 ms roll. The number was right; the *mechanism story* would have been wrong.

## Update — a FAITHFUL Yale hand reverses the verdict (iteration 2, Goal-1 redo)

The [[iteration_findings#^28|§28]] fixed-vs-Yale result above used a stand-in; Goal 1 was reopened to redo it
with a **faithful pseudo-rigid-body (PRB) mechanism** (`src/yale_prb.py`,
iteration_findings **[[iteration_findings#^29|§29]]**): flexure joints as torsional return springs + a
**constant-tension, distal-weighted tendon**, one actuator, and — the test of
faithfulness — **zero `getContactPoints` in the close law** (a finger stalls
because the ball is physically in its way; the rest keep closing under the same
tension, so self-distribution EMERGES). What changed:

- **The verdict flips.** The stand-in "ejected" the off-center ball (a puppet
  artifact). The faithful hand **cages it as robustly as the rigid fixed close**
  (4 fingers, 26/26, escape-margin ≥10 g) **AND re-centers it** in the finger
  direction — convergently (pull-in +1.3..+3.1 cm across 1.5-3.5 cm offsets,
  seating to <0.4 cm; CONVERGED=YES at every substep/contact/seed). It re-centers
  *more than fixed* (paired delta EARNED at n4-finger 2.5/3.5 cm and n6-finger).
- **Envelope, stated as tightly as the soft result.** Re-centering is earned only
  for **finger-direction** approaches at ring density **n4-n6**; it is honestly
  ABSENT in the **gap direction** (ball lands between two fingers — cages but
  nothing sits behind it to push it back) and at **n8** (too little per-finger
  travel budget for a differential). The coverage weakness is the SAME one the
  rigid close has, now shown to bound the adaptive hand's re-centering too.
- **A robustness win the binary missed:** the faithful hand's compliant close cages
  to ≥5 cm in *both* directions with a **timestep-STABLE** boundary — it escapes
  the [[iteration_findings#^26|§26]] artifact band (4-5 cm caged/escaped verdict that flips with the substep)
  that the rigid fixed/soft closes still sit in.
- **Numerical honesty of the fix:** the near-massless fingers need inertia
  regularization (×50) to be integrable; that scaling is proven **scale-invariant**
  (identical self-distribution at ×30/×50/×100), so it conditions the stiff ODE
  without manufacturing the result. Stated ceiling: fixed-base, spherical object,
  no continuous-flexure/true-tendon-friction/shape adaptation (a MuJoCo project).

Transferable: **an adaptive/underactuated hand's headline advantage (re-centering
an off-center object) is real but geometry-gated** — it needs a finger *behind* the
object to translate it, and enough per-finger travel to differentiate. And, again:
**mechanism claims must be scored on a faithful mechanism**, or you measure the
stand-in, not the physics.

## Buildable at home (sim2real)

- **Fin Ray fingers** — print in **TPU** (flexible filament; widely available,
  e.g. Bangalore FDM services), one servo to close. Lightest + most
  position-robust + no body reaction → best fit for a drone catcher.
- **Yale OpenHand** — open-source, 3D-printed links + fishing-line tendons +
  flexure joints; the canonical adaptive hand, but its active closing torque
  needs reaction budgeting on a drone.
- Sim caveat: PyBullet's rigid contact can approximate underactuation (constant
  torque + soft joints) and a discretized Fin Ray (multi-link soft chain), but
  not true continuous deformation or jamming — those need FEM.
