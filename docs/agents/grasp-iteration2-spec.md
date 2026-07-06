# Grasp study, iteration 2 — worker + reviewer loop spec (DRAFT for review)

> **⚠️ GOAL 1 REOPENED (mechanism-fidelity defect).** The "Yale" hand scored in the
> first Goal-1 pass (`src/yale_hand.py`) is **not** a faithful Yale OpenHand — it is
> a *contact-reading position-budget redistributor* (reads `getContactPoints`, splits
> a software "flexion budget" via a computed mean) bolted onto the existing rigid
> 4-finger × 3-segment caging gripper. It lacks the three things that make the real
> hand adaptive: continuous flexure compliance, a **physical** tendon/pulley +
> whiffletree, and Yale's co-tuned geometry; it was only ever tested on a sphere.
> Its docstring mislabels it "Faithful." So the "Yale ties the rigid close" verdict
> is **unreliable** — it may reflect a poor model, not the mechanism. Goal 1 is
> reopened: build a **faithful** pseudo-rigid-body Yale-style hand (§2A), prove it is
> real before scoring, redo the fixed-vs-Yale re-score, and re-gate. Do **not**
> re-close Goal 1 until the reviewer re-approves against the new mechanism-fidelity
> detector (§3, D9) with regressions still green. The soft/compliant/fixed Goal-1
> results already approved stand; only the Yale arm of the comparison is invalidated.

> Seeds a fresh `/goal`-driven session. The session **lead** reads this, spawns a
> **worker** teammate and an independent **reviewer** teammate, and coordinates
> them until the `/goal` condition (§5) is met. Builds on iteration 1; read
> `docs/agents/grasp-experiment-reflection.md` first (what went wrong and why),
> and the iteration-1 outputs on worktree branch `worktree-agent-a276c1c3e2d9858e9`
> (the trustworthy harness `tests/cage_harness.py`, `iteration_findings §25-27`).

## 0. Framing (from project memory — keep these honest)
- **Engineering, not science.** The goal is to *characterize the practical limits*
  of robust caging and *apply known grasping principles* (caging/form-closure,
  Yale-style underactuation, Fin-Ray compliance), **not** invent a novel
  algorithm. Success = a trustworthy, frame-grounded characterization + the best
  known-principle close, with limits stated.
- **General detectors, not a failure map.** The reviewer's rubric (§3) is a set of
  *domain-general* checks ("does the result look as good as the number says?",
  "was it convergence-checked?"), not a list of specific pre-enumerated failures.
  Add a **ratchet**: once a failure class is found, it becomes a standing check;
  checks only tighten.

## 1. The goal (operationalized)
Characterize, with trustworthy + frame-grounded evidence, how robustly the
catcher's caging gripper can **trap AND well-seat** a ball under cm-scale
position uncertainty — and deliver the best close strategy among known principles,
with its limits. "Well-seat" is first-class: a ball trapped by one off-center
finger is **not** a success even if it survives a disturbance battery.

## 2. The worker's task + deliverables (each exists to satisfy a §3 detector)
1. **Add a continuous hold-QUALITY metric** to `cage_harness.py` (the binary
   "caged" over-credits precarious holds — iteration-1's core miss): report
   **escape-margin** (min disturbance accel over all directions, not pass/fail at
   a fixed g), **centeredness** (ball-center↔cup-center), **# fingers in
   contact**, and **contact symmetry**. Keep the existing form-closure battery as
   one input.
2. **Re-score the existing strategies on quality** (fixed / compliant / soft /
   Yale-underactuated), per offset × direction × finger count. *Explicit question:
   does the fixed-vs-Yale verdict change once quality is visible?* (iteration 1
   found a binary "tie"; quality is the dimension where adaptive hands should win
   — the redemption test.)
3. **Convergence-check every contact-rich result** (vary timestep + contact model
   + seed); a result without a convergence table does not count. (Determinism ≠
   convergence — the iteration-1 artifact.)
4. **Render legible review frames by default** — slow-mo + HUD-annotated key
   moments (close, seated, post-disturbance) — and **cite a frame beside every
   number.** Do not report a metric without its frame.
5. **Adaptive re-centering (the user's flagged next step):** prototype a close
   that *adjusts* for an off-center ball (sense which fingers contact → re-seat /
   re-close, or the mechanical whiffletree), and measure it on the quality metric
   vs the rigid close.
6. **Layered dynamic test (kept SEPARATE from the static study):** ball velocity ×
   approach angle × catch pose vs incoming trajectory, quality metric applied at
   capture. Static harness answers "is the cage good?"; dynamic answers "can the
   catch deliver into it?" — so failures stay attributable. (Dynamic full-TV catch
   is gated by the §20 tracking instability; use the scoop catch if needed and
   say so.)
7. **An explicit "what I did NOT test" list** in the findings.
8. **Regression unchanged** + everything additive/opt-in.

## 2A. REOPENING — faithful Yale hand + redo of the fixed-vs-Yale Goal-1 arm
This supersedes the Yale portion of §2.2. Everything additive/opt-in on the worktree
branch; be explicit that the model is a **discretized approximation with a stated
ceiling** (not the real compliant hand).

**Build a faithful pseudo-rigid-body (PRB) Yale-style hand** — the accepted way to
sim compliant/underactuated hands:
- **Flexure joints** modeled as multi-segment revolute chains with **per-joint
  torsional return springs** (τ = −kθ − cθ̇), not rigid pinned box segments.
- A **physical tendon/differential** — self-distribution must emerge from the physical
  mechanism, NOT from a contact-reading algorithm. **NOTE (physics correction):**
  `JOINT_GEAR` is the WRONG primitive here — it enforces a rigid kinematic ratio
  (θ_a = k·θ_b), forcing fingers to move *equally*, the OPPOSITE of a differential. A
  real whiffletree is **constant-TENSION** (equal force per branch via a floating
  balance bar); the redistribution comes from force equalization, not a fixed ratio.
  Faithful options: (a) a **constant-tension tendon** — equal closing torque per finger
  driven to a common actuator ramp, no `getContactPoints` anywhere, so a blocked
  finger stalls and free fingers keep moving under the same tension; and/or (b) a
  **physical floating balance-bar (whiffletree) link** coupled by point/prismatic
  constraints so force equalizes mechanically.
- **Honest-negative is a valid outcome.** Constant-tension/torque tendons on these
  ~3–4 g fingers are exactly what §25 found numerically ill-conditioned (Coulomb-like
  joint thresholds, frozen distal joints, body flips) — which is *why* the prior author
  retreated to the contact-reading model. It may now be viable under the §26 converged
  numerics (compliant pads + 1/960 substep); it may not.
- **A negative requires a DIAGNOSIS, not just "it didn't converge" (user criterion).**
  Before any honest-negative, classify the cause with evidence:
  - **Hardware-config** (finger mass, joint friction/damping/stiffness, actuator ramp
    rate, pad stiffness, substep) — these are TUNABLE. You must exhaust them (heavier
    fingers, tune joint params, slower ramp, finer substep) and get a working model.
    Do NOT report a negative that is really just untuned fingers.
  - **Sim-fundamental** — PyBullet structurally cannot hold a constant-tension
    equilibrium on light links *regardless of tuning* (no native tendon primitive,
    contact solver can't represent it). ONLY THEN is the negative legitimate → state it
    as the model's ceiling (a true tendon differential belongs in MuJoCo).
  Never force a broken model to "work," and never fall back to a scripted contact-reading
  stand-in and call it faithful. Report which category, and what tuning was tried.
- **Compliant contact pads**: `changeDynamics(contactStiffness/contactDamping)`.
- **Geometry**: prefer Yale's published geometry (Model O STL→URDF) if tractable;
  else a geometry chosen for adaptive grasping — **state which** and why.

**Two hard constraints (state them, honor them):**
- (i) **Fixed-base harness ONLY.** The extra flexure joints are unstable on the
  floating drone (see §15 finger-on-floating-base instability). Do not put this hand
  on the drone.
- (ii) **Shape-adaptability is OUT OF SCOPE**, and PyBullet is the wrong tool for it
  (no continuous compliance, no native tendons — that is a MuJoCo project). **Test the
  sphere only; do not claim shape adaptation.**

**Prove the model is real BEFORE scoring it** (each with cited frames):
1. The **flexure fingers conform continuously** to the sphere — the chain wraps more
   than 3 rigid segments would (cite frames showing the wrap).
2. **Self-distribution emerges from the physical coupling, not from reading contacts**
   — with the `JOINT_GEAR`/whiffletree constraint alone (no contact-reading logic),
   per-finger angles come out **unequal off-center**. Show it.
3. **Fix the misleading "Faithful" docstring** in `src/yale_hand.py` to describe
   exactly what that (old) model is; the new faithful hand lives in its own module.

**Redo the Goal-1 fixed-vs-Yale arm with the faithful hand:**
- Re-run the quality re-score (escape-margin + centeredness + #contacts + symmetry)
  for **fixed vs faithful-Yale** across offset × direction × finger count,
  convergence-checked (timestep + contact + seed), legible frame beside every number.
- **Headline question (the real redemption test):** does the fixed-vs-Yale verdict
  change now that the hand is faithfully modeled?
- **Re-gate:** the reviewer must re-approve the redone Goal 1 against the
  mechanism-fidelity detector (§3 D9), and the regression gates (`arm_catch_solo
  --grid` 12/12, `elbow_catch_solo` caught=True held=True) must still pass. Goal 1
  does not close until that approval exists.

## 3. The reviewer's rubric (independent, multimodal, adversarial — domain-general detectors)
The reviewer judges **only from the worker's outputs** (rendered frames + claims +
committed numbers); it does not re-run experiments to rationalize. For every
reported finding it applies these *general* detectors and must **cite the specific
frame(s)** for each concern:
- **D1 claim↔frame consistency** — does a cited frame visually support the claim?
  ("caged" → a secure multi-finger wrap, not a one-finger graze.)
- **D2 quality-vs-success** — does a "success" *look* well-seated (centered,
  multiple fingers, margin), or marginal/precarious? Reject precarious "successes."
- **D3 convergence** — is there perturbation evidence (timestep/contact/seed) for
  any contact-rich claim? No table → reject.
- **D4 completeness** — does the validation cover the stated goal (quality +
  dynamic + velocity) or a convenient proxy? List untested dimensions.
- **D5 causal soundness** — is any "why" claim verified (ablation/frame) or merely
  asserted?
- **D6 sim-fidelity / falsifiability** — can the testbed even *see* the benefit being
  evaluated? Reject a claim the sim structurally cannot falsify unless it is labeled
  as a testbed-regime limitation (e.g. "Yale ejects in the gravity-off free-ball
  regime" ≠ a mechanism verdict).
- **D7 static-vs-dynamic attribution** — static-harness claims and dynamic-catch
  claims must stay strictly separate and not be conflated.
- **D8 frame-coverage** — are there frames from multiple timepoints AND multiple
  camera angles for each verdict-bearing cell? If coverage is insufficient to judge,
  DEMAND the specific missing renders rather than approving on faith.
- **D9 mechanism fidelity** *(standing ratchet — added after the yale_hand.py stand-in
  defect)* — is the mechanism under evaluation **faithfully implemented**, or a
  stand-in? A **behavioral abstraction on unrelated geometry does NOT count as testing
  the mechanism** (e.g. a contact-reading software budget-redistributor is not a
  physical tendon/whiffletree/flexure hand). A "faithful" claim must be backed by
  frames of the actual mechanism doing the thing (continuous flexure conformance;
  self-distribution from the *physical* coupling, not from reading contacts).
- **Provenance ratchet** *(standing — added after §28)* — every quantitative figure
  in the findings must trace to a committed log AND reconcile with the other committed
  logs; no orphaned or contradictory number.
- **Ratchet** — maintain a running checklist; any new failure class found becomes a
  standing detector for the rest of the run.
The reviewer outputs, each milestone: `REVIEWER VERDICT: APPROVED` **or**
`REVIEWER VERDICT: REVISE` + a numbered list of concerns, each with a cited frame
and which detector it fails. It only APPROVES the *final* findings when all
detectors pass.

## 4. Team structure
- **Lead (the session)** — owns the `/goal`, spawns the two teammates, relays the
  reviewer's flags to the human, does NOT mark work done itself.
- **Worker teammate** — §2. Renders legible frames; never self-approves.
- **Reviewer teammate** — §3. Independent (no part in producing results), reads
  frames, gatekeeps. The human audits the reviewer's flags, not the raw videos.
- Worktree-isolated; additive; conda `robots`.

## 5. The `/goal` completion condition (what the human types)
Kept crisp + demonstrable (the reviewer's rubble of detail lives in §3, so the
condition only checks the reviewer's verdict + the regression):

```
/goal the reviewer teammate has posted "REVIEWER VERDICT: APPROVED" on the final
findings, AND the transcript shows `arm_catch_solo.py --grid` printing 12/12 and
`elbow_catch_solo.py --headless` printing caught=True held=True
```

(`/goal` re-checks after each turn and keeps the loop running until met; `/goal`
alone for status, `/goal clear` to stop. Optionally add a `TaskCompleted` hook so
the worker cannot close a task without the reviewer's APPROVED.)

## 6. Open questions for the human before launch
1. **This session or a fresh one?** (Lead recommends fresh, seeded by this doc.)
2. **Scope of v1:** do §2.1–2.4 (quality metric + re-score + convergence + frames)
   first and gate, *then* §2.5–2.6 (adaptive + dynamic) as a second goal? Or all in
   one `/goal`? (Lead recommends the two-stage gate — smaller, auditable.)
3. **Hooks now or later?** (Lead: start without; add `TaskCompleted` only if the
   worker tries to self-approve.)
4. Anything to add to the reviewer rubric (§3) that *you* would check?
