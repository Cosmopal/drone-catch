---
tags:
  - research-digest
---

# 13-chunked-vs-consolidated-docs — raw research digest

> Unedited final digest from a research subagent (Sonnet) spawned by the
> meta-analysis session on 2026-08-31. Topic: does research support the
> project's documentation strategy — chunked, indexed, wikilinked atomic notes
> vs long consolidated docs — for agent consumption? Each finding carries an
> evidence-quality tag (measured / benchmarked / practitioner-reported /
> asserted). Raw transcript: `transcripts/13-chunked-vs-consolidated-docs.jsonl`.
> Citations as-produced, NOT independently verified.

---

All six research threads are complete. Here is the digest.

---

# Digest: Chunked/Indexed/Linked vs. Long Consolidated Docs for Agent Consumption

Context read first: `loop-engineering-analysis.md` Part IV.3 (first-class memory, index-in-context/knowledge-on-disk token mechanics), §6.2–6.3 (progressive disclosure, curated-index-beats-RAG argument), and `research/12-wikiskill-paper-notes.md` §2 (WikiSkill's index.md + patterns/*.md architecture, directly analogous to this project's MEMORY.md + docs/concepts/).

## Thread 1 — Retrieval granularity (chunk size / semantic coherence)

- **Chen et al., "Dense X Retrieval" (EMNLP 2024 / arXiv 2312.06648, Dec 2023)** — controlled ablation, same corpus/retrievers, only granularity varied (propositions vs. sentences vs. passages), 5 QA datasets, 6 retrievers. Proposition-level retrieval beat passage-level: Recall@5 unsupervised +9–12 pts (SimCSE 46.3 vs 34.3; Contriever 52.7 vs 43.0); downstream EM at fixed context budget +26–55% relative. **Measured.**
- **Jina AI "Late Chunking" (arXiv 2409.04701, Sept 2024)** — embeds whole doc first, pools per-chunk after, preserving cross-chunk context. +24.5% relative nDCG@10 avg at 512-token chunks on BeIR/LongEmbed. Vendor-authored on vendor's own models — **benchmarked**, discount magnitude somewhat.
- **Vectara, "Is Semantic Chunking Worth the Computational Cost?" (NAACL 2025 Findings, arXiv 2410.13070)** — 25 chunking configs × 48 embedding models. Fixed-size chunking *beat* semantic/breakpoint chunking on retrieval, evidence-retrieval, and generation, for higher cost. **Measured**, peer-reviewed, and directly contradicts vendor marketing.
- FloTorch 2026 industry benchmark: semantic chunking over-fragmented to ~43-token chunks, 54% QA accuracy vs. 69% for 512-token overlapping fixed chunks. **Practitioner-reported/benchmarked.**
- Popular "semantic chunking transforms RAG accuracy" blog claims: no ablation, no disclosed dataset/models. **Asserted**, and empirically contradicted by Vectara.
- Factual vs. procedural granularity divergence: **no study found** isolating this — genuine gap, not just unsearched.

Synthesis: finer granularity helps when the atomic unit is well-formed (propositions extracted with intent), but naive similarity-based "semantic chunking" is the wrong proxy and measurably underperforms simple fixed-size chunking. The lesson is "the right atomic unit," not "smaller is always better."

## Thread 2 — Structured/linked KBs vs. flat documents for agents

- **A-MEM (arXiv 2502.12110, NeurIPS 2025)** — explicitly Zettelkasten-inspired: atomic notes + LLM-driven linking + "memory evolution" (new notes update old ones). Direct head-to-head vs. MemGPT/MemoryBank/ReadAgent on LoCoMo/DialSim: multi-hop F1 27.02 vs 26.65 (MemGPT); temporal reasoning 45.85 vs 25.52 (>2x); DialSim F1 3.45 vs 1.18. Token efficiency: ~1,200 tokens/op vs ~16,900 baseline (85–93% reduction). **Measured**, and the closest thing to a direct validation of this project's strategy on an actual agent-memory benchmark.
- **HippoRAG 2** — KG + Personalized PageRank memory. MuSiQue F1 44.8→51.9 over HippoRAG1/dense RAG; gains concentrated in multi-hop, comparable to dense RAG on single-hop. **Measured**, but vs. other RAG/KG systems, not vs. "one big document."
- **GraphRAG (Microsoft 2024)** — community summaries beat flat vector RAG on query-focused summarization/global sensemaking (~86% vs ~57% comprehensiveness win-rate on complex multi-entity queries, per secondary sources). **Benchmarked**, not independently verified against primary text here.
- **Doc2Atom (arXiv 2606.12400, 2026)** — the one genuine atomic-vs-monolithic head-to-head, but in a LoRA parametric-memory-compression setting, not retrieval/agent-memory: Gemma-2-2B F1 37.99 vs 29.41 monolithic. **Measured**, narrow scope.
- **Direct "linked atomic notes vs. monolithic doc" comparison for agent task performance specifically: does not really exist.** All the marquee systems (GraphRAG, A-MEM, HippoRAG) benchmark against other RAG/memory systems, not against "give the agent one long doc and let it read."

Synthesis: "structured retrieval beats naive/flat RAG" is well-supported (A-MEM, HippoRAG, GraphRAG). "Atomic+linked beats monolithic document" specifically is asserted by analogy, not directly measured for agents — A-MEM is the closest and most favorable data point.

## Thread 3 — Context rot / progressive disclosure

- **Liu et al., "Lost in the Middle" (arXiv 2307.03172, TACL 2024)** — U-shaped position bias; GPT-3.5-Turbo's mid-context accuracy fell below its no-context baseline (56.1%). **Benchmarked.**
- **Chroma "Context Rot" (July 2025, trychroma.com/research/context-rot)** — 18 frontier models, 10K–500K tokens, isolates length as sole variable. 30–50% accuracy drops well before stated context limits; degradation starts as early as ~50K tokens even in 1M-token models; not fixed by bigger windows (multi-hop follow-up: monotonic F1 decline across all 18 models, steepest 100K–500K). **Measured**, strong methodology.
- **"Is Progressive Disclosure All You Need for Long-Context Agents?" (arXiv 2607.17598, 2026)** — the most directly relevant paper. Single-book scale: disclosure ties or *hurts* raw long-context navigation (one setup: 0.91→0.64 collapse). Library scale (corpus exceeds native context): disclosure holds 0.46 vs 0.26 raw (~2x) at half token cost. **Measured** — conditional finding: disclosure wins only once corpus exceeds what fits/is navigable natively; adds nothing (or hurts) below that threshold.
- **Anthropic "Effective context engineering for AI agents" (Sep 2025)** — progressive disclosure as stated principle, built on cited (not original) context-rot literature plus engineering reasoning; explicitly flags the trade-off (runtime exploration is slower). **Asserted**, backed by measured-elsewhere evidence.

Synthesis: context rot is real and reproducible, but it's about retrieval-under-distraction (needles among irrelevant tokens), not directly "long coherent doc vs. fragments." The one paper testing disclosure vs. long-context head-on found the benefit is conditional on corpus size exceeding native navigability — not a blanket win.

## Thread 4 — Zettelkasten / doc-structure lineage

- **Carroll et al., "The Minimal Manual" (IBM Research, HCI 1987/88)** — genuine controlled lab study, real users, real tasks; minimal/task-first manuals beat conventional ones on completion time and error recovery. **Measured/benchmarked** — the one thread here with real controlled empirical validation, though exact effect sizes weren't extractable from the source.
- **Zettelkasten/atomic notes**: no controlled study isolating atomicity+linking as the causal variable, for humans or agents. Popularity rests on general cognitive-science plausibility (recall, spaced retrieval), not a direct test. **Asserted.**
- **Wikipedia WP:SUMMARY**: editorial convention (~50KB/8,000-word split threshold), no research paper behind the specific threshold. **Practitioner-reported/asserted.**
- **Diátaxis**: unvalidated as a named framework; borrows credibility from older adjacent empirical work (Curtis et al. 1989 *Journal of Systems and Software*; a 2023 CHI field study on developer doc format) without being tested itself. **Practitioner-reported.**
- **API docs findability** (Meng et al., SIGDOC 2019, observational study) — found navigation/return failures when info is distributed across pages; recommends strong search or consolidation over fragmentation unless wayfinding is strong. **Measured (observational)** — a direct, real caution against assuming smaller chunks always win.

Synthesis: only minimal-manual research is genuinely empirically tested; everything else in this lineage (Zettelkasten, Diátaxis, WP:SUMMARY) is folklore/consensus, and the one real observational study on granularity (API docs) argues fragmentation without strong navigation hurts findability.

## Thread 5 — Agent-facing docs, 2025–2026

- **llms.txt** — ~10% adoption of sampled domains, 7.4% of Fortune 500. Two independent studies (SE Ranking ~300K domains; Trakkr 37,894 domains, matched controls) found **no correlation** with AI-citation frequency; Google's Gary Illyes compared it to the abandoned keywords meta tag. **Measured** (two independent null results) — a rare case of a popular agent-doc proposal being tested and failing.
- **AGENTS.md spec** (multi-vendor, Aug 2025) — practitioner consensus: sections under ~50 lines, file under ~150–200 lines, split into nested per-directory files past that. **Asserted/practitioner-reported**, no controlled measurement.
- **Anthropic's Claude Code best-practices docs** — explicit: keep CLAUDE.md short; named anti-pattern "over-specified CLAUDE.md — Claude ignores half of it, important rules lost in noise"; recommends `@import` splitting and moving domain-specific knowledge into on-demand Skills rather than always-loaded content. **Asserted** (official guidance, no published internal benchmark).
- **"Agent READMEs" corpus study (arXiv 2511.12884, Nov 2025)** — 2,303 real agent context files across 1,925 repos: these evolve like configuration code (frequent incremental edits, not written once); skew toward functional content (tests 75.9%, implementation 70.8%) over guardrails (security 14.8%). **Measured (descriptive/correlational)** — no length-vs-success correlation reported; that specific gap remains unfilled.
- SkillOS / Trace2Skill: turned out to be about RL-driven skill curation and trajectory distillation, not file-granularity guidance — not on point. WikiSkill itself (already read, per prompt) is the actual on-point precedent: `index.md` (one line per pattern) + `patterns/*.md` (one file per failure mode/strategy) is exactly this project's MEMORY.md + docs/concepts/ pattern, independently arrived at, and its own ablation (§5 of the paper notes) shows persistence/accumulated knowledge is the load-bearing component (+15.0 avg with wiki vs. without) — the closest thing to a controlled result validating index+atomic-files for an agent loop, albeit for a skill-evolution harness, not general documentation.

## Thread 6 — The counter-case for consolidation

- Over-fragmentation has a real, measured cost: 43-token semantic chunks scored 54% vs. 69% for 512-token overlapping chunks (FloTorch 2026). **Benchmarked.**
- Anaphoric-reference loss when chunks are embedded/read in isolation is a named, documented RAG failure mode; Anthropic's own "Contextual Retrieval" exists specifically to compensate for it. **Practitioner-reported**, but the fix's existence is itself evidence the base problem is real.
- Navigation/hop overhead is measurably expensive: web/tool-call round trips account for 73% (up to 91%) of end-to-end latency in deep-research agents; diminishing returns after the first extra retrieval hop. **Measured.**
- Wiki/doc decay (orphaned pages, "engineering wiki graveyard," 25%-of-time-lost claims) — real named problems with tooling built around them, but the quantified claims are largely uncited/anecdotal. **Asserted/practitioner-reported.**
- The one CLAUDE.md/AGENTS.md-specific practitioner data point found (Upsun) actually argues *against* monolithic files (a 5-line targeted file beat a 2,000-word one) — so there is no direct evidence *for* consolidation from agent-context-file experience itself; the consolidation case has to be built by analogy from RAG chunk-size and hop-latency studies.

## Synthesized recommendation for this project's strategy

**What the evidence actually supports:**
1. The core architecture (tiny always-on index + atomic files retrieved just-in-time) is well-supported at the *mechanism* level: A-MEM (measured, direct agent-memory benchmark) and WikiSkill's own ablation (index+persistent wiki, +15.0 avg vs. none) are the two pieces of evidence that most directly validate this project's actual design, not just an analogous one.
2. Context-rot research (Chroma, Lost-in-the-Middle) supports keeping *irrelevant/distractor* content out of active context — which the MEMORY.md-index + on-demand file-read pattern already achieves — but doesn't by itself prove any coherent, non-distractor-laden doc should be split.
3. The progressive-disclosure paper (2607.17598) gives the sharpest caveat found anywhere in this research: disclosure helps *conditionally*, once the corpus exceeds what's natively navigable, and is neutral-to-harmful below that threshold. This project's corpus (docs/, iteration_findings.md, concepts/) is well within what an agent can navigate in one session — so the win here is likely real but should be attributed to token cost and precision, not to some universal law that fragments beat coherent docs.

**What's assumption, not evidence:**
- "Atomic + linked beats monolithic for agents" as a *general* claim — no one has run that head-to-head experiment for agents; the closest analogues (Doc2Atom) are in an unrelated setting (LoRA compression).
- llms.txt-style "just expose structure and agents will use it well" — measured to be a null result for the adjacent (web-crawler) case; a caution against assuming any indexing scheme self-evidently helps just because it's machine-readable.
- The Zettelkasten/atomic-notes lineage this project cites as an inspiration has essentially zero controlled empirical backing on its own terms — it's cognitive-science-plausible folklore, not a tested result. Cite it as *design inspiration*, not *evidence*.
- The claim that fine-grained note splitting per se aids retrieval is contradicted by Vectara's peer-reviewed result that semantic/fine chunking underperforms simple fixed-size chunking — the actual load-bearing variable isn't granularity per se, it's whether each unit is a complete, self-contained thought (a well-written concept note), which is closer to what this project already practices (one concept per file, written deliberately, not auto-chunked).

**Concrete refinements suggested by the evidence:**
1. **Guard against over-fragmentation** — the Vectara/FloTorch results and the 2019 API-docs findability study both warn that splitting too fine, or splitting without strong "wayfinding" (the index + wikilinks), actively hurts. This project's notes should stay at "one coherent concept, sized to be self-contained" rather than shrinking further for granularity's own sake.
2. **Keep the index itself lean and pruned** — the llms.txt null result and the "Agent READMEs" corpus study (files bloat like unmaintained config code) both suggest an index that grows without pruning becomes exactly the kind of artifact that stops helping. `link_and_tag_docs.py` + the supersession/retirement idea in IV.3 is the right mitigation; treat index staleness as an active risk, not a solved one.
3. **Don't rely on file existence/format alone to make content "agent-legible"** — llms.txt's failure suggests structure without genuine information-density gain doesn't help; the wins in this thread (A-MEM, WikiSkill) came from write-time curation (reflection, root-cause extraction into patterns) not from the linking mechanism alone. This validates the project's "do the work at write time" principle already stated in §6.3.
4. **Consolidation is still the right call for narrative/onboarding material** — nothing found argues split notes beat a coherent walkthrough for building a first mental model (CLAUDE.md's own architecture/flow sections are exactly this use case and should probably stay consolidated, distinct from concepts/findings which should stay atomic).

## Not covered
None — all six threads were researched. The one explicit internal gap flagged across sources: no study anywhere (RAG, agent-memory, or documentation research) directly measures agent task success as a function of doc granularity in a controlled way that isolates "many linked atomic files" vs. "one long coherent file" holding content constant. Every piece of evidence gathered here approaches that question by analogy (chunking studies, agent-memory benchmarks, corpus studies) rather than testing it directly — worth stating plainly rather than overclaiming.
