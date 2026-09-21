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
- **M8 / `elbow_catch_solo`** — the *physical* cage on a *moving* ball: 2/12 on
  the grid, and the documented failure is that **the ball punches through at
  ~2.3 m/s relative before the cage firms**. This is the most directly relevant
  number the project has, and it is a negative precedent.
- **M6 / `finger_catch_solo`** — cages a ball *placed* in the cup; the in-flight
  catch was unreliable at ~7–10 cm rendezvous miss (a delivery failure, removed
  by the fixed base here).

So the physical cage has **never** reliably caught a fast-moving ball. The priors
below are correspondingly cautious, and deliberately so: if they are wrong in the
optimistic direction, the dish and axis-alignment are doing real work.

## Predictions

**P1 — Speed is the dominant limit; the cage punches through above ~2.5 m/s even
at perfect alignment.**
Capture is a race between the ball arriving and the fingers closing. Axis
alignment and a dished palm change *where the ball goes*, not *how fast the
fingers close*. Predict: 1.5 m/s captures and retains at 0° / 0 miss; **4.0 m/s
does not capture at any misalignment**; 2.8 m/s is marginal.
*Falsifier:* capture and retention at 4.0 m/s, 0°, 0 miss.
*Confidence 0.6. Provenance: analogy* — M8's 2.3 m/s punch-through, same physical
hand, different pose, no dish.

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
