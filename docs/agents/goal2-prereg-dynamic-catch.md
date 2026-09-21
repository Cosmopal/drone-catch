---
tags:
  - agent-loop
---

# Pre-registration — dynamic axis-aligned catch milestone

> **SEALED.** Written by the LEAD 2026-09-22, **before any build or run**, per
> [[grasp-goal2-loop-spec#^0|§0.3]]. **Never pass this file, or any content from
> it, to the worker or to any gate.** Anchoring in LLM judges survives explicit
> "disregard this" instructions. The lead runs the predicted-versus-observed diff
> as a separate step AFTER the gates have scored blind.
>
> The human's own prior is recorded separately in
> [[grasp-dynamic-catch-spec#^5|§5.1]] of the spec with its asymmetric scoring
> rule, and is likewise sealed. **These predictions are the lead's own and were
> formed without reference to it.**
>
> Design under test: [[grasp-dynamic-catch-spec|grasp-dynamic-catch-spec.md]].

## What the priors rest on

Three in-project precedents, none of them this experiment:

- **M5 / `arm_catch_solo`** — compliant capture held **12/12** at contact
  relative velocities to 4.6 m/s. But it used a *soft constraint stand-in*, not
  the physical cage. Its success is weak evidence here.
- **M8 ([[iteration_findings#^15|§15]]) / `elbow_catch_solo`** — the *physical*
  cage on a *moving* ball punched through at ~2.3 m/s before the fingers firmed.
  **SUPERSEDED — do not anchor on this.** (The lead's first draft did, having
  failed to read four sections forward; recorded because it is exactly the
  provenance failure our own rules exist to prevent.)
- **M8b ([[iteration_findings#^16|§16]]) — the current and most relevant
  precedent.** Pre-positioning landed the *first retained physical catch*, and
  re-diagnosed the failure mode: **"the ball seated at the cup RIM (~3 cm
  off-center), not the center. The static cage held through inversion + lift; a
  rim-seated ball gets only partial form closure → it works loose in ~1 s and any
  acceleration ejects it."** Also: firming the grip to 2.0 N·m produced
  **100–166 N** contact forces on a 0.64 N ball, and a lift jolted the rim-seated
  ball out.
  **Rim seating is precisely what a dished palm targets**, so the intervention
  under test addresses the documented failure rather than a stale one.
- **M8c–M8e ([[iteration_findings#^17|§17]]–[[iteration_findings#^19|§19]])** —
  the cage catch is noise-fragile; the arm's snap into tracking is intrinsic
  (three fixes all broke the catch); velocity-matching infrastructure exists
  (`arm_kinematics.jacobian`, `ik_velocity`, joint-velocity feedforward in
  `hold_arm`) but naive use did not improve the catch; and the arm runs at
  **84–93% extension** through the approach, near the Jacobian singularity, with
  an IK that models nothing for staying folded, for compliance, or for trajectory
  overlap. **§19 already tried the folded-arm-absorbs-momentum idea and hit that
  wall** — relevant because the fixed-base design here removes the tracking IK
  entirely, which is the thing that was forcing near-full extension.
- **M6 / `finger_catch_solo`** — cages a ball *placed* in the cup; the in-flight
  catch was unreliable at ~7–10 cm rendezvous miss (a delivery failure, removed
  by the fixed base here).

So the physical cage *has* caught and retained a moving ball, but only at nominal
conditions, and its diagnosed weakness is **seating quality**, not raw speed.

## Predictions

**P1 — The binding failure is RIM SEATING, not punch-through, and it degrades
with speed.**
§16's retained catch failed earlier attempts because the ball came to rest ~3 cm
off-centre at the cup rim, giving only partial form closure. Predict: **seated
offset grows with approach speed**, and the ball reaches the rim region
(≳2 cm off-centre) at 4.0 m/s even at 0° misalignment / 0 miss — with retention
failing where seating does, not independently of it.
*Falsifier:* seated offset flat across speed, or retention failing while seating
stays central (which would mean the failure is a different mechanism and the dish
is aimed at the wrong thing).
*Confidence 0.6. Provenance: analogy* — §16's rim-seating diagnosis, same physical
hand, but that run had no dish and a tracking arm rather than a fixed base.

**P2 — Close timing dominates misalignment.**
If capture is a race, then *when* the close is triggered relative to arrival
should matter more than the geometry of approach. Predict: within a fixed cell,
sweeping close timing changes the capture outcome more than sweeping misalignment
0° → 20° does.
*Falsifier:* misalignment changes outcome more than timing does.
*Confidence 0.5 — a genuine guess, and the weakest prediction here.*

**P3 — Toward-gap misalignment is worse than toward-finger.**
The tangential velocity component drives the ball toward an escape route between
fingers; toward a finger it is blocked. Predict: at matched magnitude, capture
rate for gap-azimuth < finger-azimuth.
*Falsifier:* gap ≥ finger, or no azimuth difference at all.
*Confidence 0.7. Provenance: geometry.*

**P4 — Peak elbow torque is near zero at 0° misalignment and rises with angle.**
`τ = r × F`: at 0° the contact force line runs down the forearm and passes near
the elbow axis. Predict monotonic rise 0° → 30°, at least 3× over that range.
*Falsifier:* torque flat across misalignment, or highest at 0°.
*Confidence 0.65. Provenance: geometry.*
**Flagged deliberately:** this is the exact claim the lead was cautioned against
leaning on as a design rationale. It is therefore *predicted and measured*, never
assumed. **If it comes back flat, the "benign load path" reasoning was wrong from
the start** — which would be the more useful outcome.

**P5 — Lateral miss tolerance is ~2 cm, geometrically bounded.**
The splayed mouth is ~10 cm across against a 6 cm ball, leaving ~2 cm clearance
per side before the ball strikes a finger rather than entering. Predict sharp
degradation between 1.5 cm and 3.0 cm.
*Falsifier:* clean capture at 3.0 cm, or failure at 1.5 cm with all else nominal.
*Confidence 0.7. Provenance: geometry.*

**P6 — Adverse corners fail where each single axis survives.**
Per M-B's joint-corner lesson, expect super-additivity. Predict at least one
corner cell fails where every individual factor at that same level succeeded.
*Falsifier:* all corner outcomes predictable from the single-axis results.
*Confidence 0.6. Provenance: analogy* — M-B's (substep 8 × contact ×0.33) corner.

## Explicitly NOT predicted

**Base reaction force and torque.** No prior exists — the project has never
measured what a catch does to the airframe. This is genuinely exploratory, and any
number is new information. Recording the absence of a prior so that whatever comes
back cannot later be narrated as expected.

## Uncovered cell (independence referent: the DESIGN)

At least one cell at **45° misalignment** and **5 cm lateral miss** — outside
every prediction above and outside the range the design was shaped to favour. It
exists so the envelope has an edge capable of embarrassing the priors, including
the lead's. Per the standing rule, the evidence set must contain at least one
element whose selection was independent of the hypothesis.

## Scoring

Per [[grasp-goal2-loop-spec#^0|§0.3]]: a **violated** prediction raises scrutiny
and must be investigated before the result is reported either way; a **confirmed**
one lowers nothing and still faces the full verifier and reviewer gates. A wrong
prior can be spuriously confirmed.

Note the shape of this set: it is **mostly pessimistic**. That makes confirmation
cheap and refutation informative — the reverse of the usual asymmetry, and worth
stating so the diff is not read as a success when the hand simply outperforms a
cautious guess.

Per the standing worker instruction: if a result violates a pre-registered
expectation, a dated note is committed **before** any follow-up run or
reconciliation, so the ordering is auditable rather than asserted.
