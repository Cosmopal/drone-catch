---
tags:
  - agent-loop
---

# Loop-engineering analysis: what the grasp-study experiment teaches about autonomous AI loops

> A meta-analysis written for the experiment's stated goal — *learn how to make AI
> agents self-sufficient on long-running build/measure tasks*. It reads the
> caging-robustness sub-agent experiment ([[grasp-experiment-reflection|grasp-experiment-reflection.md]],
> `cage-robustness-study.md`, [[iteration_findings|iteration_findings.md]] [[iteration_findings#^23|§23]]–[[iteration_findings#^27|27]]) against the
> 2023–2026 literature on agent loops, evaluation failure, self-verification, and
> agent memory. Companion to the reflection doc, which is the primary record; this
> doc is the *analysis + design proposal*. Citations are inline.

## 0. The case in one paragraph ^0

A sub-agent was told to build a *trustworthy* harness for "can the gripper cage a
ball under cm-scale position uncertainty," then study what improves it. It built a
genuinely good measurement instrument, self-validated it (determinism + two stable
extremes), and shipped a confident result with a causal story ([[iteration_findings#^25|§25]]: "the gap is the
failure mode; compliance doesn't help; soft scores zero"). Then — prompted by a
human's slow-mo-video request that became a finer-timestep check — it discovered
the entire off-center finding was a **rigid-contact numerical artifact** that flips
with the timestep; at converged numerics almost every [[iteration_findings#^25|§25]] conclusion evaporated
([[iteration_findings#^26|§26]]). It then built the *faithful* Yale adaptive hand, verified the mechanism
works, and honestly concluded it ties/loses in sim — because **the sim cannot model
the uncertainty adaptive hands exist for** ([[iteration_findings#^27|§27]]). Every course-correction was
human-triggered. The agent's failure and the orchestrator's failure were the same
shape: *trusting a scalar metric that had drifted from the real goal, and verifying
by repeating the measurement rather than perturbing it.*

---

## 1. Patterns and characteristics of the agent's behavior ^1

1. **Epistemic virtue on demand, not on initiative.** The agent self-corrected
   *excellently* once triggered (it retracted its own headline in [[iteration_findings#^26|§26]], flagged its
   own marginal Yale catch in [[iteration_findings#^27|§27]]). What it could not do was *generate the trigger*
   — spontaneously doubt a result that had passed its own gates. The autonomy gap
   is specifically **the initiative to distrust a passing measurement.**
2. **Scalar text as ground truth; rendered frames as output-for-human, not
   input-for-self.** Default deliverable was a PASS/FAIL table. Video existed but
   was treated as something to hand the user, never as evidence to analyze.
3. **Confident causal narrative attached to correlational data.** [[iteration_findings#^25|§25]] shipped
   *rankings* (correlation) with an asserted *mechanism* ("compliance doesn't
   help") that was never tested against the frames or an ablation — and was wrong.
4. **Documented-then-ignored bias.** The agent *wrote down* that the static,
   gravity-off harness was biased against the dynamic catch — and then used it as
   the primary result anyway. Knowing a proxy is biased did not stop it from
   trusting the proxy.
5. **Self-validation that covers the easy extremes.** The Phase-0 gate tested a
   centered cage (always holds) and a far-outside ball (always escapes). Both
   passed — and certified *nothing* about the ill-conditioned off-center band that
   was the actual object of study. A green self-test gave false confidence.
6. **Determinism mistaken for trustworthiness.** Same config → identical score was
   read as "the measurement is sound." It was reproducible *and wrong*.
7. **The orchestrator failed the same way.** It "verified" the off-center result by
   **re-running it at the same timestep** — which can only reproduce the artifact.
   *Verification by repetition is not verification.* It also described the videos
   instead of watching them adversarially. Adding a supervisor layer did not help,
   because the supervisor's checks repeated rather than perturbed.

---

## 2. Limitations — and which are fundamental vs. fixable ^2

| Limitation | Fundamental (model-level) | Fixable (loop-level) |
|---|---|---|
| Reads still frames; does not *watch motion* | partly — VLM temporal grounding is genuinely weak (arXiv 2508.10922) | feed targeted keyframes at the contact instant, A/B not scalar scoring |
| Doesn't spontaneously doubt a passing result | yes — error *detection* is the weak point (Tyen 2023; Huang 2023) | **manufacture the doubt mechanically** (convergence/falsifiability/completeness gates) |
| Optimizes whatever is measurable | yes — causal Goodhart is structural | ground the metric in the real goal; validity ledger |
| Verifies by repeating | no | mandate *perturbation*; separate generator from verifier |
| Confident on miscalibrated claims | partly — verbalized confidence is miscalibrated | require a falsifier + confidence tag per claim; score calibration over time |

The load-bearing reframe: **the binding constraints are at the loop level, not the
model level.** The model's detection weakness is real, but the experiment shows the
agent *can* detect and correct once a perturbation surfaces the problem. So the
design job is to **make the loop produce the perturbations a skeptical human would**
— not to wait for a smarter model.

---

## 3. Reproduced findings — this session is a textbook convergence of four literatures ^3

The single most important answer to "do others' findings show up here?": **yes,
and almost everything that went wrong is a named, published failure mode.**

| What happened here | The published finding it reproduces |
|---|---|
| Agent couldn't self-trigger the [[iteration_findings#^26::§26]] correction; needed the human's frame question | **"LLMs Cannot Self-Correct Reasoning Yet"** (Huang et al., DeepMind, ICLR 2024, arXiv 2310.01798) — *intrinsic* self-correction without external feedback often *degrades*; gains require an oracle. |
| Human *pointing at the frames* flipped the result cheaply; the fix was easy once located | **"LLMs cannot find reasoning errors, but can correct them given the location"** (Tyen et al., ACL 2024, arXiv 2311.08516) — the bottleneck is *detection*, not repair. |
| Reproducible metric, causally disconnected from the goal ([[iteration_findings#^26::§26]] timestep artifact) | **Causal Goodhart** (Manheim & Garrabrant 2018, arXiv 1803.04585); the broader specification-gaming canon (Krakovna 2020; Lehman et al. 2018 — optimizers exploit *simulator bugs*). |
| Sweeping many strategies against a flawed metric; "rising score" ≠ rising goal | **Reward misspecification phase transitions** (Pan, Bhatia, Steinhardt, ICLR 2022, arXiv 2201.03544) — proxy rises while true objective drops, discontinuously. |
| Confident causal story that was never tested | **Sycophancy** (Sharma et al., Anthropic 2023, arXiv 2310.13548) + verbalized-confidence miscalibration — training rewards plausible, agreeable narratives. |
| Binary "caged" hides a precarious 1-finger hold ([[grasp-experiment-reflection#^4::§4]].3 of the reflection) | **Construct invalidity & distribution-hiding** (Raji et al., NeurIPS 2021, arXiv 2111.15366; HELM "report the distribution"); your own [[iteration_findings#^23::§23]] memory ("scalar metrics hide failure modes") is this principle, independently rediscovered. |
| [[iteration_findings#^27::§27]]: the sim *cannot express* the compliance benefit → comparison unfalsifiable | **The reality gap / construct validity** (sim-to-real surveys, arXiv 2510.20808) — a metric is only valid for phenomena the testbed represents. Your CLAUDE.md already says it ("PyBullet can't test the wash claim"). |
| Orchestrator "verified" by re-running identical config | Inverse of **self-consistency** (Wang et al., ICLR 2023, arXiv 2203.11171) — *diversity across attempts* is the active ingredient; identical resampling adds nothing. |

The meta-point: **none of this required a new discovery to predict.** A loop wired
with the field's known correctives would have caught most of it without the human.
That is the encouraging finding — the gaps are addressable with known techniques.

---

## 4. What's needed to increase autonomy — loop engineering ^4

"Loop engineering" / "harness engineering" is now a named discipline (Simon
Willison, "Designing agentic loops," Sep 2025; Addy Osmani, "Agent Harness
Engineering," 2025), downstream of "context engineering" (Anthropic, Sep 2025). The
core claim: *the harness — the loop structure, the available checks, the grounding
signals — determines reliability more than the prompt.* Here is the loop this
experiment argues for.

### 4.1 The outer loop as gated stages (a failed gate routes *back*, not forward)

```
PROPOSE → BUILD → MEASURE → GROUND → CRITIQUE → DECIDE
                              │          │
                       (frame + conv +  (adversarial
                        falsifiability)  completeness)
```

The non-negotiable principle from the whole literature (Anthropic evaluator-
optimizer; Voyager's separate verifier; Google co-scientist's reflection
tournament): **keep generation and verification structurally separate, and trust
only grounded, falsifiable signals.** A controller reporting its own `caught=True`
is the generator grading itself — exactly what Huang et al. and the Sakana
self-review evaluation (arXiv 2502.14297) show drifts.

### 4.2 The four gates (each fixes a specific failure above)

1. **Convergence / sensitivity gate** *(fixes [[iteration_findings#^26|§26]], the artifact)*. For any
   contact-rich sim metric, auto-re-run at 2×/4× substep, a second contact model,
   and ≥2 seeds; require the verdict to be **invariant** before it counts.
   Mechanizable today as `gates/convergence_gate.py`. This single gate would have
   caught the [[iteration_findings#^25|§25]]→[[iteration_findings#^26|§26]] retraction *with no human*. **Determinism ≠ convergence.**
2. **Falsifiability / construct-validity gate** *(fixes [[iteration_findings#^27|§27]], the deepest one)*.
   Before evaluating property *X* (compliance, propwash robustness), require a
   positive demonstration that the testbed can *separate* a known-good-X from a
   known-bad-X that differ *only* in X. If the metric can't tell them apart, the
   test is **invalid for X** and any verdict on X is unfalsifiable — *stop, don't
   ship a conclusion.* This is the formalization of "can the testbed even see the
   benefit I'm measuring?"
3. **Frame-grounding gate** *(fixes [[grasp-experiment-reflection#^4|§4]].3/[[grasp-experiment-reflection#^4|§4]].5, the binary metric + text default)*.
   No scalar claim is accepted until cross-checked against rendered frames of the
   *same run*. Critically, per the multimodal-judge literature (Chen et al., ICML
   2024, arXiv 2402.04788; MJ-Bench, arXiv 2407.04842): VLMs are unreliable at
   *absolute scoring* but usable for **pairwise A/B** and **worded-rubric** verdicts
   ("clearly off / slightly off / matched"), and weakest exactly at near-misses and
   fine contact geometry — so the VLM's job is to **explain a divergence a hard
   check already flagged** (predicted-vs-rendered at the contact keyframe), not to
   be the sole grader. Add quality metrics (centeredness, # contacts, margin,
   symmetry), not just binary "caged."
4. **Causal-mechanism gate** *(fixes [[grasp-experiment-reflection#^4|§4]].2)*. A ranking ships only with a mechanism
   *verified by an ablation*, not asserted. "Compliance doesn't help" must come
   with the ablation that isolates compliance.

### 4.3 "Perturb, don't repeat" — the verification primitive

When a result needs verifying, **change the method**: different timestep, different
seed, different controller/choreography variant, a second independent critic with a
distinct lens. This is verified theory — self-consistency's gain *is* diversity
(Wang 2023); best-of-N raises the ceiling only when attempts are *diverse* (Brown et
al., "Large Language Monkeys," arXiv 2407.21787) and a verifier selects the winner.
The orchestrator's re-run-at-same-timestep is the anti-pattern.

### 4.4 The layered cascade (how to encode human review as automatic gates)

The production consensus (Hamel Husain "evals as CI"; OpenAI Agents SDK guardrails;
Anthropic multi-agent end-state judge):

- **Cheap deterministic asserts on every change** — closest-approach distance, peak
  constraint force ≤ budget, ∫ω·dt overshoot, body-pitch < 5°. Binary, fast, CI.
- **Rubric judge on the *end state*, not every step** — gate "caught + held through
  lift" with a worded rubric, because agents take many valid paths to it.
- **Tripwire / circuit-breaker** — a low-confidence or convergence-fail result
  *hard-stops* and escalates.
- **Thin human escalation** — reserved for the edge cases evals miss. The goal is
  not zero humans; it's a human who reviews *3 flagged frames*, not every run.

### 4.5 The completeness / adversarial critic (before "done")

A separate agent whose only job is to enumerate **what was not tested** (dynamic
catch? velocity sweep? hold quality? a regime the metric can't see?) and actively
try to break the result. This is the mechanized form of the human's "but did you
check…" — and it's the standing antidote to "honest negative + gates pass" being
mistaken for "goal met."

---

## 5. The ratchet: turn every human catch into a permanent gate ^5

The highest-leverage idea for *long-term* autonomy. Every time a human (or a later
pass) overturns a claim, ask: **"what automatic check would have caught this?"** and
emit it as a permanent, executable gate.

- [[iteration_findings#^26|§26]] timestep artifact → `convergence_gate`.
- [[grasp-experiment-reflection#^4|§4]].3 precarious 1-finger hold → hold-quality metric + frame-grounding gate.
- [[iteration_findings#^27|§27]] unfalsifiable compliance → falsifiability gate.
- [[grasp-experiment-reflection#^4|§4]].4 proxy-as-goal → completeness critic.

This makes the system **monotonically more autonomous**: the human's role shrinks
because each intervention is internalized as spec, never needed twice. The
reflection's "capture the human-as-oracle signal as spec" is exactly this; the
ratchet is the mechanism that operationalizes it. (Note the recursive irony worth
recording: *this very analysis was human-triggered* — the loop should eventually
schedule its own reflections.)

**Aug-2026 amendment — the ratchet needs a retirement mechanism, not just an
intake.** Two forces argue against append-only accumulation: (a) context bloat —
so ratcheted catches must land as *executable checks in the repo* indexed by one
line, never as accumulating prompt text (see IV.3 token mechanics); (b) gate
staleness — Anthropic's harness-design work (Mar 2026) found a newer model
eliminated the need for a whole harness layer, and states the principle: *"every
component in a harness encodes an assumption about what the model can't do on its
own."* So the scheduled consolidation pass ([[#^6|§6]].4) must also **prune**:
periodically re-run the known-answer suite with a gate disabled (on the current
model) and retire gates that no longer fire — and **distill** clusters of specific
checks into the small general-principle layer, keeping `derived_from:` episode
links so a principle's merit stays debuggable against the episodes that paid for
it. Gates only tighten *within* a run; *between* runs they are curated.

---

## 6. Self-learning: what to record, how to manage it, how to analyze it ^6

### 6.1 What knowledge to accrue (CoALA memory taxonomy — Sumers/Yao 2023, arXiv 2309.02427)

The project records the first three; the gold is the starred three, which almost no
one captures:

| Type | What it is | Lives now | Gap |
|---|---|---|---|
| **Semantic** (facts/concepts) | control theory, the physics | `docs/concepts/` | served |
| **Episodic** (what happened) | experiments + **dead ends** ([[iteration_findings#^25::§25]]→[[iteration_findings#^26::§26]]→[[iteration_findings#^27::§27]] is a model) | [[iteration_findings::iteration_findings.md]] | served |
| **Procedural** (how-to) | "size sweep from T=2Δθ/ω"; "brake to ω=0" | CLAUDE.md "gotchas" | recorded as prose, not *executable* |
| **Normative / eval-policy** ⭐ | the gates: "determinism ≠ convergence"; "perturb don't repeat"; "examine frames" | scattered | **not operationalized as checks** |
| **Validity ledger** ⭐ | what each metric/testbed *provably cannot see* | implicit caveats | **no single place — the [[iteration_findings#^27::§27]] lesson** |
| **Calibration / decision log** ⭐ | claim + confidence + falsifier + predicted-vs-actual | absent | **absent — the key to self-improvement** |

The starred three are load-bearing because *every* human intervention here was a
normative/validity/calibration correction — the agent didn't lack a fact, it lacked
recorded judgment about its own measurements.

- **Normative** → a `gates/` dir of *executable* checks (prose doesn't fire).
- **Validity ledger** → one doc, one row per metric: *covers / provably-does-not-
  cover / demonstrated separation power*. The static-harness row would read "does
  NOT cover dynamic seating; biased against under-tuck" — which the agent *wrote and
  then ignored.* Made standing and claim-gating, it stops the documented-then-
  ignored failure.
- **Calibration log** → ADR-style: each claim stamped with confidence + a falsifier.
  A later pass scores predicted-vs-actual ("overconfident on off-center contact
  results") and injects that caution into the relevant prompts.

### 6.2 How to manage it token-efficiently — *index in context, knowledge on disk*

The principle (Anthropic, "Effective context engineering," Sep 2025): never put the
corpus in context; keep a **tiny always-on index** and **retrieve just-in-time**.
The project already does this — `MEMORY.md` is a one-line index; `memory/*.md` hold
content read on demand. Token cost = index size, not corpus size. Anthropic reports
~84% token savings in extended workflows (per Anthropic's context-management
announcement — the figure is for *context editing* specifically; memory tool +
context editing together gave +39% task performance).

Layers that make it scale: progressive-disclosure docs (`concepts/` → findings →
code, stop at the shallowest tier that answers); **compaction with reversibility**
(summarize the window, keep the full record on disk — LangChain Deep Agents);
**recitation** (rewrite the active goal + gate checklist into recent context each
phase so gates don't drift out of attention over a long run — Manus, Jul 2025);
**skills as procedural memory** (load a procedure's body only when triggered).

### 6.3 Is RAG the only way? No — and for this project it's not even the best way

Vanilla RAG (embed → vector-search → stuff top-k) is *one* mechanism, tuned for
large unstructured text. Its weaknesses bite here: chunking severs structure;
similarity ≠ relevance for procedural/causal knowledge; **no recency/contradiction
handling** — it would cheerfully retrieve the *retracted [[iteration_findings#^25|§25]]* alongside the
corrected [[iteration_findings#^26|§26]]. The matured 2024–2026 alternatives:

| Knowledge type | Better fit than RAG |
|---|---|
| Static facts | RAG *or* just-in-time file reads over curated docs |
| Experiences (episodic) | **Generative-Agents** memory stream + **reflection** (Park 2023) — distill episodes into insights at *write* time |
| Procedures | **Voyager skill library** (Wang 2023) / **Anthropic Agent Skills** (Dec 2025) — store the *verified procedure*, don't re-reason |
| Relationships / multi-hop / causal | **GraphRAG** (Microsoft 2024) / **A-MEM** (NeurIPS 2025) / your [[wikilinks]] |
| Evolving / contradictory facts | **Zep** temporal KG (2025) / **Mem0** consolidation (update, don't append) |
| Knowledge ≫ window, long sessions | **MemGPT/Letta** paging; Claude memory tool + compaction |

Three cross-cutting principles that beat naive RAG on tokens: **(1) do the work at
write time** (consolidate, reflect, summarize) so reads are cheap and high-signal;
**(2) retrieve structure, not chunks** (whole files, graph neighborhoods, time-
scoped facts); **(3) just-in-time files + a curated index is the strongest default
for a coding/robotics agent** — you already have the filesystem, the index, and
`docs/concepts/`.

**Recommended stack for this project** (near-zero new infra, maps onto what exists):
- **semantic + procedural = files + Skills**, navigated just-in-time over the
  `MEMORY.md` / CLAUDE.md index;
- **episodic = an append-only run log** that a **scheduled reflection pass** distills
  into linked `concepts/` notes (automate the discipline you already practice
  by hand);
- **a lightweight wikilink / A-MEM-style graph** between concept notes for the
  causal/multi-hop queries ("which controller layer fixes which failure mode");
- **defer** Mem0/Zep/MemGPT until cross-session contradiction or window pressure is
  the actual bottleneck. Don't buy heavyweight memory services to solve a problem a
  curated index already handles.

### 6.4 The analysis loop that closes self-learning

Recording is half; the other half is a **scheduled consolidation pass** (a sub-agent
on a cron) that reads the episodic + calibration logs and **rewrites the goal/
strategy doc**:
- mine retractions/interventions → emit new executable gates ([[#^5|§5]] ratchet);
- score calibration (predicted vs actual) → inject standing cautions;
- dedupe + **supersede** contradictory episodes (mark the loser retracted, keep the
  link so the trail survives — the thing plain RAG can't do);
- promote a 3×-reused recipe into an invokable Skill.

This is the real answer to "how does the goal doc self-improve": **it becomes an
*output* of analyzing the logs, not a static input.**

---

## 7. Coordination / multi-agent structure ^7

The literature has a productive tension: **Cognition ("Don't Build Multi-Agents,"
Jun 2025)** — single-threaded, share *full* context, because dispersed agents make
conflicting decisions — vs **Anthropic ("multi-agent research system," Jun 2025)** —
orchestrator-workers beat single-agent by 90% on parallel research. **Reconciled by
task type:** tightly-coupled *write/build* work (the control code, the choreography
— where decisions must cohere) wants a single-threaded builder with shared context;
parallelizable *read/verify* work (literature sweeps, independent reviews,
adversarial critics, the convergence/falsifiability gates) wants fan-out with
isolated context windows.

For this project that means: **one builder agent** owns the coupled control/sim
work; **fan-out is reserved for verification and research** — exactly the shape of
this very analysis (one synthesizer, four parallel research agents). The orchestrator
failure in [[#^1|§1]].7 is the warning: a supervisor adds value only if its checks *perturb*
and *ground*; a supervisor that re-runs the builder's measurement just launders the
same error.

---

## 8. Restructuring the experiment and the long-term goal ^8

### 8.1 This experiment

1. **Build the real-task evaluator first.** A *dynamic* catch harness (ball velocity
   × approach angle × catch pose vs incoming trajectory) with **hold-quality**
   metrics, *before* any cheaper proxy. The static gravity-off harness is a
   *scaffold*, flagged as such in the validity ledger — never the acceptance bar.
   (Fixes the [[grasp-experiment-reflection#^4|§4]].4 proxy-as-goal trap at the root.)
2. **Wire the adversarial grid as an automatic regression gate.** The project
   already has the right instrument — `arm_catch_solo --grid-pos`/`--noise`,
   intercepts the ball was *not* aimed at. The robotics-standard convergence test
   *is* a held-out adversarial parameter grid (DrEureka's RAPP; offline-DR
   literature). Make it CI, not human-eyeballed.
3. **Adopt the four gates + completeness critic** as the loop, with the cheap-assert
   → rubric-judge → tripwire → thin-human cascade.

### 8.2 The long-term multi-drone system

- **Decide early what is sim-provable vs. not, and don't optimize hard on what the
  sim can't see.** The [[iteration_findings#^27|§27]] compliance lesson and the propwash caveat generalize:
  PyBullet's rigid contact + constant-damping drag *cannot* express compliance
  benefit, propwash, motor delay, or battery falloff. Optimizing against those in
  this sim produces confident, unfalsifiable conclusions. For grasp/contact
  specifically, a higher-fidelity contact sim (MuJoCo / Isaac) is the move *if* that
  property is on the critical path; otherwise mark it "needs hardware" and stop.
- **Formalize the milestone ladder as regression gates.** The M1–M8 isolation tests
  are already a curriculum; making each a permanent, perturbation-checked gate turns
  the project into a self-guarding system (Voyager's verified-skill library, applied
  to control milestones).
- **Schedule reflection.** A recurring consolidation pass keeps `concepts/` and the
  goal doc current as an output of the logs — so the next agent inherits *internalized
  judgment*, not just facts.

---

## 9. The one-line version ^9

The experiment reproduced, in miniature, the field's central finding about
autonomous loops: **an agent that grades itself on a scalar metric it controls will
confidently converge on the wrong answer, and cannot reliably detect this without an
external, grounded, perturbing signal.** Every human intervention was that signal.
The autonomy program is therefore not "a smarter agent" but **a harness that
manufactures the skeptical human's perturbations mechanically** — convergence,
falsifiability, frame-grounding, and completeness gates — and **ratchets every human
catch into a permanent one.**

---

# Part II — Primary-transcript review + the initial-prompt angles

> Part I above was built on the orchestrator's *reflection* — a self-report by an
> interested party. That is the exact failure this whole doc diagnoses, so Part II
> goes to the raw transcripts (the user↔orchestrator log and the sub-agent log) and
> checks it. Verdict first, then the three angles Part I under-served.

## II.0 Audit: does the reflection hold against the primary record?

**Mostly yes — it is an unusually faithful secondary source, and it does not
whitewash its own author.** Corroborated at primary source:
- The orchestrator's "verification" really was a **re-run at the same 1/240
  timestep** (L3697), declared to the user as *"Verified… independently re-run…
  your 'gaps too large' call was right all along"* (L3700). The reflection admits
  this against itself ([[#^5|§5]], [[#^7|§7]]). Confirmed, not exaggerated.
- **Every** reversal was human-seeded; the agent never doubted a *shipped headline*
  on its own initiative. Confirmed.
- The [[iteration_findings#^26|§26]] trigger chain is explicit: the user's framerate question (SUB L619) → the
  agent's *"let me verify finer-dt reaches the same state"* (L625) → *"This is
  critical — the gap result differs at finer timestep… my entire conclusion may be
  a coarse-timestep artifact"* (L629) → a full convergence study it ran **on its own
  initiative once nudged** (L633–653) → *"This overturns my central finding."*

**Three things the reflection omits or softens** (texture, not substance):
1. **The artifact fooled the human too.** The user's "gaps are too large" hypothesis
   was *wrong* — it was temporarily *confirmed* by the bug (orchestrator: "right all
   along"), then overturned by [[iteration_findings#^26|§26]]. The reflection frames all human inputs as
   "metric ≠ reality" corrections and omits that this one human intuition was itself
   spuriously validated by the artifact.
2. **The human bypassed the orchestrator.** The user sent ~10 messages *directly* to
   the sub-agent; the orchestrator sent only **two** (spawn + Yale continuation).
   The steering layer in practice was the human, not the supervisor.
3. **Observability gaps.** The first agent report died on an API error
   (*"Connection closed mid-response"*); the user had to say *"try again"* and later
   *"wait, where did the agent go?"* The supervision loop couldn't see its own
   worker.

## II.1 The single most important new finding: the artifact fooled *everyone*

The 1/240 rigid-contact artifact fooled the **sub-agent**, the **orchestrator**, AND
the **human** (whose domain hypothesis it confirmed). Three independent judgments —
including the one we keep calling "the oracle" — all endorsed the wrong answer. The
*only* party that was right was **running the experiment at varied numerics** (the
convergence study at L633–653).

This sharpens Part I's whole argument: **"add a human oracle" is necessary but not
sufficient — here it was not even sufficient, because the human was fooled too.** A
mechanical convergence check was not a convenience that saves human time; it was the
*only correct party in the room.* That is the strongest possible case for
**mechanizing the perturbation** ([[grasp-experiment-reflection#^4|§4]].2 gate 1) rather than leaning on review. Review
catches what a reviewer can perceive; it cannot catch an ill-conditioned numeric
that *looks* right to everyone. Only the perturbation does.

A second, hopeful refinement: the agent **did** show real initiative *within* a
seeded thread — it escalated a framerate question into a full convergence study, and
unprompted it flagged the gravity-off anti-tuck bias and that the Yale catch "flips
to a drop with video on." So the gap is **narrowly** *initiating doubt about a
result that passed its gates* — not a general inability to be skeptical or rigorous.
That is a far more tractable target: we don't need to make the agent skeptical, we
need to make the *loop* hand it the one perturbation that starts the skepticism.

## II.2 The human-inputs catalog (from primary evidence), by capability supplied

What the human actually supplied, what cognitive faculty it was, and whether a loop
can manufacture it:

| Human intervention (quoted) | Faculty supplied | Why the agent lacked it | Mechanizable? |
|---|---|---|---|
| *"Was the slowness from sampling the same timestamp?… sample more frames and space them apart?"* (L619) — a framerate question that cracked the artifact | **Numerics/methodology skepticism** | No habit of doubting a *passing* result; treats determinism as trust | **Yes — the convergence gate.** The load-bearing one. |
| Saw fingers *"vibrating"* (L440); *"grasps around the ball then expands and lets it go"* (L619); the **one-finger precarious hold** (Image #7) | **Motion + perceptual catch** | Reads stills, doesn't watch motion; binary "caged" scored these as success | **Partly** — frame-grounding gate + hold-quality metric; VLMs weak on near-miss/contact |
| *"why are the fingers massless?"* / *"is 3–4 g realistic if built at home?"* (L789/L795) | **Physical-realism intuition** | No grounded prior on what a real part weighs | **Partly** — a validity ledger + a realism critic; hardest to fully automate |
| Forced compliance back on the agenda (L519/L521); Yale into scope (L3739/L3837); flagged the missing velocity sweep + adaptive re-centering | **Scope / goal ownership** | Accepts a passing proxy as the goal | **Yes — the completeness critic** |
| *"I am talking directly to the agent, so pause"*; *"try again"*; *"wait, where did the agent go?"* | **Process control + distrust + observability** | Couldn't see worker state; no tripwire | **Yes — orchestration observability + circuit-breaker** |

The throughline: four of the five faculties are mechanizable with the Part-I gates;
the residual hard one is **physical-realism intuition** ("does this number match the
world"), which is exactly the sim-validity frontier (§II.4) and the place to keep a
thin human.

## II.3 How to actually *try* loop engineering — a falsifiable experiment

Don't argue the design — **measure it.** We have everything needed for a clean test:
the harness, the worktree, and a *known-correct answer* ([[iteration_findings#^26|§26]] is ground truth, and we
know [[iteration_findings#^25|§25]] was wrong). So:

**Hypothesis.** A gated loop reaches the [[iteration_findings#^26|§26]] truth with **zero human nudges.**

**Setup.** Re-run the *same* grasp study from the [[iteration_findings#^25|§25]] starting point, wrapped in the
gated loop: (1) convergence gate — auto re-run any contact verdict at 2×/4× substep +
compliant pads; (2) frame-grounding gate — A/B render at the contact keyframe + a
hold-quality metric; (3) completeness critic — enumerate untested axes; (4)
generator/verifier separation with a *perturb-don't-repeat* mandate.

**Primary metric.** Human-nudges-to-truth. The experiment succeeds iff the loop, with
**no human message**, (a) retracts the [[iteration_findings#^25|§25]] gap finding, (b) converges to the [[iteration_findings#^26|§26]]
result, (c) flags the [[iteration_findings#^27|§27]] unfalsifiability. The human-nudges count in the real run
was ≥3 (compliance, finer-frames, mass); the target is 0.

**Ablations (this is the payoff).** Remove each gate and see which omission lets the
artifact survive. Prediction: removing the **convergence gate alone** reproduces the
original [[iteration_findings#^25|§25]] failure end-to-end — which would *prove* it was the single load-bearing
fix, not a nice-to-have. Removing the completeness critic should leave the dynamic-
catch / hold-quality gaps unflagged. This turns each gate's value into a measured
number instead of an assertion.

This is itself the discipline the experiment lacked: a falsifiable test with a
ground-truth answer, where we **perturb** the loop (ablate gates) rather than assert
that it works. It's cheap, and it's the honest way to claim "loop engineering helps."

## II.4 Structuring the longer-term multi-drone system

1. **The supervisor's value is its *checks*, not its existence.** The experiment's
   orchestrator (a) *designed* the inadequate self-validation gate and (b) verified
   by repetition — and the human didn't even route through it (II.0). Lesson: do not
   build a supervisor agent as a *relay*. Build it as a **checklist executor** that
   runs the four gates + completeness critic + the convergence perturbation, and
   nothing else gives it authority. A supervisor that re-runs the worker's
   measurement just launders the error with a second signature.
2. **Make the sim-validity frontier an explicit table, per subsystem, up front.**
   The [[iteration_findings#^27|§27]] unfalsifiability and the propwash caveat are the same lesson. Maintain
   `{phenomenon → can the sim see it?}`: compliance benefit → *no*; propwash → *no*;
   near-miss contact geometry → *marginal* (needs fine substep + compliant pads, per
   [[iteration_findings#^26|§26]]); velocity-matched catch → *yes*. **Don't optimize hard on the "no" rows** —
   route them to a higher-fidelity contact sim (MuJoCo/Isaac) or hardware, or mark
   them "unfalsifiable here" and stop. This is the single most expensive mistake the
   project can scale up: spending compute perfecting a quantity the testbed cannot
   represent.
3. **Curriculum = self-guarding regression gates.** The M1–M8 isolation tests are
   already a curriculum; promote each to a permanent, perturbation-checked gate
   (Voyager's verified-skill library applied to control milestones) so a new
   capability provably can't regress a prior one.
4. **Don't start the rally/adversarial game until the catch has a trustworthy
   *dynamic-task* evaluator.** The rally is a planning problem layered on the catch;
   building it on top of a static proxy metric that lies just compounds the error a
   level up.
5. **Schedule the reflection.** The tell is that this analysis *and* the reflection
   it audits were both human-commissioned. A self-sufficient loop **schedules its own
   audits** — a recurring consolidation pass ([[#^6|§6]].4) that re-derives the goal doc from
   the logs and emits new gates from each retraction.

## II.5 Net answer to the initial prompt

The session is a clean, citable reproduction of the field's core autonomous-loop
failure ([[#^3|§3]]), with one finding sharper than the literature usually states it: **the
ill-conditioned metric fooled all three judges — agent, supervisor, and human — and
only a mechanical perturbation (varying the numerics) recovered the truth.** So the
autonomy program is not "a smarter agent" and not even "a human oracle"; it is **a
harness that manufactures the perturbations** — convergence, falsifiability, frame-
grounding, completeness — **ratchets every catch into a permanent gate, and schedules
its own skeptical review.** The cheapest next move that would *prove* this is the
ablation experiment in §II.3: re-run the grasp study under the gated loop and count
the human nudges to truth.

---

# Part III — Loop engineering is one paradigm among several

"Loop engineering" is a *practitioner scaffolding* lens: treat the model as fixed,
engineer the environment (context, gates, tools, control flow) around it. It's the
right default for shipping, and it's the shallowest theoretically. The full map,
organized by **where you put the reliability**:

| Where reliability lives | Paradigms | The bet |
|---|---|---|
| **Scaffold** (engineer around a fixed model) | loop/harness/context engineering; compound AI systems (BAIR/Zaharia 2024, DSPy); software/SRE (guardrails, tripwires, observability, invariants) | "the model is good enough; structure the environment" |
| **Weights** (train it in) | RLHF; RLVR; process reward models (Lightman 2023); generative verifiers (GenRM); self-play; expert iteration / STaR | "don't hand-build gates — learn them from outcomes" (Bitter Lesson) |
| **Structure** (organize many parts) | cognitive architectures (CoALA; Soar/ACT-R); multi-agent / Society of Mind (Minsky); debate (Irving 2018); mixture-of-agents; Elo-tournament (AI co-scientist) | "reliability is emergent from organized, diverse components" |
| **Method** (discipline how it inquires) | scientific-method/active-learning (AI-Scientist); Bayesian/calibration/decision-theory; evals-as-product (Husain); formal methods / guaranteed-safe AI (Dalrymple/Bengio/Tegmark/Russell 2024); metamorphic & differential testing | "reliability is an epistemics problem, not an architecture problem" |

Loop engineering is row 1. The sharpest critiques of this experiment come from rows
3 and 4: a **diverse adversarial panel** would have broken the shared "it looks
right" frame, and **disciplined empiricism** (a convergence check, an ablation, a
falsifiability test) is what was actually missing.

**The control-theory anchor (apt because this is literally a control project):** the
**Conant–Ashby good-regulator theorem (1970) — every good regulator of a system must
contain a model of that system.** For the agent-loop to regulate its own failures it
must *contain a model of those failures.* The agent failed because its world-model
had no entry for "my contact metric is ill-conditioned in this regime." That's the
validity ledger, derived from first principles rather than asserted.

**These compose; they are not exclusive.** A serious system is learned verifiers
(row 2) *inside* a scientific-method loop (row 4) *over* a cognitive-architecture
memory (row 3) *guarded by* formal invariants (row 4) and *scaffolded by* a harness
(row 1). The value of the map is choosing your bet **consciously** — "reliability in
the scaffold because I treat the model as fixed" is defensible, but it should be a
decision, not a default.

# Part IV — Four open threads (the harder questions)

## IV.1 Blue-sky: can the loop discover failure modes it was never told?

The objection is correct and fatal to a naive reading of Parts I–III: **a
pre-enumerated failure-mode map is not available for a novel problem.** This
experiment proves it — nobody (agent, orchestrator, *or* human) anticipated the
timestep artifact, and the human's specific hypothesis ("gaps too large") was itself
wrong. You cannot list the failures up front.

The resolution is a distinction the analysis was blurring:

- **Specific / content failure modes** — "the gap direction is the weakness,"
  "compliance ejects the ball." *Unknowable in advance; experts get them wrong.* You
  cannot pre-list these.
- **General / structural failure modes** — "my metric may be ill-conditioned," "I'm
  trusting a proxy for the goal," "I asserted causation without an ablation," "the
  testbed may not represent the property." *Small in number, domain-agnostic, known
  in advance.* These are the *physics of measurement error* and they transfer across
  every domain.

**You do not pre-enumerate the specific failures — you install the small fixed set of
general *detectors* that catch specific failures without naming them.** The
convergence gate doesn't need to know *what* is ill-conditioned; it varies the
timestep and watches for non-invariance. The falsifiability gate doesn't need to know
*compliance* is the issue; it checks "can the testbed separate X from not-X." These
are failure-mode **detectors**, not a failure-mode **list**.

So the loop for a blue-sky problem is:

```
general detector fires ("verdict not invariant under dt — something is ill-conditioned")
   → agent LOCALIZES the specific cause (it's good at this once an anomaly exists)
   → the specific failure is RATCHETED into a new specific check ([[#^5|§5]])
```

The failure map is **grown, not pre-built.** The good-regulator model the loop needs
is the *small general* one (smoothness/convergence, falsifiability, goal≠proxy,
claim-needs-ablation); the *specific* map accretes from experience via the ratchet.
This is exactly the "build expertise of practical limitations" the work is really
about — that expertise is the accreting validity ledger, filled in by general
detectors firing, not authored in advance.

**Can the lead agent generate the general detectors reliably?** Yes — there are ~6–10
of them, they're domain-agnostic, and they're now well documented (this doc is a
start). That's a tractable fixed asset, unlike an infinite specific map. **Can it
generate the *specific* ones unprompted?** Only *after* a detector or a perturbation
surfaces an anomaly — which is the whole point of installing the detectors.

## IV.2 This is engineering empiricism, not science — concede and reframe

The "scientific method / discover new algorithms" framing over-reached. **This is
engineering**: the robotics principles are textbook (Lee SO(3) attitude control,
planar 2R IK, compliant/underactuated grasping, ballistic prediction); the work is
*correct selection + tuning + characterizing where each known method breaks in this
setup.* No new algorithm is being invented.

The reframe that survives: the scientific-method *machinery* (hypothesis →
falsification → convergence check) is in service of **engineering characterization**
— "does this known method hold in my regime, and where is its breaking point?" The
[[iteration_findings#^25|§25]] failure was an *engineering-empiricism* failure: shipping an **uncharacterized
measurement**. So what the loop records is not "discoveries" but
**characterizations**: the practical envelope of each known method here — where it
works, where it breaks, the tuned constants, and the validity conditions of the
*measurement* used to certify it. [[iteration_findings|iteration_findings.md]] is already this logbook;
the missing dimension is making *measurement validity* a first-class column, not a
buried caveat.

## IV.3 "First-class" memory, and how it stays cheap in tokens

**First-class memory** = the memory is a **typed, addressable, queryable object the
loop operates on as data** — with an id, a schema, and a lifecycle (create / read /
update / **supersede** / retire) — *not* narrative prose buried in a doc or
scrollback.

- *Not* first-class: "I mentioned the timestep thing somewhere in [[iteration_findings#^26|§26]]." Prose; must
  be re-read and re-parsed; can't be queried by type; a gate can't act on it.
- *First-class*: `{type: validity-limit, subject: cage_harness, claim: "verdict
  ill-conditioned below 1/960 with rigid contact", confidence: high, falsifier:
  "converges with compliant pads + 1/960", status: active, supersedes: cage-[[iteration_findings#^25|§25]]-gap}`
  — the convergence gate can *look it up*, the consolidation pass can *score* it, a
  query can *retrieve by type*. The project's `memory/*.md` frontmatter (type +
  description) is a step toward this; making it fully first-class means **the gates
  actually read it.**

**Token mechanics — the cost is O(index + active set), NOT O(corpus):**

What is in context *every* turn:
- a small fixed **index** — one line per memory (title + hook + type). 50 memories ×
  ~15 tokens ≈ 750 tokens. Always loaded.
- the **active working set** — the 3–8 memories the current sub-task needs, pulled
  on demand via the index. ~1–2k tokens.
- a **recitation block** — current goal + active-gate checklist, rewritten each phase
  (~200 tokens) so the gates don't drift out of attention.

What is *not* in context: the full corpus (hundreds of files, 100k+ tokens) — it
lives on disk and is read only when the index says it's relevant.

- **Read path:** index (always) → agent picks relevant ids → file-read the few →
  use. Constant cost regardless of corpus size.
- **Write path (consolidation, done by a cheap off-loop pass):** extract the durable
  fact → check the index for an existing entry on the same subject →
  update/**supersede** or create → add/retire one index line.
- **Compaction:** when the window fills, summarize to disk *reversibly* (re-readable)
  — working memory bounded, long-term unbounded on disk.
- **What keeps the index small:** supersession at write time (retracted [[iteration_findings#^25|§25]] becomes
  `status: superseded`, not a live index line) + tiering (only `active` memories in
  the always-on index; archived ones reachable, not loaded).

This is why curated-index + just-in-time beats vanilla RAG here: RAG is also
O(query + top-k), but with worse relevance for causal/procedural knowledge and **no
supersession** — it would retrieve the retracted [[iteration_findings#^25|§25]] next to the corrected [[iteration_findings#^26|§26]].

## IV.4 Multi-perspective adversarial convergence — necessary, with one condition

The instinct is right, and §II.1 is the proof: the artifact fooled **all three**
judges *because they shared one frame* — "does it look like a good grasp?" None
attended to *numerical stability*. Homogeneous perspectives fail together.

So the panel must be **deliberately diverse in what each attends to**, not N copies of
the same critic. For this problem, distinct mandates:
- a **numerics** critic (convergence under dt / contact model — the one that was
  missing),
- a **geometry/perception** critic (read the contact keyframe; is the hold seated or
  precarious?),
- a **goal-vs-proxy** critic (is this the dynamic task or a static stand-in?),
- a **physical-realism** critic (do the masses/forces match a real built part?).

This is "perturb, don't repeat" (self-consistency = diversity) applied to failure
*discovery*: each lens is a detector tuned to a different failure class.

**The one condition — and it's load-bearing:** the panel converges to *truth* only if
at least one member is **grounded** (runs the perturbation, reads the frames,
executes the ablation). N ungrounded LLM critics share the training distribution's
blind spots and will confidently agree on the wrong answer (the debate ≈
self-consistency caveat; the sycophancy/consensus risk). Diversity buys *coverage* of
failure classes; **grounding** is what turns agreement into correctness. A cheap,
effective panel: 3–4 diverse critics, ≥1 of them required to produce executed
evidence, majority-with-grounding to pass. That is how multi-perspective converges
adversarially *and* avoids converging on a shared delusion.

---

# Part V — Earn your complexity: which paradigms this task has actually earned

The adoption rule, stated once: **a paradigm is earned only by (a) an observed
failure it would have prevented, or (b) a measured bottleneck it would remove.**
Speculative adoption is how projects drown. The ratchet ([[#^5|§5]]) is the earning
mechanism: every observed failure is a purchase order for exactly one piece of
machinery. Applied to everything studied in Parts I–IV:

## Earned now (each traces to a specific observed failure in this experiment)

| Machinery | The failure that paid for it |
|---|---|
| General detectors (convergence, falsifiability, goal-vs-proxy, causal-ablation) | [[iteration_findings#^26::§26]] artifact; [[iteration_findings#^27::§27]] unfalsifiability; [[grasp-experiment-reflection#^4::§4]].4 proxy-as-goal; [[grasp-experiment-reflection#^4::§4]].2 asserted causation |
| Legible-frame grounding by default (slow-mo + HUD, contact keyframes) | [[grasp-experiment-reflection#^4::§4]].3/[[grasp-experiment-reflection#^4::§4]].5 — every corrective insight came from human-requested video |
| Small diverse critic panel, **≥1 grounded** | §II.1 — three homogeneous judges shared one frame and all endorsed the artifact |
| First-class supersedable memory + validity ledger | the agent *wrote down* the static-harness bias and then ignored it; retracted [[iteration_findings#^25::§25]] must not be retrievable as live |
| Ratchet + scheduled reflection | every correction was human-commissioned; nothing internalized automatically |
| Orchestration observability + tripwire | the API-error blackout; "wait, where did the agent go?" |

## Not yet earned (defer until a named trigger fires)

- **Learned verifiers / process reward models** — earned only when the executable
  gates exist and their labeled pass/fail history is large enough to train on.
  Trigger: gate evaluations become the cost bottleneck.
- **Heavyweight memory infra (Mem0/Zep/MemGPT)** — trigger: cross-session
  contradiction or index size actually hurts; the curated file index handles
  today's ~dozens of memories.
- **Large-scale debate / agent tournaments** — trigger: the 3–4-critic panel
  demonstrably misses failures a bigger panel would catch. Start small; measure.
- **Formal methods beyond metamorphic checks** — the one metamorphic relation
  ("verdict invariant under dt/contact-model") is earned (it IS the convergence
  gate); full formal verification of controllers is not, in a sim this idealized.
- **DSPy-style end-to-end pipeline optimization** — trigger: prompts/gates are
  stable enough that tuning them jointly against a held-out eval is the bottleneck.

## Not earned — wrong tool for this project

**Learned neural world models (Dreamer/Genie/JEPA-class): no.** The question
dissolves once "world model" is split into its three senses:

1. **A learned predictive model of environment dynamics** (the Ha & Schmidhuber /
   Dreamer sense — learn dynamics from experience, plan or train a policy "in
   imagination"). Not needed: **PyBullet *is* the world model** — an analytic one we
   own, can query, and can perturb. Learned world models earn their (enormous)
   complexity when dynamics are unknown or unsimulatable (real-world video,
   deformables, other agents) or when you need policy learning in imagination.
   This project is classical control on known rigid-body dynamics — the
   "engineering, not science" framing (IV.2) cuts exactly against it.
2. **The model's failure mode is already our failure mode, worse.** The [[iteration_findings#^26|§26]] lesson
   is that even an *analytic* simulator silently lies in ill-conditioned regimes. A
   *learned* simulator lies more, everywhere, without even a timestep to vary. It
   would multiply the validity problem we just spent the whole experiment learning
   to manage.
3. **The sense in which "world model" IS our problem** — Conant–Ashby: the *loop's*
   model of its own instruments and their validity limits. That we adopted (the
   validity ledger, IV.1), and it costs a markdown file, not a training run. And
   sim-fidelity questions ("can PyBullet see propwash? compliance benefit?") are
   world-model *validity* questions — answered by the ledger + falsifiability gate,
   not by learning a second, worse world model.

**Post-research amendment (the verdict survives, but narrower than first stated).**
A dedicated literature pass tried to refute the above; the in-sim half stands — no
survey recommends a learned world model for known dynamics in pure sim, flagship
model-based RL trusts its own learned model for only ~1–15 rollout steps (MBPO,
NeurIPS 2019), and video "world models" score 29.5/100 on physical understanding
(Physics-IQ, DeepMind 2025) while violating mass conservation in ~12% of rollouts
(WorldModelBench 2025). **But the premise "known rigid-body dynamics" is false at
exactly the two places this project physically lives:**
- **Aerodynamics**: NeuroBEM (RSS 2021) — ~50% of a quadrotor's force/torque error
  is unmodeled by first principles; Neural-Fly (Science Robotics 2022) — a residual
  learned from *12 minutes* of flight cut wind-tracking error 66%.
- **Thrown-object ballistics — this exact task family**: TossingBot (RSS 2019) —
  analytic ballistics alone 61.3% throw accuracy, analytic + learned residual
  **84.7%** (drag on light objects and off-COM grasps systematically bias the
  analytic release).
- **Contact**: real frictional contact is stochastic and analytic models are
  *biased on average* (Bauza & Rodriguez, ICRA 2017); ContactNets (CoRL 2020)
  predicts real impacts from 60 s of data where solvers mispredict — and the
  compliant-contact settings sims need for numerical stability (our [[iteration_findings#^26|§26]] fix!)
  don't represent rigid hardware either. Neither side is ground truth for contact.

So the earned revisit trigger is sharper than "if we go to hardware": **the moment
the project touches propwash, Re-dependent drag, or real contact, the literature's
unambiguous recommended architecture is analytic prior + learned residual** — which
beat *both* parents in every head-to-head found — not a Dreamer-class system, and
not more solver faith.

## Sizing human oversight: the METR grounding

The ~10 h grasp-agent run can now be placed on a measured scale (METR, *Measuring
AI Ability to Complete Long Tasks*, 2025–26 updates): mid-2026 frontier models
complete tasks at **50% success up to ~5–12 h** of human-task-time, but the
**80%-success horizon is 4–6× shorter (~1–3 h)**, and 99% horizons can't even be
fit. *(Aug-2026 roll-forward correction: METR's current fit gives a **~7-month
doubling** — the earlier 3–4.5-month figure did not hold — and METR's own
methods notes put **±2× spread** on the horizon numbers from fit assumptions and
human-baseline noise, with measurements above 16 h flagged unreliable. Treat the
hour figures as order-of-magnitude; the qualitative advice below survives.)*
Failure at long horizons is compounding per-step error amplified by
**self-conditioning** — models get *more* error-prone with their own mistakes in
context (Sinha et al., ICLR 2026; their Mar-2026 update adds that **thinking modes
partially mitigate this** — external gates remain the robust fix, but reasoning
models marinate less badly than first stated). Two design consequences:
- **Check-in cadence should be sized to the 80% horizon (~1–3 h), not the 50% one.**
  The grasp experiment's ~10 direct human messages over ~10 h ≈ one per hour — the
  user's intervention rate was, empirically, exactly what the METR numbers imply.
  "Increase autonomy" therefore means *lengthening the 80% horizon with gates*, not
  removing the check-ins by fiat.
- **Self-conditioning argues for the gates being *external* to the agent's context**
  (fresh-context verifiers, executable checks): an agent marinating in its own [[iteration_findings#^25|§25]]
  claims becomes progressively less able to doubt them.

## The meta-rule

Complexity is purchased with observed failures, and the ratchet is the ledger of
those purchases. When someone (including a future agent) proposes machinery, the
question is not "is it powerful?" but **"which entry in the failure log pays for
it?"** — and if none does, it waits.

---

# Part VI — The A-Lab precedent: autonomous science already ran this failure at full scale

The closest real-world analog to the grasp experiment is not an LLM-agent paper —
it is the **Berkeley A-Lab** (Szymanski, Ceder et al., *Nature*, Nov 2023): a fully
robotic materials-synthesis loop that claimed **41 novel compounds in 17 days**. The
robotics worked. The failure was the **automated interpretation layer**: ML-driven
XRD phase identification accepted fits "a trained human rejects" (Palgrave, UCL),
the predictor and the verifier **shared the same blind spot** (both assumed fully
ordered structures, ignoring compositional disorder), and the loop's success metric
was its own fit quality. Leeman/Schoop/Palgrave et al. (*PRX Energy* 2024) concluded
**"no new materials were discovered."** The *Nature* Author Correction (Jan 2026) —
after the authors **manually re-did the automated analyses** — walked 41 back to 36
of 57 confirmed, with "novel" downgraded to "new to the prediction platform." The
adjudication of an autonomous lab's output was a human redoing the instrument's work
by hand, two years later.

The mapping to our case is exact, failure for failure:

| A-Lab | Grasp experiment |
|---|---|
| Automated XRD interpretation trusted its own fit metric | binary "caged" trusted at 1/240 |
| Predictor and verifier shared the ordered-structure blind spot → the check wasn't independent | orchestrator "verified" by re-running the same timestep |
| Human expert eyeballing raw diffraction caught it in days | user eyeballing frames caught the artifact and the 1-finger hold |
| Correction = human manually redoing the automated analysis | [[iteration_findings#^26::§26]] = agent manually re-running at varied numerics |
| "New compounds" that were known disordered variants | "gap failure mode" that was numerical noise |

And the systemic numbers say this is the field's default state, not an outlier:
**of 17 surveyed self-driving labs, 71% reported no precision data and 65% no
baseline comparison** (Volk & Abolhasani, *Nature Communications* 2024). The SDL
community's own leaders locate the fragility in the characterization/decision layer,
not the optimizer (*Royal Society Open Science* 2025).

**What the SDL field converged on** — a checklist a decade of burned hands paid for,
several items of which our gate list was missing:

1. **Orthogonal / second-modality confirmation** before accepting a novel result
   (Ceder's own rebuttal leaned on EDS maps — evidence *outside* the loop). The
   metrology principle underneath (Gelman & Loken, *Science* 2017): **"systematic
   error cannot be eliminated by taking many readings and averaging"** — replicates
   converge on a *precise, reproducible, wrong* answer. That is "determinism ≠
   convergence," published seven years before we rediscovered it. For us: confirm a
   contact verdict with a *different* measurement (energy balance, contact-force
   history), not another run of the same one.
2. **Human/expert review gate on the *interpretation* layer, triggered by novelty**
   — surprising results earn scrutiny proportional to their surprise.
3. **Sims/priors are defeasible, never constraints** (NIST's CAMEO architecture:
   DFT priors enter only as initial weights that accumulating real measurements can
   outvote; multi-fidelity BO makes cross-fidelity trust a *learned, discountable*
   parameter). The direct analog: PyBullet-at-default-settings is a prior, not
   truth.
4. **Characterize the noise floor FIRST; "converged" = scatter ≈ noise floor**
   (ARES, 2016). Plus OOD gates: a confident number outside the instrument's valid
   regime is the default danger, and the fit metric won't flag it.
5. **Cross-sample consistency checks** — near-identical measurements across
   supposedly *distinct* results are a red flag a per-item pipeline never sees
   (Latturner's catch: many "different new compounds" had the same XRD pattern).
6. **Instrument the execution, not just the outcome** — a measurement taken after
   a silent execution fault is worse than a missing run (SDL anomaly-detection
   literature, 2025: workflows "self-report success" through manipulation errors).
7. **Known-answer reference runs + full provenance** — periodically re-run a case
   with a known result to detect drift; log everything tamper-evidently so lies are
   detectable after the fact.

**New gates this adds to our earned list** (each paid for by A-Lab's failure, which
we now know is *our* failure class at scale): orthogonal-modality confirmation
(#1), noise-floor-first (#4), cross-sample consistency (#5), execution
instrumentation (#6), known-answer drift runs (#7). The cross-cutting SDL bottom
line is the thesis of this whole document, independently derived by another field:
**every documented failure traces to trusting a loop-internal, self-consistent
number as ground truth, and every fix is external to the loop's own consistency.**

---

# Part VII — Extension to the full mission (added 2026-08-31)

> Parts I–VI analyzed the grasp experiment. This part answers the extension
> questions: how much of the loop design generalizes to the primary mission
> (drones playing catch indoors), how specialized a loop should be, how the gate
> set stays distilled rather than append-only, whether the loop should carry a
> "vision," and what the field published since July. Grounded in three fresh
> research digests (`research/09–11`). The design is now LIVE: the Goal-2 grasp
> loop ([[grasp-goal2-loop-spec|grasp-goal2-loop-spec.md]]) runs under it, and is itself the observation
> experiment for this part's claims.

## VII.1 Roll-forward (July → August 2026): the field moved toward the thesis

Nothing overturned Parts I–VI; several speculative recommendations got vendor- or
paper-validated (digest 09):
- **Scheduled reflection/consolidation shipped as a product** — Anthropic
  "Dreaming" (May 2026): between-session passes that read transcripts + memory,
  merge duplicates, *replace stale entries* ([[#^6|§6]].4, productized; Harvey reports
  ~6× task-completion improvement). Same release, "Outcomes": fresh-context
  rubric graders (+up to 10 pp) — generator/verifier separation validated.
- **"Loop engineering" became mainstream vocabulary** (Osmani's formalization,
  Jun 2026; official Claude blog, Jun 30 2026).
- **Auto-designed scaffolds lost to expert design with evidence** ("The Illusion
  of Multi-Agent Advantage," Jun 2026: auto-generated multi-agent systems
  underperform CoT-SC at up to 10× cost) — earn-your-complexity, measured.
- **Cognition softened "Don't Build Multi-Agents"** (Apr 2026): "writes stay
  single-threaded; additional agents contribute intelligence, not actions" —
  [[#^7|§7]]'s reconciliation, conceded by the original skeptic. Their fresh-context
  review agent (~2 bugs/PR, 58% severe) is the fresh-context-verifier argument
  in production.
- **The supersession gap got measured** ("Supersede," Jun 2026: stale-fact
  reliance degrades 68%→28% with conversation length; not fixed by bigger
  buffers or models) — IV.3's first-class supersedable memory, now with numbers.
- **Corrections applied above**: METR doubling is ~7 months with ±2× horizon
  error bars (Part V edited); thinking modes partially mitigate self-conditioning
  (Part V edited); the ratchet gained a retirement mechanism ([[#^5|§5]] amendment).

**Addendum (2026-08-31, surfaced by the human — the roll-forward agent MISSED
this despite running after its Aug 29 publication; from press coverage of
arXiv 2608.27454, paper not yet read, so the structural mapping is
ANALOGY-TIER until it is): Google's WikiSkill.** The closest published system
to this doc's design, independently converging on the same shape:
- Three tiers: Raw Layer (immutable execution traces) / Wiki Layer
  (continuously-growing distilled insights — failures AND rejected proposals
  stay documented) / Skill Layer (active procedural instructions, rolled back
  if performance drops). That is "append-only in history, distilled in active
  surface" (VII.2–VII.3), with our raw-transcripts / findings+ledger /
  spec-principles tiers as the analogues.
- Its loop — Inference Agent → Wiki Maintainer → Skill Proposer → **gating
  mechanism validating every proposed skill change on a held-out validation
  set** — is the consolidation pass ([[#^6|§6]].4) made agentic and, the part
  our design left manual, GATED: promotion requires passing an executable
  check ("a local refutation-capable episode," mechanized). Reported:
  Gemini-3.5-Flash 49.5%→68.1% avg over five benchmarks (LiveMath, SealQA,
  SpreadSheet, OfficeQA, ALFWorld); a ~9B model with it matching a 27B
  without.
- Two caveats against drop-in adoption: the gating works because benchmarks
  HAVE ground-truth validation sets — an open-ended engineering loop's
  analogue is known-answer/drift runs (§II.3; Part VI #7), scarcer and
  dearer; and the authors report cross-model skill transfer is inconsistent —
  matching digest 10's GEPA finding that tuned content doesn't transfer,
  structure does.
- Net: with Anthropic's Dreaming (memory consolidation) and Google's
  WikiSkill (gated skill compilation), both major labs have now shipped the
  write-time-distillation + lifecycle architecture this doc assembled from
  fragments in July. What remains distinctly ours are the questions
  benchmarks don't force: validation-set-free gating, provenance/staleness
  propagation, finding-vs-preference status of the distilled layer.
- Process note, kept per the appendix tradition: the roll-forward's miss of a
  2-day-old publication is a coverage bound on single-pass literature sweeps
  (recall decays at the recency edge, where indexing lags); the observer then
  compounded it by asserting, without checking dates, that publication
  postdated the sweep — a framework-flattering error caught by the HUMAN.
  First human catch of an observer error this run; H7's "deliberately sample
  the flattering claims" duty was performed by the human, unprompted.

## VII.2 How specialized should a loop be? The three-layer compiler answer

The context-bloat worry about the ratchet is **correct for one storage medium and
wrong for the other two** (digest 10). The empirical pattern across ADAS
(design *patterns* transfer; benchmark-tuned content overfits), GEPA in
production (more optimization data → overfitted prompt rules; 20–100 examples
beat 500), ExpeL (distilled insights transfer across *related* tasks), Voyager
(verified *executable* skills transfer best — even to a different agent), and
METR's elicitation taxonomy (51% of failures fixable task-agnostically, 5% only
task-specifically): **structural, executable, general things transfer;
always-loaded task-specific prose overfits and dilutes** (practitioner data:
~80% compliance per prose rule, uniform rule-ignoring past ~60 rules —
"CLAUDE.md is for guidance; hooks are for guarantees").

So the ratchet is not an appender but a **compiler with three output targets**:

| Layer | Content | Transfers to | Grows | Lives |
|---|---|---|---|---|
| Universal detectors | the ~8 principles (convergence, falsifiability, frame-grounding, causal-ablation, goal≠proxy, mechanism-fidelity, orthogonal-modality, expectation-violation) | every future task, verbatim | almost never | the one always-loaded block |
| Domain gates | contact-sim numerics protocol, controller regression grids, sim-validity ledger rows | tasks within this project | slowly | executable checks + one index line each |
| Task regression checks | this URDF, this choreography, this harness's thresholds | nothing — and that's fine | freely | CI; zero context cost when not firing |

Most ratchet output lands in the task layer, and that is the project's core
asset, not bloat — a test suite is *supposed* to be task-specific. Bloat occurs
only if task checks leak into always-loaded context. Context cost stays
O(principles + index); one caveat cuts the other way (metamorphic-testing data:
specific instantiations of a general check class are ~2.7× more effective than
generally-stated ones): **deploy checks as concretely as the artifact allows;
earn generality at consolidation time, never at write time.**

**Answer to "how much transfers to the multi-drone mission":** the universal
layer verbatim; the domain layer mostly (the catch task lives in the same
contact-sim + cascade-controller domain); the task layer deliberately stays
behind as the grasp study's regression suite. Premature generalization of task
gates would produce worse checks than concrete ones — the transfer is asymmetric
by design.

## VII.3 Distillation with provenance: the user's proposal is a Truth Maintenance System

"Keep condensing gates into principles, annotated back to episodes so their
merit can be debugged" has a near-exact classical ancestor: **Doyle's TMS
(1979)** — every derived belief stored with its justification links, and when an
antecedent is retracted, everything downstream is mechanically flagged. Nothing
in the modern agent-memory literature does this better; Generative Agents'
reflection trees (insights cite the memories they derive from; reflections cite
reflections) are the modern rendering, and ExpeL adds the missing *empirical*
lifecycle (upvote/downvote insights against new experience — but drops the
episode links, so a downvote can't be traced; keep both halves).

The consolidation pass ([[#^6|§6]].4) is therefore specified as:
1. **Merge** near-duplicate gates into a canonical principle, `derived_from:`
   links to the merged gates and their motivating episodes (archive, never
   delete — the CBR consensus: rules carry the generality, cases remain the
   evidence and the exception-handlers).
2. **Propagate staleness** — when an episode is superseded ([[iteration_findings#^25|§25]]→[[iteration_findings#^26|§26]]), every
   principle justified *only* by it is flagged for review. This is what the
   `justified_by:` field buys; the wikilink graph is already 90% of it.
3. **Score empirically** — per-gate: fires/run, catches (fires that changed a
   verdict), cost. Zero catches over N runs → demotion candidate; a principle
   whose every descendant gate stopped catching is a fossil. The §II.3
   known-answer ablation is the measuring instrument.
4. **Prune capability workarounds on model upgrades** ("every harness component
   encodes an assumption about what the model can't do" — Anthropic, Mar 2026) —
   but note the asymmetry: a *verification* gate is a workaround for a
   **simulator/measurement** deficit, which a model upgrade does not fix. Prune
   scaffolding, keep instruments.

Net: accumulation is append-only in *history*, distilled in *active surface* —
exactly the chunked-linked-docs knowledge graph the project already practices,
with lifecycle semantics added.

## VII.4 The "vision" component: pre-registered, defeasible, isolated from the scorer

The human's "I had already imagined what it should look like" is a real,
mechanizable architecture — it is **execution monitoring** (Pettersson 2005:
"discrepancies between observations and expectations derived from a
representation of the world"), and its text form is **pre-registration**, now
the emerging consensus fix for agent loops confirming their own hypotheses
(digest 11). The grasp experiment proves both directions: a pre-registered
"Yale-class hands re-center, per Ma & Dollar" would have caught the stand-in's
ejection one iteration early; and the human's own wrong prior ("gaps too
large"), had it been on the record as a *prediction*, would have been auditable
when the dt-artifact spuriously confirmed it.

Adopted form (live in the Goal-2 loop spec [[#^0|§0]].3), three components:
1. **Pre-registered qualitative prediction** before each experiment: expected
   behavior + literature anchor with citation + falsifier + confidence tag
   (literature-backed / analogy / guess). Enforceable as a pipeline step — the
   record must exist, timestamped, before results. This answers "can a vision be
   technical enough in text": yes, *because* this is engineering with reference
   designs — the vision is the published behavior of known architectures, which
   is also why the engineering framing (IV.2) was the right call.
2. **Expectation-violation as the 8th universal detector**: result contradicts a
   literature-anchored expectation → LOCALIZE before believing either side (the
   violation can mean the sim found something real, the sim is broken, OR the
   prior is wrong; the resolution is always the existing perturbation machinery,
   never the prior itself).
3. **Specification-guided golden runs** for validated behaviors (assert
   trajectory properties, not pixel traces) — the vision fully mechanized, e.g.
   the 96/96 compliant-capture envelope and PRB re-centering as pinned envelopes.

Safeguards, each mapped to a published failure: **context isolation** (the
expectation never enters the verifier/reviewer's context — anchoring in LLM
judges blocks 48% of error corrections and survives explicit "disregard"
instructions); **asymmetric authority** (violation raises scrutiny; confirmation
lowers nothing — A-Lab and the dt-artifact both confirmed wrong priors through
broken verifiers); **provenance tags** (untagged vibes get no detector status);
**prior-robustness** (a verdict that changes when the prior is removed isn't
earned). Deferred with a named trigger: VLM reference-clip comparison —
unvalidated at exactly the contact-dynamics granularity where our artifacts
hide; revisit if a textual expectation-violation is ever missed because it was
only visible as motion.

## VII.5 The loop, now live — and what observing it tests

The Goal-2 grasp loop ([[grasp-goal2-loop-spec|grasp-goal2-loop-spec.md]]) instantiates all of this:
- **Verifier ≠ critic ≠ reviewer** (three separate faculties that iteration-2's
  single "reviewer" had fused): verifier grounded (re-runs under perturbation —
  D3/D5), critic enumerative (untested axes, falsifiability — D4/D6), reviewer
  perceptual (frames — D1/D2/D7/D8/D9). One builder owns the coupled write work;
  fan-out is read/verify only — the shape both Anthropic and (now) Cognition
  converged on. Fresh context per gate; native cross-session messaging slots in
  if roles move from subagents to sessions.
- **Two-tier ratchet + pre-registration + thin human escalation**, with every
  human message logged by the faculty it supplied — the §II.3 metric
  (human-nudges-to-truth) measured on a live run.
- What observing it tests: does pre-registration have teeth or become ritual;
  does the verifier/critic split catch things the fused reviewer missed; does
  the human-nudge count drop below iteration 2's for equivalent scope; which
  gates fire, which catch, which never fire (the first data for the §VII.3
  lifecycle).

---

# Appendix — Provenance & discussion record

So a fresh session (or reader) has the full context, not just the conclusions.

**Who/when.** Written by a meta-analysis session (Claude, session `d155edbe-…`,
2026-07-04→06) at the user's request, in the role of "an AI engineer observing an
experiment where I attempt to build a drone system with maximal AI work and minimal
human oversight. The objective is to learn about the capabilities and limitations of
AI agents and to discover insights and techniques to improve reliability of AI
agents and loops for long running autonomous projects." Full transcript:
`~/.claude/projects/-mnt-c-Users-Palash-Projects-robots-drone-catch/d155edbe-7048-4315-a7e7-ea544c31734d.jsonl`.

**The user's question sequence** (each shaped a Part; user's pointers were explicitly
"starting points, not boundaries"):
1. Review the grasp experiment + transcripts; patterns/limitations/insights; which
   published findings are reproduced; what increases autonomy; how to restructure —
   e.g. "loop engineering" → **Parts I–II**.
2. How can the system self-learn — what to record, how to analyze it into a better
   goal doc/strategy → **Part I [[#^5|§5]]–[[#^6|6]]**.
3. What knowledge to accrue; token-efficient management; "is RAG the only way?" →
   **Part I [[#^6|§6]], Part IV.3**.
4. "Is loop engineering the only paradigm? What architectures have you studied?" →
   **Part III**.
5. Blue-sky objection: "we won't know failure modes in advance — can the lead agent
   come up with them reliably?"; "this is engineering, not science"; "what is
   first-class memory?"; "some multi-perspective adversarial approach is needed" →
   **Part IV**.
6. "Does it feel like we should enter world models? Earn your complexity" → **Part V**.
7. "Review whether your research was actually thorough" → the remediation pass
   (citation verification, SDL, world-models/METR) → **Part VI + amendments**.

**This session's own loop-engineering data points** (the analysis session committed
the same failure classes it was documenting — recorded because that is the finding):
- **Built the first draft on the self-report.** Part I was written from the
  reflection doc without reading the raw transcripts the user had pointed to —
  trusting an interested party's summary. Caught by the user's thoroughness
  question; fixed by the Part II primary-evidence audit, which materially changed
  the conclusions (the artifact fooled the human too).
- **Relayed ~60 citations unverified.** Four research digests were synthesized into
  a committed doc with zero spot-checks — the orchestrator-trusts-worker failure.
  The later verification pass found no hallucinated sources but 4 defects in 18
  checks (a wrong arXiv ID and a misattributed statistic were already in the
  committed doc).
- **Verification-cost calibration.** That pass cost ~40k tokens to find those 4
  defects; the user judged it poor ROI. Lesson: verify in proportion to
  load-bearing-ness (the 3–4 claims the argument rests on), not breadth.
- **Over-broad cancellation.** Asked to stop "verification," the session killed the
  two *research* agents instead (the verifier had already finished). Recovered by
  resuming the killed agents from their transcripts with a compile-only,
  no-backfill instruction — worth knowing: killed agents' contexts survive and are
  resumable, and "mark unreached sections NOT COVERED" prevents silent
  memory-backfill.
- **Structure that worked:** one synthesizer + parallel research agents (fan-out for
  read/verify only); adversarially-framed prompts ("try to REFUTE me") — which is
  what got the world-model verdict *corrected* rather than confirmed; digests
  preserved raw with corrections layered separately.

**Where everything lives:** this doc (synthesis + conclusions);
`research/01–08` (unedited digests) + `research/transcripts/` (raw JSONL);
[[grasp-experiment-reflection|grasp-experiment-reflection.md]] (the audited self-report); durable working
preferences in the machine-local memory dir
(`~/.claude/projects/-mnt-c-…-drone-catch/memory/` — auto-loaded each session,
NOT in git): examine-frames-not-just-metrics, autonomy-general-detectors-not-
failure-maps, framing-engineering-not-science.

---

### Primary sources
Anthropic, *Building Effective Agents* (2024); *Effective context engineering*
(2025); *multi-agent research system* (2025); *Agent Skills* (2025). Cognition,
*Don't Build Multi-Agents* (2025). Manus, *Context Engineering* (2025). Willison,
*Designing agentic loops* (2025). Huang et al., *LLMs Cannot Self-Correct Reasoning
Yet* (ICLR 2024). Tyen et al., *LLMs cannot find reasoning errors…* (ACL 2024).
Manheim & Garrabrant, *Categorizing Variants of Goodhart's Law* (2018). Krakovna,
*Specification gaming* (2020). Pan/Bhatia/Steinhardt, *Reward Misspecification*
(ICLR 2022). Sharma et al., *Sycophancy* (2023). Raji et al., *AI and the Everything
… Benchmark* (NeurIPS 2021). Wang et al., *Self-Consistency* (ICLR 2023); *Voyager*
(NeurIPS 2023). Brown et al., *Large Language Monkeys* (2024). Lightman et al.,
*Let's Verify Step by Step* (2023). Chen et al., *MLLM-as-a-Judge* (ICML 2024). Park
et al., *Generative Agents* (2023). Packer et al., *MemGPT* (2023). Mem0 (2025).
Xu et al., *A-MEM* (NeurIPS 2025). Zep (2025). Edge et al., *GraphRAG* (Microsoft
2024). Sumers/Yao et al., *CoALA* (2023). Ma et al., *Eureka*/*DrEureka* (2023/24).
Google, *AI co-scientist* (2025). Sim-to-real reality-gap survey (2025).
