---
tags:
  - research-digest
---

# Research digest: Adversarial spot-verification of 18 load-bearing citations from digests 01-04

> Raw output of research subagent `a67c13b1afdd7b3d6` (session d155edbe, 2026-07-04),
> spawned for the loop-engineering meta-analysis. Unedited final message;
> synthesis and corrections live in ../[[loop-engineering-analysis|loop-engineering-analysis.md]].
> Full transcript: `transcripts/06-citation-verification.jsonl`.

Verification complete — all 18 claims checked against primary sources. Overall: the subagents were largely accurate. One wrong arXiv ID, one mis-attributed statistic, and two baseline/framing slippages. The suspicious late-2025 arXiv IDs (2509.25370, 2502.12110, 2504.19413) are all real.

## Verdict table

| # | Claim | Verdict | Notes |
|---|---|---|---|
| 1 | Huang et al., self-correct, 2310.01798 | **CONFIRMED** | ICLR 2024. Abstract: "LLMs struggle to self-correct their responses without external feedback, and at times, their performance even degrades after self-correction." |
| 2 | Tyen et al., 2311.08516 | **CONFIRMED** | Gladys Tyen first author, ACL 2024 Findings. Title matches exactly; correction robust given error location. |
| 3 | Pan/Bhatia/Steinhardt, 2201.03544 | **CONFIRMED** | ICLR 2022. Abstract: "phase transitions: capability thresholds at which the agent's behavior qualitatively shifts, leading to a sharp decrease in the true reward" while proxy reward rises. |
| 4 | Manheim & Garrabrant Goodhart, **1803.06869** | **PARTLY — wrong arXiv ID** | 1803.06869 is a *Floquet semimetal physics paper* (Li/Lee/Gong). The real paper exists at **arXiv 1803.04585** (Manheim & Garrabrant, Mar 2018). Fix the ID. |
| 5 | Zhu et al., 2509.25370 | **CONFIRMED** | Real, submitted Sept 29, 2025. Abstract names AgentErrorTaxonomy, AgentDebug, "up to 26% relative improvements" (ALFWorld/GAIA/WebShop). Note the "up to". |
| 6 | Mem0, 2504.19413 | **PARTLY — baselines conflated** | Paper real (Apr 28, 2025), numbers real, but: 26% accuracy is vs OpenAI; the **91% p95 latency and >90% token savings are vs the full-context baseline**, not vs OpenAI memory. |
| 7 | A-MEM, 2502.12110 | **CONFIRMED** | Wujiang Xu first author, Feb 2025; arXiv page states accepted to NeurIPS 2025. |
| 8 | Zep, 2501.13956 | **CONFIRMED** | Jan 2025, Zep/Graphiti authors. "Up to 18.5%" accuracy + 90% latency reduction on LongMemEval. Note "up to". |
| 9 | MLLM-as-a-Judge, 2402.04788 | **CONFIRMED** | Dongping Chen, ICML 2024 oral. Abstract: "human-like discernment in Pair Comparison... significant divergence from human preferences in Scoring Evaluation and Batch Ranking." |
| 10 | GenRM, 2408.15240 | **CONFIRMED** | Lunjun Zhang (Google DeepMind), Aug 2024, ICLR 2025. Abstract literally: "73% → 93.4% on GSM8K" (Best-of-N). |
| 11 | Large Language Monkeys, 2407.21787 | **CONFIRMED** | Bradley Brown, Jul 2024. "increases from 15.9% with one sample to 56% with 250 samples" (DeepSeek-Coder-V2-Instruct, SWE-bench Lite). |
| 12 | Cognition "Don't Build Multi-Agents" | **CONFIRMED** | Walden Yan, June 12, 2025. Principles: "Share context, and share full agent traces, not just individual messages" + actions carry implicit decisions. Flappy Bird example present. |
| 13 | Manus context-engineering blog | **CONFIRMED** | Yichao 'Peak' Ji, July 18, 2025. All three techniques verbatim: KV-cache hit rate "the single most important metric", todo.md recitation, "Leave the wrong turns in the context." |
| 14 | Anthropic "Effective context engineering", 84% figure | **PARTLY — figure is from a different post** | The engineering post exists (Sept 29, 2025) but contains **no 84% figure**. The 84% comes from the same-day companion post **"Managing context on the Claude Developer Platform"** (claude.com/blog/context-management), and it's attributed to **context editing** ("reducing token consumption by 84%"), not the memory tool; memory tool + context editing combined gave +39% performance. Your subagent's suspicion was correct. |
| 15 | Sakana AI Scientist eval, 2502.14297 | **PARTLY — substance right, framing loose** | Paper real: Beel, Kan, Baumgart, "Evaluating Sakana's AI Scientist" (Feb 20, 2025), genuinely independent. No correlation statistic anywhere; the body's finding is directional misalignment: the automated reviewer "rejected 9 out of 10 papers, including four that had been accepted by human reviewers, while recommending acceptance for only one, which had been rejected on OpenReview." Compatible with "weak agreement with real reviewers" but not stated as a correlation, and it's in the body, not the abstract. |
| 16 | Reflexion, 2303.11366 | **CONFIRMED** | Abstract: "achieves a 91% pass@1 accuracy on the HumanEval coding benchmark." arXiv page doesn't display the venue, but NeurIPS 2023 matches the public record. |
| 17 | Let's Verify Step by Step, 2305.20050 | **CONFIRMED** | Lightman et al., OpenAI, May 2023. "Our process-supervised model solves 78% of problems from a representative subset of the MATH test set." |
| 18 | Raji et al., 2111.15366 | **CONFIRMED** | "Accepted in NeurIPS 2021 Benchmarks and Datasets track." |

## Notes for correcting the report

- **Must fix**: claim 4's arXiv ID → **1803.04585** (as cited, it points at condensed-matter physics).
- **Should fix**: claim 6 — restate Mem0's latency/token numbers as "vs full-context," keeping only the 26% as "vs OpenAI." Claim 14 — cite the 84% to claude.com/blog/context-management and attribute it to context editing, not the memory tool or the engineering essay. Claim 15 — soften "correlates only weakly" to "the automated reviewer disagreed with human accept/reject decisions on most papers evaluated."
- **Minor hedges**: claims 5 and 8 both say "up to" in their abstracts (26%, 18.5%); worth carrying that qualifier.
- No hallucinated papers found — every source exists with correct authors and dates, including all three 2025-dated arXiv IDs.
