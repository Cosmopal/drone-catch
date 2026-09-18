---
tags:
  - agent-loop
---

# Three-session agent-team workflow — roles, protocol, and machine-resume guide

> The ONE document to read when resuming this project's pseudo-agent-team on a
> new machine. Everything here is either state (committed, with pointers) or
> protocol (how the three sessions work together). Written 2026-09-19 by the
> meta-observer session at the human's request before a machine move.
> Companion state docs: [[goal2-run-log|goal2-run-log.md]] (the loop's event
> log, owned by the lead), [[goal2-observer-notes|goal2-observer-notes.md]]
> (the meta-study ledger, owned by the observer),
> [[grasp-goal2-loop-spec|grasp-goal2-loop-spec.md]] (the loop contract).

## 1. The three roles (as run 2026-08-31 → 2026-09-19)

| Session name | Model | Role | Owns (docs) | Never does |
|---|---|---|---|---|
| `drone-catch-meta` | Fable | **Meta-observer / AI researcher.** Studies the loop itself: logs every gate catch, human nudge (+faculty tag), error (all layers incl. its own), hypothesis score. Runs research passes (literature, hardware envelope). Feeds consolidation. | [[goal2-observer-notes|observer notes]], [[loop-engineering-analysis|analysis doc]] Parts VII+, `research/` digests, `concepts/14` | Coordinate the loop; approve work; touch the worktree's code |
| `grasp-iter-lead` | Opus | **Lead.** Routes worker reports through gates (verifier→reviewer→critic, fresh-context Sonnet subagents), keeps the run log, escalates per spec §4, adjudicates detector promotions, writes gate briefs (never stating expected outcomes). | [[goal2-run-log|run log]], prereg diffs, gate briefs | Mark work done itself; relay a figure without re-deriving from artifact; put prereg/human-prior in gate contexts |
| `grasp-iter-2` | Sonnet | **Worker.** Builds + measures in the worktree (`.claude/worktrees/grasp-iter2`, branch `grasp-iter2`). Owns the conda env (may fix packages; may NOT change pybullet/numpy/python versions mid-study). Commits logs+code with every number. | worktree code, committed run ledgers, evidence dirs | Self-approve; report a number without committed code + evidence at the human's medium |

**The human** decides milestone scope, design rulings, and supplies the
faculties the run showed aren't mechanized: physical-realism/mechanism design
(most consequential), evidence-medium discipline ("show me" — most frequent),
experiment-design judgment (most structural). Human messages are logged as
nudges with faculty tags — that count is the study's primary metric.

## 2. Communication protocol

- Sessions message each other by session NAME (Claude Code cross-session
  messaging; `ListAgents` to discover; disambiguate by `[ref]` if duplicates).
- Worker reports → lead. Lead routes to gates, then sends the observer a
  one-paragraph summary per gate verdict / escalation (verdict, which role
  caught what, nudge count). Observer replies with logging confirmations and
  flags — the observer has NO authority over the loop.
- Report shape (worker→lead): per-gate command + verdict line + worktree SHA;
  causal claims with perturbation tables + evidence paths; side-by-side
  reproduction cells; not-tested list; trust recommendation.
- Standing rules earned during the run (full reasoning in the
  [[goal2-observer-notes|observer notes]] and run log — the spec §0.3/§6
  amendments carry most):
  1. Prereg isolated from all gates; predicted-vs-observed diffed by the lead
     AFTER blind scoring. Human priors sealed the same way (limit: a prior
     encoded in the experiment's DESIGN cannot be sealed — score
     asymmetrically: refutation strong, confirmation weak).
  2. Briefs name rival hypotheses + discriminating experiments; NEVER the
     expected winner or which result is "convenient" (read-back test).
  3. Causal claims from grounded roles state the MECHANISM or return
     UNDERDETERMINED ("my medium can't separate the hypotheses" → render).
  4. Evidence coverage attaches when a claim becomes DECISION-DRIVING, in the
     human's review medium (video for temporal behavior), not when its cell
     was planned. Non-rotating evidence paths.
  5. Every number traces to committed CODE (not just a log).
  6. The evidence set contains ≥1 element selected independently of the
     hypothesis — name the referent (prediction / scoring / design).
  7. Convergence certificates are per-METRIC and never transfer to
     finer-grained metrics.
  8. Paired comparisons share declared numerics (solver iterations included).
  9. Direction words name their referent ("cup mouth faces…", not "points…").
  10. A retraction requires the same evidentiary standard as the claim it
      retracts (watch item at 2 episodes, adjudication pending).

## 3. Resume procedure on a new machine

1. **Clone/pull the repo.** Branches: `main` (current, includes ported core
   code + all docs), `grasp-iter2` (the study worktree branch — recreate the
   worktree: `git worktree add .claude/worktrees/grasp-iter2 grasp-iter2`).
2. **Environment** (Windows recipe; adapt paths elsewhere): install Miniconda
   (user scope); `conda create -n robots python=3.11 numpy`; pybullet from
   conda-forge (`conda install -n robots -c conda-forge pybullet` — PyPI has
   NO Windows wheels); `pip install imageio imageio-ffmpeg matplotlib` in the
   env. **Record the versions installed** — the study's paired comparisons
   are valid only within one build (this run: python 3.11.16, numpy 2.4.6,
   pybullet 3.25/conda-forge). A version change = re-validate one committed
   baseline cell before trusting new numbers, and a validity-ledger note.
3. **Reinstall the post-commit hook** (`tools/hooks/post-commit` →
   `.git/hooks/post-commit`) and re-point the Obsidian sync path if the vault
   moved (see CLAUDE.md "Obsidian notes sync").
4. **Seed session memory**: copy `docs/agents/memory-mirror/*.md` into the new
   machine's `~/.claude/projects/<this-repo's-project-key>/memory/`. (The
   mirror is a snapshot — check `grasp-iter2-state.md` against
   [[grasp-iter2-STATUS|the STATUS doc]] and update if stale. After seeding,
   keep the mirror in sync when memories change.)
5. **Recreate the three sessions** (names matter — they're the message
   addresses):
   - `grasp-iter-2` (Sonnet), cwd = the worktree. Seed: "You are the WORKER
     in the Goal-2 gated loop. Read docs/agents/team-workflow.md §1–2, then
     grasp-goal2-loop-spec.md, then goal2-run-log.md tail for current state.
     Await the lead's brief."
   - `grasp-iter-lead` (Opus), cwd = main checkout. Seed: "You are the LEAD.
     Read docs/agents/team-workflow.md, then goal2-run-log.md in full (your
     own log — resume it), grasp-goal2-loop-spec.md, and the observer notes'
     last 3 entries. State the current milestone status and pending human
     rulings back to the human before acting."
   - `drone-catch-meta` (Fable or successor), cwd = main checkout. Seed: "You
     are the META-OBSERVER. Read docs/agents/team-workflow.md §4 (your role
     learnings), goal2-observer-notes.md in full (your own ledger — resume
     it), and loop-engineering-analysis.md Part VII. You log, research, and
     flag; you never coordinate."
6. **Verify the mesh**: have the lead message both other sessions; confirm
   receipt; then the lead recites current state (from the run log) and the
   human confirms or corrects. Do not resume experiments before that
   recitation matches the human's understanding.

## 4. Observer-role learnings (for my successor — hard-won, follow them)

1. **Verify before relaying, against the primary artifact.** Every layer that
   consumed a summary propagated the run's false figure; the role pointed at
   the artifact stopped it. When the lead corrects you, re-verify the
   correction at source too (corrections-of-corrections are where deference
   is cheapest and most dangerous).
2. **Supersede, never delete.** Corrections are appended with the original
   struck/marked; both readings preserved. Twice this run an over-retraction
   destroyed true information — over-claiming and over-retracting are one
   scope-error class in opposite directions, and retractions get audited
   less because they read as humility.
3. **Your own errors go in the ledger, named and numbered.** Observer errors
   1–9 are in the notes; the direction pattern (framework-flattering) is
   itself a finding (H7), though unscoreable without deliberate sampling of
   modest claims.
4. **Don't promote your own proposals.** Flag candidates with episodes and
   caveats; the lead/consolidation adjudicates. The promotion bar: ≥2 local
   refutation-capable episodes, OR structural recurrence, OR study-wide blast
   radius × ~zero carry cost. Scope any new detector to its MARGINAL
   coverage, not its motivating pattern.
5. **Score catches, not character.** Displays of epistemic virtue (cheap,
   visibly logged: self-flagging, declining credit, admitting error) are
   contaminated evidence — the scoring supplies the incentive. Behavioral
   claims are admissible only when the action COST something and left an
   artifact. State this in any write-up's limitations (H5/H7 partly measure
   the observation apparatus).
6. **Cap meta-recursion.** The observation study is downstream of the loop
   producing results, never a substitute. When gate work is pending, hold
   design discussion. (The lead imposed this once; impose it on yourself.)
7. **Archive raw agent outputs immediately** — subagent transcripts
   intermittently flush empty (3 instances); stat the file before relying on
   it and preserve the digest from the completion message verbatim when
   empty, noting availability in the archived header.
8. **Author tags + wikilinks inline** per CLAUDE.md's Obsidian conventions;
   commit after every substantive entry; everything of value lives in git,
   never only in conversation (this document exists because that rule was
   almost violated at machine scale).

## 5. State snapshot at handoff (2026-09-19 — verify against the run log,
which is authoritative if they diverge)

- **M-A closed** (gate A trustworthy 108/108 under attack; gate B demoted to
  informational; env shift exonerated). **M-B closed by human decision**:
  failed as science, succeeded as metrology (placement invalid above ~3.5 cm
  — ball spawned overlapping a finger; lateral offset was the mechanism's
  weakest axis; OAT convergence inadequate for marginal claims; pull-in not
  substep-converged at large offsets).
- **Next phase (agreed in shape, prereg NOT yet written)**: fixed-base
  axis-aligned dynamic catch — feasibility envelope, speed × lateral miss →
  catch rate; passive `prb` alone first; dished palm in the baseline.
  Pending human rulings: two-phase pose (meet arrival-aligned → rotate
  vertical to hold) in/out of first build; sweep ranges. The human's
  pre-registered prior is on record ("a very simple hand with just compliant
  material will be decently performative") with the asymmetric scoring
  protocol fixed in advance.
- **Consolidation queue (the M-D-style distillation pass, not yet run)**: the
  PROPOSE/design-audit gate (the run's unifying gap — every detector audits
  execution, none audits design); D9 extended to actuators; scope detector
  promoted; sample-generation-bias promoted; situation-fidelity promoted;
  per-metric convergence certificates; finding-vs-preference tagging of the
  spec; compile-coverage check (H6, 3 instances); gate lifecycle stats.
- **Hypotheses live**: H1–H2 supported/confirmed, H3 finally has an at-risk
  prediction (score at dynamic-catch close, asymmetrically), H4 strongly
  supported (one milestone), H5/H6 supported within stated limits, H7
  unscoreable as designed. Full scoring in the observer notes.
- **Hardware envelope** ([[14-hardware-envelope|concepts/14]]): 5″ class,
  real AUW 900 g–1.1 kg; hand floor ~150–250 g (Model T topology); no
  back-drivable cheap actuator (series-elastic or dish-as-compliance);
  2–4 min/pack endurance; thrust-vectoring cost raised.
