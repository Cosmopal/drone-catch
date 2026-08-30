# Grasp iteration-2, Goal 2 — gated-loop spec (loop design v2)

> The first loop designed *from* the meta-analysis (`loop-engineering-analysis.md`)
> rather than before it. It resumes the grasp work (Goal 2 of
> `grasp-iteration2-spec.md` §2.5–2.7, on branch `grasp-iter2`) AND serves as the
> observed test case for the loop design itself — we run it, watch where it needs
> human input, and score the design against the §II.3 metric (human-nudges-to-truth).
> Launched 2026-08-31 from the meta-analysis session.

## 0. What changed vs. the iteration-2 loop (design deltas, each with a reason)

1. **Verifier and critic are now SEPARATE roles** (they were fused in the single
   "reviewer"). The reviewer conflated two different faculties:
   - **Verifier** — *grounded*: actually re-runs the worker's verdict-bearing
     results under perturbation (timestep × contact × seed, plus one ablation per
     causal claim). Owns D3 (convergence) and D5 (causal soundness). Its currency
     is executed evidence, never opinion. *Perturb, don't repeat*: it must vary
     something on every re-run.
   - **Critic** — *enumerative/adversarial*: never runs anything; enumerates what
     was NOT tested, whether the testbed can even see the property claimed, and
     what the cheapest experiment to break the claim would be. Owns D4
     (completeness) and D6 (falsifiability).
   - **Reviewer** — *perceptual*: judges claims against rendered frames only. Owns
     D1, D2, D7, D8, D9 + provenance.
   Reason: §II.1 — homogeneous judges converge on shared delusions; the panel needs
   deliberately different attention targets, and ≥1 member (the verifier) must be
   grounded.
2. **Two-tier ratchet — principles in context, checks in code.** (Addresses the
   context-bloat concern.) The always-loaded layer is a SMALL fixed set of general
   principles (§3 below, ~8 lines). Every specific human/loop catch is ratcheted as
   an **executable check in the repo** (a harness flag, a test, an assert), indexed
   by one line in the validity ledger — NOT as accumulating prompt text. Context
   cost stays O(principles + index); the specifics cost tokens only when a gate
   fires. Periodic distillation (§6) merges specific checks back into the general
   principles, with provenance links kept so a principle's merit can be re-audited
   against the episodes that motivated it.
3. **Pre-registration block ("vision", defeasible).** Before each experiment the
   worker writes down, in the run log, (a) the *predicted qualitative behavior*,
   anchored where possible in published behavior of the mechanism (e.g. "Yale-class
   adaptive hands re-center off-center objects toward the palm; literature shows
   passive re-seating, not ejection"), (b) the falsifier, (c) confidence. A result
   that *violates* the pre-registered expectation is an anomaly to investigate
   before it can be reported either way; a result that *confirms* it still needs
   the normal gates (a wrong prior can be spuriously confirmed — the "gaps too
   large" episode). The prior directs attention; it never decides verdicts.
   **Safeguards (from the Aug-2026 vision research):**
   - *Context isolation* — the pre-registration is NEVER passed to the verifier or
     reviewer (anchoring in LLM judges survives even explicit "disregard this"
     instructions, arXiv 2608.25869). The lead strips prereg content from what the
     gates see; the predicted-vs-observed diff is a separate lead/critic step
     AFTER the gates have scored blind.
   - *Asymmetric authority* — a violated expectation raises scrutiny (triggers
     convergence + mechanism checks); a confirmed expectation lowers nothing.
   - *Provenance tags* — each prediction is tagged literature-backed / analogy /
     guess, with citation where literature-backed; untagged vibes get no detector
     status.
   - *Prior-robustness* — if a verdict would change with the prior removed, it is
     not earned yet.
4. **Milestone-gated, lead-routed.** The worker runs one milestone at a time and
   STOPS; the lead routes its output through verifier → reviewer → critic before
   the next milestone starts. A failed gate routes BACK (revise), never forward.

## 1. Roles

| Role | Who | Reads | Produces | Must NOT |
|---|---|---|---|---|
| Lead | the orchestrating session | everything | routing decisions, human escalations | mark work done itself; relay-without-checking |
| Worker | sub-agent in worktree `.claude/worktrees/grasp-iter2` (branch `grasp-iter2`, conda `robots`) | spec + iteration_findings §26–29 + concepts/13 | code, runs, logs, frames, pre-registrations, claims | self-approve; touch main; report a number without a frame + committed log |
| Verifier | fresh-context sub-agent, grounded | worker's claims + repo | executed perturbation tables, ablation results, CONFIRMED/NOT-CONFIRMED per claim | trust the worker's runs; re-run identical configs |
| Reviewer | fresh-context sub-agent, perceptual | frames + claims + logs only | APPROVED / REVISE with per-detector, per-frame citations | re-run experiments to rationalize; approve without frame coverage |
| Critic | fresh-context sub-agent, adversarial | final claims + spec | untested-axes list, falsifiability challenges, cheapest-break proposals | run experiments; soften findings |

Fresh context per gate is deliberate (self-conditioning: an agent marinating in its
own claims loses the ability to doubt them). If any role runs as a separate Claude
Code session rather than a sub-agent, coordination uses native session messaging;
the lead's job is unchanged.

## 2. Milestones (Goal 2 per iteration-2 spec §2.5–2.7)

- **M-A (setup + pre-registration):** confirm regression gates green on the
  worktree (`arm_catch_solo --grid` 12/12; `elbow_catch_solo --headless`
  caught=True held=True); write the pre-registration for adaptive re-centering
  (predictions + falsifiers + literature anchor). Gate: lead sanity-check only.
- **M-B (adaptive re-centering, §2.5):** a close that senses/adjusts for an
  off-center ball (or exploits the PRB hand's passive re-centering actively),
  measured on the quality metrics (escape-margin, centeredness, #contacts,
  symmetry) vs the rigid close, per offset × direction, convergence-checked,
  frames beside every number. Gate: verifier → reviewer.
- **M-C (dynamic layered test, §2.6):** SEPARATE from the static study — ball
  velocity × approach angle × catch pose vs trajectory, quality at capture;
  gravity-on / momentum-seated regime (the faithful hand's fair regime). Static
  and dynamic claims never conflated (D7). Gate: verifier → reviewer.
- **M-D (close-out, §2.7):** explicit not-tested list; findings doc; validity-
  ledger updates. Gate: critic → reviewer final APPROVED → distillation pass (§6).

## 3. The always-loaded principle set (the ONLY prompt-text layer; everything else is code or on-demand)

1. Determinism ≠ convergence — no contact verdict counts without perturbation
   invariance (dt × contact model × seed).
2. Verify by perturbing, never by repeating.
3. No metric without its frame; no "success" that looks precarious.
4. A causal claim requires its ablation.
5. A verdict on property X requires the testbed to demonstrably separate X from
   not-X (else: "unfalsifiable here", stop).
6. A mechanism verdict requires a faithful mechanism, not a behavioral stand-in.
7. Static-proxy and real-task claims stay attributable — never conflated.
8. A negative requires a diagnosis (tunable-config vs sim-fundamental), not a shrug.

(D1–D9 of the iteration-2 spec are the per-role renderings of these; the ratchet
adds *executable* checks, and distillation folds them back into this list only if
they generalize.)

## 4. Escalation to the human (thin, and every escalation is logged as data)

Hard-stop and escalate when: a gate fails twice on the same claim; the verifier
and worker disagree on a converged result; a pre-registered expectation is
violated and the investigation doesn't localize a cause; anything requires
physical-realism judgment (masses, forces, "would a real part do this") — the one
faculty §II.2 marked not mechanizable. Everything else proceeds without asking.
Each human message received is logged with what faculty it supplied — that log IS
the experiment's primary metric (human-nudges-to-truth, target: fewer than
iteration 2's count for equivalent scope).

## 5. Observability

Worker commits after every milestone (additive, worktree branch only). The lead
keeps a run log (`docs/agents/goal2-run-log.md`) recording: milestone starts/ends,
gate verdicts, escalations, human messages + faculty, pre-registration outcomes
(predicted vs observed). This is the raw material for the loop's own analysis.

## 6. Distillation pass (at M-D close)

A consolidation step reads the run log + any new ratcheted checks and:
- merges redundant specific checks; promotes a check to the §3 principle list ONLY
  if it fired in ≥2 distinct contexts or is clearly domain-general;
- annotates every principle/check with `derived_from:` episode links (findings §,
  run-log entries) so merit is debuggable later;
- supersedes (never deletes) anything overturned;
- records per-gate lifecycle stats from the run log: fires/run, catches (fires
  that changed a verdict), cost — zero catches over N runs marks a gate a
  demotion candidate; a superseded episode flags every principle justified only
  by it (TMS-style staleness propagation via `derived_from:` links);
- prunes capability workarounds that a model upgrade made unnecessary, but keeps
  verification gates (they compensate for simulator/measurement deficits, which
  model upgrades don't fix);
- updates the validity ledger and this spec — the spec is an OUTPUT of the run.
