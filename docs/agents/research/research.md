---
tags:
  - research-digest
---

# Raw research record — loop-engineering meta-analysis (2026-07-04)

Primary record behind ../[[loop-engineering-analysis|loop-engineering-analysis.md]]. Eight research subagents
were spawned during the meta-analysis session; each `NN-*.md` is that agent's
**unedited final digest**, and `transcripts/NN-*.jsonl` is its full raw transcript
(every search, fetch, and intermediate step — for auditing what the digest claims).

Read the digests with the corrections from [[06-citation-verification|06-citation-verification.md]] in hand:
the verifier found no hallucinated sources across 18 spot-checks, but four defects
(a wrong arXiv ID, a misattributed statistic, two conflated baselines/framings).
Corrected values are in the main analysis doc; the digests here are preserved
as-produced, defects included — that is the point of a raw record.

| # | Digest | What it covers | Feeds |
|---|---|---|---|
| 01 | loop-context-engineering | "loop/context engineering" as named disciplines; long-horizon reliability patterns; why loops fail to converge | Part I [[iteration_findings#^4::§4]], Part III |
| 02 | metric-gaming-eval-failures | Goodhart/specification gaming; LLM self-verification limits; sycophancy; eval construct validity; sim-to-real | Part I [[iteration_findings#^3::§3]] (reproduced findings) |
| 03 | verifier-critic-architectures | generator-verifier separation; VLM/frame grounding limits; test-time verification scaling; robotics self-improving loops; supervisor patterns | Part I [[iteration_findings#^4::§4]], Part IV.4 |
| 04 | agent-memory-architectures | token-efficient memory beyond vanilla RAG: JIT retrieval, MemGPT, Mem0/A-MEM/Zep, GraphRAG, reflection, skills, CoALA | Part I [[iteration_findings#^6::§6]], Part IV.3 |
| 05 | transcript-mining-grasp-experiment | independent extraction from the RAW grasp-experiment transcripts (verbatim human messages, turning points, reflection-vs-transcript discrepancies) | Part II (all) |
| 06 | citation-verification | adversarial spot-check of 18 load-bearing citations from digests 01–04 | corrections in Parts I/III |
| 07 | self-driving-labs | the A-Lab failure precedent + critiques; SDL converged practices (orthogonal measurement, noise floor, known-answer runs) | Part VI |
| 08 | world-models-metr-horizons | learned world models vs analytic sims (incl. the residual-physics refutation); METR time-horizon measurement | Part V amendment |

**Extension pass (2026-08-31, same session resumed):** three more digests behind
the doc's Part VII — the full-mission generalization questions:

| # | Digest | What it covers | Feeds |
|---|---|---|---|
| 09 | rollforward-aug2026 | May–Aug 2026 literature roll-forward: METR corrections, Dreaming/Outcomes, GEPA, auto-scaffold-design counter-evidence, supersession measured, Cognition's softened multi-agent stance | Part VII.1, edits to Part V + [[iteration_findings#^5::§5]] |
| 10 | generic-vs-specialized-loops | ratchet overfitting; scaffold transfer (ADAS/GEPA/ExpeL/Voyager/METR); TMS/reflection-tree distillation with provenance; checks in code vs context; layered check hierarchies | Part VII.2–VII.3 |
| 11 | vision-reference-priors | expectation-based monitoring; pre-registration for agents; literature-derived priors; anchoring-bias evidence; VLM reference-clip limits | Part VII.4 |
| 12 | wikiskill-paper-notes | **full paper read, not a subagent digest** — Google's WikiSkill (arXiv 2608.27454): three-layer wiki/skill co-evolution, [[12-wikiskill-paper-notes::PURPOSE.md provenance]], gated skill updates, isolation ablation; missed by sweep 09, surfaced by the human | Part VII.1 addendum |

Note: 10 and 11 have NO raw transcripts (their task transcript files were empty
at archive time — a harness observability gap, itself a data point); the digests
are the agents' final messages preserved verbatim. 09's transcript is present.

Also archived: `transcripts/00-meta-analysis-session-d155edbe.jsonl.gz` — the
**main meta-analysis session's own raw transcript** (the user↔Claude conversation
that produced the analysis doc and spawned agents 01–08). Snapshot taken
2026-07-06 near the session's end; the last few closing exchanges may be absent.
`gunzip` to read (JSONL, one event per line).

Provenance notes:
- Agents 01–04 ran in the first research fan-out; 05 was the primary-evidence
  audit; 06–08 were the remediation pass after the thoroughness self-audit.
- Agents 07 and 08 were killed mid-run by mistake and resumed with a compile-only
  instruction (no post-stop fetches); 08's scalable-oversight sub-thread is
  explicitly marked NOT COVERED in its digest rather than backfilled from memory.
- The grasp experiment's own transcripts (the *subject* of study) are NOT copied
  here; pointers to them are in ../[[grasp-experiment-reflection|grasp-experiment-reflection.md]] [[grasp-experiment-reflection#^1|§1]].
