---
tags:
  - research-digest
---

# 09-rollforward-aug2026 — raw research digest

> Unedited final digest from a research subagent spawned by the meta-analysis
> session on 2026-08-31 (the extension pass: full-mission generalization).
> Topic: Roll-forward of the July research to 2026-08-31 (new/updated literature).
> Raw transcript: `transcripts/09-rollforward-aug2026.jsonl`. Citations are as-produced by the
> agent and NOT independently verified (per the verification-ROI lesson, only
> load-bearing claims get verified, at use time).

---

All research threads are complete. Here is the digest.

---

# Research roll-forward digest: loop-engineering analysis (May–Aug 2026)

Rolling [[loop-engineering-analysis|docs/agents/loop-engineering-analysis.md]] (written 2026-07-04→06) forward to 2026-08-31. Sections: (a) what changed, (b) per-thread findings, (c) no-change list.

## (a) What changed since July — items that MODIFY the doc's conclusions

1. **MODIFY — Part V "Sizing human oversight" numbers are stale/overstated.** The doc says "doubling every ~3–4.5 months" and "80%-horizon ~1–3 h." METR's current fit (page updated May 8, 2026, latest models Claude Mythos Preview, GPT-5.4, Gemini 3.1 Pro) gives a **~7-month doubling (213 days for the 80% threshold, 212 for 50%)** — the faster 2024–25 doubling did not hold as the headline trend. Worse for precision: METR's own March 2026 methods note shows **alternative reasonable fits move 50% horizons −35% and 80% horizons +100%** (Opus 4.6: ~1.5×/2× spread), human-baseline noise could cut recent 50% horizons another 25–40%, and **"measurements above 16 hrs are unreliable with our current task suite."** The doc's *qualitative* advice (size check-ins to the 80% horizon, not the 50%) survives; the specific hour figures should be flagged as ±2× and the doubling rate corrected. Sources: [METR time horizons](https://metr.org/time-horizons/), [METR 2026-03-20 modelling-assumptions note](https://metr.org/notes/2026-03-20-impact-of-modelling-assumptions-on-time-horizon-results/), [METR 2026-01-22 limitations note](https://metr.org/notes/2026-01-22-time-horizon-limitations/).

2. **MODIFY (nuance) — self-conditioning is partially mitigated by thinking modes.** Sinha et al. (v3 updated Mar 13, 2026) explicitly find **"thinking mitigates self-conditioning"** and extends single-turn execution length; scaling alone does not. The doc's design consequence (gates external to the agent's context) still holds, but the claim should note reasoning-mode models resist marinating in their own errors better than the doc implies. Source: [arXiv 2509.09677](https://arxiv.org/abs/2509.09677).

3. **MODIFY (new principle for the ratchet) — gates go stale as models improve.** Anthropic's "Harness design for long-running application development" (Mar 24, 2026) reports that Opus 4.6 **eliminated the need for their sprint-based decomposition**, and states the load-bearing line: *"every component in a harness encodes an assumption about what the model can't do on its own."* The doc's ratchet only adds gates; it has no retirement mechanism. Suggested amendment: a periodic "gate-pruning" pass (re-run the known-answer suite with a gate disabled on a new model; retire gates that no longer fire). Source: [anthropic.com/engineering/harness-design-long-running-apps](https://www.anthropic.com/engineering/harness-design-long-running-apps).

4. **CONFIRM-and-strengthen — scheduled reflection/consolidation is now a shipped product.** Anthropic **"Dreaming"** for Claude Managed Agents (announced May 6, blog May 19, 2026): a scheduled between-session process that reads transcripts + memory stores, extracts patterns, merges duplicates, **replaces stale entries**, and rewrites memory — explicitly modeled on hippocampal consolidation, with optional human review of memory diffs. Harvey reported **~6× task-completion improvement**. This is [[iteration_findings#^6|§6]].4 ("the goal doc becomes an output of analyzing the logs") productized — the doc's most speculative recommendation is now vendor-validated. Same release: **"Outcomes"** = a separate-context rubric grader (+up to 10 pp task success) — direct validation of generator/verifier separation with fresh context ([[iteration_findings#^4|§4]].1, Part V self-conditioning argument). Source: [claude.com/blog/new-in-claude-managed-agents](https://claude.com/blog/new-in-claude-managed-agents), [The New Stack coverage](https://thenewstack.io/anthropic-agent-memory-dreaming/).

5. **CONFIRM — "loop engineering" went from coinage to mainstream discipline in June 2026.** Addy Osmani formalized "Loop Engineering" (June 7, 2026, after Boris Cherny's "I don't prompt Claude anymore. I write loops that prompt Claude"); the official Claude blog published "Loop engineering: Getting started with loops" (June 30, 2026 — four loop types, stopping conditions, token management). The doc's framing is now the field's standard vocabulary, not an extrapolation. Sources: [addyosmani.com/blog/agent-harness-engineering](https://addyosmani.com/blog/agent-harness-engineering/), [O'Reilly Radar version](https://www.oreilly.com/radar/agent-harness-engineering/), [codecentric terminology explainer](https://www.codecentric.de/en/knowledge-hub/blog/loop-harness-context-engineering-explained).

6. **CONFIRM (with teeth) — automated scaffold self-design still doesn't beat expert design.** "The Illusion of Multi-Agent Advantage" (arXiv 2606.13003, Jun 2026): **automatically generated multi-agent systems consistently underperform CoT-SC at up to 10× the cost**; expert-designed MAS beat auto-generated; auto-design produces "architectural bloat." This is empirical backing for Part V's "earn your complexity" and for keeping ADAS/Gödel-Agent machinery in the not-earned bin. Source: [arXiv 2606.13003](https://arxiv.org/pdf/2606.13003).

## (b) Per-thread findings

### Thread 1 — load-bearing citations

- **Huang et al. (Cannot Self-Correct):** core finding unchallenged as of Aug 2026. The active follow-up line is *trained* (not prompted) self-correction: **SCoRe** (RL-based, ICLR 2025, [arXiv 2409.12917](https://arxiv.org/pdf/2409.12917)) shows genuine intrinsic gains via training; **Self-Correction Bench** ([arXiv 2507.02778](https://arxiv.org/html/2507.02778)) characterizes a "self-correction blind spot." Loop-level implication unchanged: without training your own model, external grounded feedback is still required.
- **Tyen et al. (detection is the bottleneck):** confirmed, extended. "LLMs cannot spot math errors, even when allowed to peek into the solution" ([arXiv 2509.01395](https://arxiv.org/pdf/2509.01395)) and CoT-error-diagnosis work ("When the Chain Breaks," [Computer Graphics Forum 2026](https://onlinelibrary.wiley.com/doi/10.1111/cgf.70439)) both re-find that localization, not repair, is the weak link. No refutation found.
- **METR:** see (a)(1). Also note a no-CoT horizon paper ([arXiv 2606.07157](https://arxiv.org/pdf/2606.07157)) and "half-life" reanalysis ([arXiv 2505.05115](https://arxiv.org/pdf/2505.05115)) — the constant-hazard/half-life model is the main alternative framing.
- **Sinha self-conditioning:** see (a)(2).
- **Agent Skills:** Anthropic published "Equipping agents for the real world with Agent Skills" ([anthropic.com/engineering](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)) — Skills as procedural memory is now the productized Voyager-skill-library pattern the doc recommended.

### Thread 2 — loop/harness/context engineering as practitioner discipline

- See (a)(3, 5). Key additions from the Anthropic harness post beyond the gate-staleness point: **generator/evaluator "sprint contracts"** (success criteria negotiated *before* implementation, hard per-criterion thresholds — a gate-design pattern matching [[iteration_findings#^4|§4]].4), and three named failure modes: **self-evaluation bias** ("confidently praising the work"), **context anxiety** (premature wrap-up as the window fills), and **shallow testing** by evaluators — all consistent with the doc's [[iteration_findings#^1|§1]].
- **Evals-as-CI matured into a standard cascade**: deterministic floor (schema/regex/structural/citation checks catch 30–60% of failures) → classifier on the residual → LLM judge on the survivor sample; full judge sweeps nightly, not per-PR; **metric contract pinned in git** (rubric text, judge model id, canonical answers); statistical gating to avoid random red builds. Matches [[iteration_findings#^4|§4]].4 nearly clause-for-clause. Sources: [Confident AI agent-eval guide](https://www.confident-ai.com/blog/llm-agent-evaluation-complete-guide), [futureagi deterministic-metrics](https://futureagi.com/blog/deterministic-llm-evaluation-metrics-2026/), [QASkills CI quality gates](https://qaskills.sh/blog/llm-evaluation-ci-cd-quality-gates).

### Thread 3 — agent self-improvement of the scaffold

- **Headline:** narrow, trace-grounded optimization works and is in production; open-ended scaffold self-design does not transfer. **GEPA** (ICLR 2026 oral): reflective prompt evolution over execution traces, +13% over MIPROv2, +20% over GRPO with 35× fewer rollouts; production use at **Microsoft** (pre-training data-filter judge) and **Nubank** (judge accuracy 68.9→88.9%). Note GEPA's active ingredient is the doc's own thesis: it reads *execution traces* (grounded signal), not scalar reward. Sources: [dspy.ai GEPA overview](https://dspy.ai/api/optimizers/GEPA/overview/), [github.com/gepa-ai/gepa](https://github.com/gepa-ai/gepa).
- **Counter-evidence for open-ended self-design:** (a)(6) Illusion-of-Multi-Agent-Advantage; plus MAS-PromptBench ([arXiv 2606.23664](https://arxiv.org/pdf/2606.23664)) asking *when* prompt optimization helps MAS at all; a NeurIPS 2026 workshop "Managing Agents that Manage Agents" ([site](https://meta-agents-workshop.github.io/)) signals the community treating meta-agents as a risk/eval problem, with explicit calls for meta-level benchmarks because "leaderboards hide failure cases."
- Active harness-evolution research exists (DemoEvolve [2605.24539], FlashEvolve [2605.08520], SIA joint harness+weight updates [2605.27276], EvoAgentBench [2607.05202]) — all benchmark-bounded; none demonstrates reliable out-of-benchmark transfer. The doc's "defer DSPy-style end-to-end optimization until prompts/gates are stable" stands, with the amendment that GEPA specifically has crossed into justified-for-judge-prompt-tuning territory once you have a labeled gate history.

### Thread 4 — memory consolidation / supersession

- **Dreaming** — see (a)(4). The strongest single update to [[iteration_findings#^6|§6]].
- **Supersession is now a measured, named gap:** "Supersede: Diagnosing and Training the Memory-Update Gap" ([arXiv 2606.27472](https://arxiv.org/abs/2606.27472), Jun 2026): bounded self-maintained memory drops accuracy 92%→77%; stale-fact reliance worsens with conversation length (68%→28% at 24× length) and is **not fixed by bigger buffers or bigger models** — direct empirical support for IV.3's "first-class supersedable memory" and the anti-RAG argument (retrieving retracted [[iteration_findings#^25|§25]] next to corrected [[iteration_findings#^26|§26]]).
- **Zep vs Mem0, benchmarked:** on LongMemEval, Zep 63.8% vs Mem0 49.0%; the mechanism gap is exactly the doc's concern — Zep's edges carry valid_from/valid_to/invalid_at (temporal supersession); Mem0 has no fact-validity windows, so stale facts can win on semantic similarity. New benchmark **BEAM** includes contradiction-resolution and knowledge-update categories as first-class. Sources: [vectorize.io Mem0-vs-Zep](https://vectorize.io/articles/mem0-vs-zep), [Mem0 State of Agent Memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026).
- **Letta sleep-time compute:** quantified — ~5× reduction in test-time compute for equivalent accuracy; ~2.5× cost amortization across related queries; "memory models" trained to generate memories during downtime ([letta.com/blog/sleep-time-compute](https://www.letta.com/blog/sleep-time-compute/), [towards-agents-that-learn](https://www.letta.com/blog/towards-agents-that-learn/)).
- The doc's "defer Mem0/Zep until contradiction is the actual bottleneck" still holds for this project's scale (~dozens of memories), but if that trigger fires, the evidence now clearly points at Zep-style temporal-KG, not Mem0-style consolidation.

### Thread 5 — multi-session / multi-agent coordination in coding agents

- **Cognition softened "Don't Build Multi-Agents"** — "Multi-Agents: What's Actually Working" (Apr 22, 2026): the working principle is **"writes stay single-threaded; additional agents contribute intelligence rather than actions."** Working patterns: clean-context **code-review agent** (~2 bugs/PR caught, 58% severe — attributed to avoiding context rot and the coder's implicit biases: literally the doc's fresh-context-verifier argument), "smart friend" escalation, early manager-child delegation. Parallel-writer swarms still fail. This is the doc's [[iteration_findings#^7|§7]] reconciliation (single-threaded build, fan-out verify) confirmed by the original skeptic. Source: [cognition.com/blog/multi-agents-working](https://cognition.com/blog/multi-agents-working).
- **Claude Code practitioner consensus (2026):** three tiers — subagents (in-session, cover ~80% of needs), agent teams (independent contexts, task claiming, plan-approval gates, hooks for quality checks), background agents — with explicit advice to use the lightest tier that fits and treat inter-agent messages as expensive. Sources: [cloudzero.com claude-code-agents](https://www.cloudzero.com/blog/claude-code-agents/), [Osmani "The Code Agent Orchestra"](https://addyosmani.com/blog/code-agent-orchestra/), [hatchworks subagents-vs-teams](https://hatchworks.com/blog/claude/claude-sub-agents-and-agent-teams/).
- Anthropic's frontend/long-running work uses an explicit **generator + evaluator (GAN-inspired) pair** with Playwright-grounded evaluation — grounded verifier, not LLM-only ([Anthropic engineering](https://anthropic.com/engineering)).

## (c) No change / thin results

- **Tyen et al. refutation:** searched follow-ups and 2026 error-localization work; found only confirmations (detection remains the bottleneck). No change.
- **CoALA, Generative Agents (Park 2023), A-MEM:** searched agent-memory 2026 surveys and taxonomy papers (e.g., "Anatomy of Agentic Memory" [arXiv 2602.19320], "Hitchhiker's Guide to Agentic AI" [arXiv 2606.24937]); no new versions or refutations of these specific works surfaced — they appear as stable background citations. No change.
- **Voyager:** nothing new beyond the Agent Skills productization already noted. No change.
- **Gödel Agent / AlphaEvolve specifically:** Darwin Gödel Machine (2025) still the reference point; found no May–Aug 2026 result showing open-ended scaffold self-modification working reliably outside benchmarks (the counter-evidence in (a)(6) is the notable movement). AlphaEvolve: no major follow-up release found in the window.
- **Huang et al. direct refutation:** none found; the SCoRe/training line qualifies but does not overturn the prompting-only claim.
- **NOT COVERED:** A-Lab/SDL follow-ups (Part VI) — not in the assigned threads, not searched. Also not searched: VLM temporal-grounding updates (Part I [[iteration_findings#^2|§2]] table).

**Bottom line:** nothing overturns the doc's core thesis; the field moved *toward* it (Dreaming = scheduled reflection shipped; Outcomes = fresh-context graders; Cognition conceding read/verify fan-out; evals-as-CI cascades standardized; auto-designed scaffolds empirically losing to expert design). The three concrete edits worth making: fix the METR numbers (±2× error bars, ~7-month doubling), add the "thinking mitigates self-conditioning" nuance, and add a **gate-retirement/pruning mechanism** to the ratchet so the harness doesn't ossify around a weaker model's limitations.
