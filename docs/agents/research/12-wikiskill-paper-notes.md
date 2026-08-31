---
tags:
  - research-digest
---

# 12-wikiskill-paper-notes — full paper read

> **Unlike digests 01–11, this is NOT a subagent digest — it is the
> meta-observer session's own notes from reading arXiv 2608.27454 in full**
> (28 pp; main body, algorithm, ablations, case study, limitations, related
> work), 2026-08-31, after the human surfaced the paper the roll-forward sweep
> missed. Feeds the [[loop-engineering-analysis|analysis doc]] Part VII.1
> addendum (the condensed version); this file is the detailed reference.
> Confidence: paper-read (primary source), not press-mediated.

**WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill
Evolution.** Tang, Rashtchian, Ferng, Tomkins, Juan, Vu — Google Research +
Virginia Tech, arXiv 2608.27454, 27 Aug 2026. Named inspiration: Karpathy's
"LLM Wiki" gist (compile experience into persistent, compounding knowledge).

## 1. Problem framing

Skill-evolution methods (EvoSkill, Trace2Skill, SkillOpt) iterate: roll out →
analyze traces → edit skills → gate on validation. Their shared defect: the
INSIGHTS driving skill edits stay scattered across optimization artifacts
(proposal histories, rejected-edit feedback) — no separate, evolving knowledge
representation. WikiSkill inserts a persistent knowledge layer between raw
experience and executable skills. This is exactly the gap our design fills
with iteration_findings + the validity ledger between raw logs and the
[[grasp-goal2-loop-spec|loop spec]]'s active principles.

## 2. Architecture — three layers (workspace = a filesystem)

| Layer | Dir | Mutability | Contents | Our analogue |
|---|---|---|---|---|
| Raw | `raw/` | immutable, write-once | complete execution traces: reasoning, tool calls, outputs, answers | committed run logs + `research/transcripts/` |
| Wiki | `wiki/` | compounding, NEVER rolled back | see below | [[iteration_findings::iteration_findings.md]] + validity ledger + [[goal2-observer-notes::observer notes]] |
| Skill | `skills/` | reversible (gated, rollbackable) | active procedural instructions | the loop spec's [[grasp-goal2-loop-spec#^3::§3]] principles + standing requirements |

Wiki layer internals (the part worth copying):
- `patterns/*.md` — ONE file per failure mode or successful strategy, with
  actionable workarounds AND per-iteration evidence citations ("Iter 0:
  train: 00, 02 | Iter 1: train: 01…") — episode links, maintained as data.
- `index.md` — one-line-per-pattern catalog, revised whenever patterns change
  (the MEMORY.md pattern; token cost O(index)).
- `logs.md` — chronological evolution log, appended each iteration by the
  Wiki Maintainer.
- `skill-impact.md` — **written PROGRAMMATICALLY by the outer-loop harness**
  after each validation gate: proposal metadata, target skill, unified diff,
  validation score, Accepted/Rejected. An objective audit trail no agent can
  fail to maintain. ⭐ The single best idea to steal: provenance by
  construction, not by agent discipline — directly answers our chimera
  episode (a figure re-attached to the wrong run by summary-relay).

Skill internals: each skill dir = `SKILL.md` (frontmatter name/description +
full procedural instructions + applicability conditions) + **`PURPOSE.md`
mapping the skill back to the motivating wiki patterns** — our `derived_from:`
field, shipped. Skills are injected in FULL into the inference prompt (no
retrieval — deliberately, to remove triggering/retrieval as a confound; their
stated limitation).

## 3. The loop (Algorithm 1)

State per iteration k: (S_k skills, W_k wiki), both start empty. R_best
initialized from a no-skill validation baseline.

1. **Inference Agent** rolls out training tasks with S_{k-1} injected;
   traces → `raw/`. **Wiki access BARRED during rollouts** (see §5 ablation).
2. **Wiki Maintainer** gets full wiki + a stratified SAMPLE of pass/fail
   traces (context-budget control); does root-cause analysis on failures,
   extracts strategies from passes; creates/patches pattern pages
   (incremental edits, not rewrites); updates `index.md`; appends `logs.md`.
   No cap on patterns per iteration — its judgment call.
3. **Skill Proposer** (multi-turn ReAct): initially given only the wiki
   INDEX + `skill-impact.md` + a one-line-per-task outcome summary; pulls
   specific pattern pages and raw traces on demand via read_file — JIT
   retrieval over an index ([[loop-engineering-analysis#^6|§6]].2's design,
   independently arrived at). Emits ONE atomic proposal per iteration:
   create one skill or patch one skill.
4. **Gating & Rollback**: apply proposal → evaluate on validation split →
   accept iff score STRICTLY improves R_best (update R_best), else roll back
   skills. **The wiki is never rolled back either way.** Harness appends the
   outcome to `skill-impact.md`. Early-stop if validation hits 100%.

## 4. Results (5 benchmarks: LiveMath, SealQA, SpreadSheet, OfficeQA,
ALFWorld; 5 models: Qwen-3.5-4B/9B, Qwen-3.6-27B, Gemma-4-31B,
Gemini-3.5-Flash; 3 independent evolution runs each, paired bootstrap p<0.05)

- Beats EvoSkill/Trace2Skill/SkillOpt on average for every model (+3.3 to
  +12.0 over the strongest competitor per model). Gemini-3.5-Flash avg
  49.5→68.1; Qwen-27B 39.4→63.3.
- **Gains INCREASE with model scale** (Qwen family: +12.3/+17.5/+23.9 for
  4B/9B/27B) — skill evolution complements scaling. Yet skills compensate for
  scale: 9B+skills (47.4) beats 27B bare (39.4).
- Benchmark-dependent: big gains where procedural workflow is the bottleneck
  (SpreadSheet +40.9 for 27B; LiveMath +20–40 across models); small where
  long-context execution is the bottleneck (OfficeQA; a 4B can't execute the
  multi-step search workflow it's handed and reverts to default behavior).

## 5. The two ablation findings that matter for our design

1. **Persistence is the load-bearing component**: proposer WITH wiki vs
   without = 63.7 vs 48.7 avg (+15.0). Without accumulated knowledge the
   proposer "struggles to resolve intricate failure modes" (re-proposes
   rejected ideas, misses recurring errors).
2. **Executor isolation from the knowledge layer**: giving the Inference
   Agent wiki access during training rollouts DEGRADES final skill quality
   (63.7→60.9; LiveMath 72.6→64.8). Hypothesized mechanism: the executor
   solves tasks from the wiki instead of the skills, making its traces less
   informative for skill development. **A second, independent argument for
   layer isolation beyond our anchoring safeguard
   ([[grasp-goal2-loop-spec|loop spec]] §0.3): isolation protects the
   LEARNING SIGNAL, not just judge objectivity.**

## 6. Cross-model transfer (Table 2 — refines [[10-generic-vs-specialized-loops|digest 10]])

- Skills transfer across scales AND families; foreign-evolved skills
  sometimes BEAT self-evolved (9B on ALFWorld: 70.2 with 27B's skill vs 63.4
  with its own; 4B skills lift Gemma-31B on LiveMath 33.9→73.1). Small→large
  transfer works. "Skill DISCOVERY and skill EXECUTION are distinct
  capabilities" — supports our asymmetric role/model assignments
  (Sonnet worker, Opus lead).
- **Negative transfer has a specific signature**: skills encoding
  MODEL-SPECIFIC WORKAROUNDS (a 4B's single-line-Python crutches, fragmented
  diagnostics burning the interaction budget) throttle stronger models
  (Gemini on SpreadSheet 50.5→18.1 with 4B skills, →63.4 with 27B skills).
  Same taxonomy as digest 10 / VII.2: general procedures transfer;
  capability workarounds don't and should be pruned on model upgrade.
- Execution capability gates the value of transferred knowledge: the same
  27B SpreadSheet skill gives +18.4/+26.2/+40.9 to 4B/9B/27B.

## 7. Case study mechanics (ALFWorld, Qwen-27B — Figure 3)

Iter 0: Maintainer writes `take-examine-move-loop.md`; Proposer's
`goal-directed-action` skill REJECTED (val 0.72). The rejection + diff live
in `skill-impact.md`. Iter 1: informed by that recorded rejection ("too
abstract"), Proposer writes `break-repetition-loop` with a concrete rule —
ACCEPTED (0.78); its `PURPOSE.md` cites both the pattern and the prior
rejection. Iter 4: new pattern evidence accumulates → skill refined with a
second rule. Rejected work compounding into accepted work via recorded
provenance — the mechanism our consolidation pass specifies, demonstrated.

## 8. Stated limitations (theirs) ↔ our open ground

| Their limitation | Our position |
|---|---|
| No skill retrieval/triggering story (full injection) | same open question; Skills/progressive disclosure is the intended mechanism |
| Strict-improvement gating rejects neutral-now/enabling-later proposals | our finding-vs-preference tags + deferred-with-trigger tier are precisely for these |
| **No wiki pruning mechanism** — accumulation unbounded | our lifecycle (fires/catches scoring, demotion, TMS-style staleness propagation via `derived_from:`) is the missing half — **our main differentiator** |
| Not tested on very-long-horizon tasks; no online (within-rollout) adaptation | matches our milestone-cadence design; untested for us too |
| (implicit) gating presumes ground-truth validation sets | the open-ended-engineering gap: our analogue is known-answer/drift runs ([[loop-engineering-analysis|analysis]] §II.3, Part VI #7) — still nobody's solution |

## 9. What to actually adopt here (concrete, small)

1. **Harness-written audit trail** (`skill-impact.md` pattern): the Goal-2
   run log's gate verdicts should eventually be appended by tooling, not by
   the lead's prose — kills the summary-relay error class structurally.
2. **`PURPOSE.md`-style back-links** on every ratcheted check (which episode
   paid for it) — we specify this (`derived_from:`); they show it working.
3. **Pattern pages with per-run evidence citations** — iteration_findings
   sections already approximate this; the delta is citing run/task IDs as
   data, not prose.
4. Keep executor/knowledge-layer isolation as a design rule (two independent
   mechanisms now: anchoring + learning-signal protection).
5. Their related work maps a whole 2026 subfield the roll-forward missed
   (EvoSkill 2603.02766, Trace2Skill 2603.25158, SkillOpt 2605.23904,
   SkillOS 2605.06614, HarnessX 2606.14249, Self-Harness 2606.09498,
   AutoHarness 2603.03329, Meta-Harness 2603.28052, agentic-harness-
   engineering 2604.25850, SoK 2602.20867) — sweep candidate if scaffold
   self-evolution becomes our critical path.
