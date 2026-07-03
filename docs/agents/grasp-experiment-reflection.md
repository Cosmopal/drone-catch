# Reflection: the caging-robustness agent experiment (for loop-engineering study)

> **Purpose.** A holistic, honest record of the grasp-study sub-agent experiment,
> written for a *meta-agent* studying how to make AI agents self-sufficient on
> tasks like this ("loop engineering"). It documents what the agent was told,
> what it did, **where the loop failed to converge on its own and a human had to
> intervene**, and what that implies for structuring goal + validation so the
> loop converges autonomously. Written by the orchestrating agent (the main-loop
> "Claude" that spawned and supervised the sub-agent), at the user's request,
> including the user's stated concerns and the orchestrator's own self-critique.

## 1. Artifacts / pointers (read these for the raw record)

- **Sub-agent transcript (JSONL)** — the full sub-agent conversation, *including
  the user's direct messages to it and the orchestrator's spawn/continuation
  prompts*:
  `~/.claude/projects/-mnt-c-Users-Palash-Projects-robots-drone-catch/f1ce1eef-1e9e-4588-8d6f-776aa6e3fbf7/subagents/agent-a276c1c3e2d9858e9.jsonl`
  (meta: `…/subagents/agent-a276c1c3e2d9858e9.meta.json`)
- **Main conversation transcript (JSONL)** — the user ↔ orchestrator chat:
  `~/.claude/projects/-mnt-c-Users-Palash-Projects-robots-drone-catch/f1ce1eef-1e9e-4588-8d6f-776aa6e3fbf7.jsonl`
  **The grasp experiment is lines ~3653–4003 of 4003**: the user's "let's spin an
  independent agent" decision at **~3653**, the orchestrator's agent launch at
  **~3656**, the Yale-hand continuation at **~3872**, and the reflection request
  near the end. (Everything before ~3653 is the broader drone-catch session that
  led up to it.)
- **The agent's OUTPUT** (on its worktree branch `worktree-agent-a276c1c3e2d9858e9`,
  commit `1b6b312`, **not yet on main**): `docs/agents/cage-robustness-study.md`;
  `docs/iteration_findings.md §25/§26/§27`; `docs/concepts/13-...md`;
  `docs/cage_videos/README.md` + clips; `tests/cage_harness.py`; `src/yale_hand.py`.

## 2. The experiment — setup, goal, and the three roles

**The specific experiment** (a sub-problem of the broader two-drone "play catch"
project the agent already knows): *can the catcher's caging gripper reliably trap
a ball despite cm-scale uncertainty about where the ball actually is at contact?*
This had been the session's stuck point — many quick experiments gave
contradictory results — so the experiment's **first** job was to build a
*trustworthy measurement* of "is the ball caged," and only then study what
gripper / close-strategy improves it. Two nested goals: **(a)** a trustworthy
harness, **(b)** a finding about robust caging.

**The three roles:**
- **User (human director)** — owns the goal and the reality-check. Set direction
  and, crucially, *reviewed the rendered videos/frames* to catch when the metrics
  diverged from reality (the artifact, the wrong causal story, the poor hold
  quality). The load-bearing oracle (§4–5).
- **Orchestrator (this main-loop agent, "Claude")** — translated the goal into
  the agent's spec + gates, supervised, *independently verified* sub-agent claims
  before relaying, and relayed results to the user. Author of this doc. (Its
  gaps: §6/§8.)
- **Sub-agent** (`agent-a276c1c3e2d9858e9`, isolated git worktree) — did the
  build + experiments + docs autonomously over ~10 hrs of wall-clock and many
  turns. It self-corrected well *once triggered* but defaulted to trusting text
  metrics until pushed.

**What the files mean** (so the meta-agent can map them):
- `tests/cage_harness.py` — the trustworthy *measurement instrument* (deliverable a).
- `docs/iteration_findings.md §25→§26→§27` — the *running result log*; read in
  order to watch the result evolve: §25 first (wrong) finding → §26 correction →
  §27 Yale follow-up.
- `docs/agents/cage-robustness-study.md` — the agent's *own* status/summary.
- `docs/cage_videos/`, `docs/cage_frames/` — the *frame-level evidence* (the thing
  that unlocked the real insights; see §4.5).
- `src/yale_hand.py` — the faithful adaptive-hand model from the follow-up.
- `tests/cage_dynamic_catch.py`, `cage_drone_close.py`, `cage_drone_catch.py` —
  the on-drone / dynamic extensions.

## 3. The INPUT (what the orchestrator told the agent)

Three instructions over the experiment (verbatim in the sub-agent transcript):

1. **Spawn spec**: build a *trustworthy* fixed-base caging harness (prior quick
   experiments were noisy), study close-strategy × finger-count × ready-pose vs
   offset, then make the winning close work on the drone via a finger-reaction
   feedforward. Four gates: (1) harness self-validation, (2) beat the current
   close off-center, (3) on-drone pitch < 5° + full catch, (4) regression. *"A
   trustworthy negative beats a noisy positive."*
2. **Continuation — faithful Yale hand**: the first study tested crude stand-ins,
   not the real differential/whiffletree coupling; model it, prove
   self-distribution, evaluate on the corrected harness AND the dynamic catch.
3. **(User-driven, direct to the agent)** — slow-mo + HUD videos; the
   timestep/finer-frame questions that exposed the artifact; the finger-mass
   questions.

## 4. Where the loop failed to self-converge (the load-bearing human inputs)

Each was supplied by the *human*, not the agent or orchestrator — and each is
what actually moved the result toward reality.

### 4.1 Determinism was mistaken for trustworthiness (the artifact)
The agent's self-validation checked *determinism* + two *stable extremes*
(centered cage, far-outside escape). It passed; the orchestrator re-ran it and
called the off-center result "verified." But the off-center *band* was
ill-conditioned and the verdict **flipped with the timestep** — which neither the
gate nor the orchestrator's re-run tested. **Only the user's "finer frames?"
question** became the convergence check that exposed it. Lesson (§26):
*determinism ≠ convergence.*

### 4.2 The causal story was wrong and survived until video review
The agent shipped *rankings* with an attached *causal narrative* ("compliance
doesn't help; the gap is the failure mode"). Both wrong, both stated
confidently; it never tested the mechanism against the frames. **The user's video
review** forced the re-examination.

### 4.3 Hold QUALITY was never measured — by anyone (the user's image of a 1-finger hold)
The harness metric is **binary**: survive a 26-direction disturbance battery →
"caged" or not. A ball trapped by a single off-center finger in a precarious pose
scores the *same* as a deeply seated symmetric grasp. The user pointed to a frame
of a ball *barely held by one finger*; the obvious next step — fingers *adapting*
to re-center the grasp (sensing or algorithm) — was flagged by **neither the
agent nor the orchestrator**. The metric diverged from what a human sees as a
"good grasp," and nobody cross-checked metric against frame.

### 4.4 The validation tested a convenient proxy, not the real task
The harness is **static, gravity-off, fixed-base, single placement**. The real
task is a **dynamic catch of a ball arriving with velocity along a trajectory.**
The agent *knew* the static metric was biased (it said so) yet the loop still
treated it as the primary result. No sweep over ball velocity / approach angle /
catch pose vs incoming trajectory.

### 4.5 The agent trusted text metrics; only human-requested slow-mo + HUD video made reality legible
The agent's default output was scalar text (scores, PASS/FAIL). The corrective
insights came from **rendered video** — and specifically from the user *asking*
for **slow-motion** (the grasp is only ~0.64 s of sim, unwatchable at real speed)
and an on-screen **HUD overlay** (fingers touching, per-finger flexion,
displacement, HELD/ESCAPED). Those requests were the user's, not the agent's;
they were *required* to make the frames legible enough to review, and once legible
they unlocked what the numbers hid (the self-distribution made visible, the
artifact, the precarious holds). Left to itself, the agent neither instrumented
nor critically watched its own runs — it believed the table.

## 5. Systemic gaps

**In the agent:** metric coarseness (binary "caged," no quality dimension); no
convergence/sensitivity gate (only extreme-stability, not numerical convergence);
correlation shipped as causation; a cheap proxy accepted as the goal; default to
text over self-rendered, legible frames.

**In the orchestrator (me — equally important):**
- **Verification that re-ran the same flawed measurement** — I "verified" the
  off-center finding at the *same timestep*, which can only reproduce the
  artifact. Verification must *perturb* the method, not repeat it.
- **Did not watch the videos adversarially** — I *described* clips but accepted
  the agent's framing; never asked "does the held pose look robust?" The saved
  "examine frames, not just metrics" preference was not operationalized.
- **Did not push on completeness** — relayed the static study as near-final;
  didn't flag the missing velocity sweep or the hold-quality gap.
- **Was "satisfied" too early** — treated honest *negatives* + passing *gates* as
  sufficient, without asking whether the *gates* covered the goal.

## 6. Loop-engineering recommendations (preliminary — grounded in the failures above)

Throughline: **every human intervention was a "the metric doesn't match reality"
correction.** Autonomous convergence needs the *validation* grounded in the real
goal, and the *supervisor* to enforce that grounding.

1. **Operationalize the goal completely, up front.** Validation must cover the
   real use (dynamic catch × ball velocity/approach × **hold-quality** ×
   robustness), not a convenient proxy. A cheaper proxy (static harness) is a
   *scaffold*, never the acceptance criterion. (Fixes §4.4.)
2. **Frame-grounded validation as a hard gate — and the agent renders the frames
   *legibly by default*.** No scalar claim is accepted until cross-checked against
   rendered frames of the same run, *and the agent must proactively produce
   slow-mo + HUD-annotated views and review them* — not wait to be asked (§4.5).
   Add quality metrics matching human judgement (centeredness / # contacts /
   margin / symmetry), not just binary success. (Fixes §4.3, §4.5.)
3. **Convergence/sensitivity gate for any contact-rich sim.** Vary
   timestep/contact-model/seed; require the verdict to *converge* before it
   counts. Determinism is necessary, not sufficient. (Fixes §4.1.)
4. **Causal-mechanism gate.** A ranking ships with a mechanism explanation
   *verified against frames / an ablation*, not asserted. (Fixes §4.2.)
5. **Adversarial self-critique / completeness critic** before "done": the agent
   enumerates what it did *not* test and actively tries to break its own result.
6. **Supervisor checklist (the orchestrator's job).** Before relaying a result as
   a finding: *(a) completeness* — goal or proxy? *(b) metric-vs-frame
   consistency* — do the videos match the scores? *(c) convergence* — was the
   method perturbed, not repeated? *(d) causal soundness* — is the mechanism
   verified? "Honest negative + gates pass" is **not** the bar if the gates don't
   cover the goal. Default stance: **adversarial, not satisfied.**
7. **Capture the human-as-oracle signal as spec.** Everything the human caught —
   video-grounded quality, completeness, convergence, *making frames legible* —
   is the list of checks the loop must *internalize*. The design target is a
   supervisor that reproduces the human's adversarial review without the human in
   the chair.

**Direct answer to the user's question** ("how do I define this so a supervising
agent could guide it similarly?"): the human's guidance was always *grounding the
abstract metric in observable reality*. Encode that as the supervisor's
non-negotiable gates — goal-not-proxy, **legible-frame-grounding**, convergence,
causal-mechanism — and require the agent to produce the *evidence* (legible frames
beside scores, a convergence table, an ablation), not a summary. The supervisor
must assume the metric is lying until frame + convergence + completeness say
otherwise.

## 7. Orchestrator's defence / clarifications / possibly-missed perspectives

- **What did work.** The "trustworthy negative > noisy positive" framing in the
  spec was load-bearing — it's *why* the agent eventually overturned its own
  headline. The agent showed real epistemic virtue *once triggered* (retracted
  §25, flagged its own marginal Yale catch). The orchestrator caught some things
  unaided: corrected its own §24 overclaim when pushed, flagged the
  safety-classifier / API-error caveat and re-verified gates, and self-identified
  the Yale-hand spec gap. The harness, *as a tool*, is genuinely good — the
  failure was the **scope** of its metric, not its rigor.
- **A perspective worth adding.** The final conclusion ("in sim, compliance ties
  the rigid close; the benefit is for hardware uncertainty") is a statement about
  **sim fidelity**, not the mechanism. This sim injects only clean offsets +
  compliant rigid contact; it does *not* model the sensing/shape/actuation
  uncertainty adaptive hands exist for. So "compliance doesn't help" may be
  *unfalsifiable* here — a grasping loop should treat "can the testbed even *see*
  the benefit I'm evaluating?" as a first-class question, or it will confidently
  reject the right answer.
- **Honest bottom line on my role.** The user is right that I was too easily
  satisfied: my verification reproduced rather than perturbed; I didn't watch the
  videos adversarially; I didn't flag hold-quality or velocity-completeness. The
  single highest-leverage change to my own behavior: *never relay a sim metric as
  a finding without (i) a legible frame beside it, (ii) a convergence
  perturbation, and (iii) an explicit list of what the metric does not cover.*

## 8. Concrete next-step candidates this reflection surfaced (for the real study)

(Recorded; not yet done.)
- A **hold-quality metric** (centeredness, # fingers in contact, min contact
  margin, symmetry), cross-checked against frames.
- **Adaptive re-centering** of the grasp (sensing-/algorithm-driven finger
  adjustment) for off-center captures — the user's flagged obvious next step.
- A **dynamic** harness: ball velocity × approach angle × catch pose vs incoming
  trajectory, with form-closure + quality metrics applied at/after capture.
- Revisit whether the sim can model the uncertainty adaptive hands are *for*,
  else the compliance comparison stays unfalsifiable.
