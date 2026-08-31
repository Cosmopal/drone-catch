---
tags:
  - research-digest
---

# Research digest: Token-efficient agent memory beyond vanilla RAG

> Raw output of research subagent `adc8af3df5879cfe9` (session d155edbe, 2026-07-04),
> spawned for the loop-engineering meta-analysis. Unedited final message;
> synthesis and corrections live in ../[[loop-engineering-analysis|loop-engineering-analysis.md]].
> Full transcript: `transcripts/04-agent-memory-architectures.jsonl`.

I have strong primary-source coverage across all eight topics. Compiling the digest now.

---

# Token-Efficient Agent Memory Architectures: A Grounded Survey (Beyond Vanilla RAG)

A structured digest for designing a knowledge-accrual system for a long-running autonomous coding + robotics-experiment agent. Each section: source (org/date/title), mechanism, strengths/weaknesses, and a one-line token-efficiency takeaway. Synthesis at the end.

---

## 1. Vanilla RAG — and why it breaks for agentic/procedural/causal knowledge ^1

**Mechanism.** Embed a corpus into chunks → store vectors → at query time embed the query, retrieve top-k by cosine similarity, stuff the chunks into context. One-shot, stateless, document-centric.

**Known weaknesses (well-documented, not folklore):**
- **Chunking destroys structure.** Splitting sacrifices the contextual relationships between specialized terms and abstract concepts; large chunks add noise, small chunks lose coherence — there is no chunk size that preserves both. A causal chain or a procedure spanning chunks is severed.
- **Similarity ≠ relevance/evidence.** Vector search returns passages *semantically similar* to the query that frequently *do not contain the required evidence*, especially in multi-document settings. It does not capture how pieces connect across chunks.
- **Multi-hop failure.** One-shot top-k retrieval either misses critical details or floods the model; "vanilla RAG performs poorly on complex multi-hop queries" is a recurring benchmark finding. Causal/relational queries ("why did the catch fail when ω was high?") need traversal, not nearest-neighbor.
- **No hierarchy / no global view.** RAG "fails on global questions directed at an entire corpus" — sensemaking is a query-focused *summarization* task, not a retrieval task (this is exactly the gap GraphRAG names).
- **Stale/contradictory chunks.** Plain vector stores are append-mostly; old and new facts coexist with no temporal validity or contradiction resolution. The agent retrieves both and cannot tell which is current.

**Token efficiency:** Cheap and simple, but pays in *wasted* tokens — irrelevant-but-similar chunks crowd the window and degrade reasoning; use it only for static, fact-lookup-shaped knowledge where structure doesn't matter.

Sources: [When Retrieval Succeeds and Fails (arXiv 2510.09106)](https://arxiv.org/pdf/2510.09106) · [Survey of Graph RAG (arXiv 2501.13958)](https://arxiv.org/pdf/2501.13958) · [GraphRAG / SingleStore writeup](https://www.singlestore.com/blog/rethinking-rag-how-graphrag-improves-multi-hop-reasoning-/)

---

## 2. Agentic / just-in-time retrieval (retrieval-as-a-tool) ^2

**Source.** Anthropic Engineering, **"Effective context engineering for AI agents"** (Sep 29, 2025, alongside Claude Sonnet 4.5).

**Mechanism.** Instead of pre-loading embedded chunks, the agent holds **lightweight identifiers** (file paths, stored queries, URLs) and **loads data at runtime via tools** — `grep`, `head`/`tail`, file reads, targeted queries over a *structured* corpus plus a curated index. Claude Code embodies this: a human-readable `CLAUDE.md` as the curated index, and the filesystem itself as the memory; the model navigates and reads exactly what it needs, when it needs it. Mirrors how humans use a filing system rather than memorizing everything.

**Strengths.** Preserves document structure (you read whole files / real sections, not severed chunks); retrieval is *agent-decided* and inspectable; naturally handles hierarchy (directory layout = ontology); no embedding-staleness problem; progressive disclosure keeps the window lean.
**Weaknesses.** Costs agent turns/latency (search is iterative, not one-shot); quality depends on corpus organization and index curation; the agent can wander or miss things a curated index would surface.

**Token efficiency:** Loads only what the current step needs — the highest-leverage pattern for *your* use case (a coding agent already lives in a filesystem); pairs perfectly with a curated `CLAUDE.md`/`docs/concepts/` index.

Source: [anthropic.com/engineering/effective-context-engineering-for-ai-agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

---

## 2b. Claude memory tool + context management (the productized version) ^2b

**Source.** Anthropic, **"Managing context on the Claude Developer Platform"** + **Memory tool docs** (`context-management-2025-06-27` beta; memory tool now GA on Messages API), 2025.

**Mechanism.** A **file-based memory tool**: Claude can create/read/update/delete files in a dedicated memory directory that **persists across conversations** — building a knowledge base over time, maintaining project state, referencing prior learnings without keeping them in-context. Pairs with **context editing** (clears stale tool results) and **compaction** (server-side summarization of old turns). Compaction keeps the active window small; memory preserves what must survive summarization.

**Strengths.** Native, low-glue persistence; self-curated by the model; combines with compaction for long-running tasks. **Weaknesses.** Model-managed memory can drift or accumulate cruft without discipline; it's a mechanism, not a strategy (you still design *what* gets written).

**Token efficiency:** Anthropic reports **~84% token reduction** in extended workflows — the agent stops re-loading what it should already "know."

Sources: [anthropic.com/news/context-management](https://anthropic.com/news/context-management) · [Memory tool docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)

---

## 3. Hierarchical / OS-style paging memory — MemGPT / Letta ^3

**Source.** Packer, Wooders, Lin, Fang, Patil, Gonzalez et al., **"MemGPT: Towards LLMs as Operating Systems"** (arXiv 2310.08560, Oct 2023). Productized as **Letta**.

**Mechanism.** **Virtual context management**, borrowed from OS virtual memory: a small **physical context** (the actual window) backed by a large **virtual context** (external store). The LLM uses **function calls** to *page* information in and out — moving data between fast (in-context) and slow (external) memory, editing its own context, and deciding when to respond. Self-editing memory hierarchy (core/working ↔ archival/recall) gives the *appearance* of unbounded context.

**Strengths.** Principled unbounded-context illusion; the agent manages its own working set; strong on long multi-session dialogue. **Weaknesses.** Paging logic consumes function-call turns and reasoning overhead; correctness depends on the model making good page-in/out decisions; added latency.

**Token efficiency:** Keeps the window bounded regardless of total knowledge size, paying in tool-call turns rather than context tokens — use when total knowledge vastly exceeds any window and sessions are long.

Source: [arXiv:2310.08560](https://arxiv.org/abs/2310.08560) · [letta.com](https://www.letta.com/)

---

## 4. Dedicated memory layers (extract → consolidate → update → retrieve) ^4

### Mem0
**Source.** **"Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory"** (arXiv 2504.19413, Apr 2025).
**Mechanism.** A **three-stage streaming pipeline**: **extract** salient facts from each turn → **consolidate/update** against existing memories (resolve, merge, overwrite) → **retrieve** at query time. A graph variant (`Mem0g`) adds relational structure.
**Strengths.** Actively de-duplicates and updates (addresses staleness/contradiction that vanilla RAG ignores); production-oriented. **Weaknesses.** Extraction/consolidation is itself LLM work (write-time cost + possible extraction errors); lossy by design.
**Token efficiency:** Reports **>90% lower token cost and 91% lower p95 latency vs full-context**, with +26% accuracy over an OpenAI memory baseline — the headline "consolidated memory beats stuffing the window" result.
Source: [arXiv:2504.19413](https://arxiv.org/abs/2504.19413)

### A-MEM (Zettelkasten-style, self-organizing)
**Source.** Xu, Liang, Mei, Gao, Tan, Zhang, **"A-MEM: Agentic Memory for LLM Agents"** (arXiv 2502.12110; NeurIPS 2025).
**Mechanism.** Each new memory becomes a **structured note** (contextual description, keywords, tags). The system then **analyzes historical notes and creates links** where meaningful similarities exist — a self-organizing **Zettelkasten** knowledge network. New memories can **trigger evolution** (updates to the attributes/links of existing notes).
**Strengths.** Emergent structure without a hand-built schema; links enable associative/multi-hop recall; memory *evolves* rather than just accreting. **Weaknesses.** Link-generation is LLM-driven (cost + noise); graph can drift.
**Token efficiency:** Retrieves a *connected neighborhood* rather than k isolated chunks — better recall per token for relational queries. Strong conceptual fit for "accrue transferable robotics/control knowledge with links between concepts" (your `docs/concepts/` goal).
Source: [arXiv:2502.12110](https://arxiv.org/pdf/2502.12110) · [GitHub](https://github.com/WujiangXu/A-mem)

### Zep / Graphiti (temporal knowledge graph)
**Source.** **"Zep: A Temporal Knowledge Graph Architecture for Agent Memory"** (arXiv 2501.13956, Jan 2025); engine = **Graphiti**.
**Mechanism.** A **bi-temporal knowledge graph**: every edge carries explicit **validity intervals** and tracks *when an event occurred* vs *when it was ingested*. Updates are **non-lossy** — new facts are added with timelines rather than overwriting, so superseded facts remain but are time-bounded.
**Strengths.** First-class **contradiction/staleness handling** via time (the thing plain vector stores can't do); fuses conversational + structured data. **Weaknesses.** Graph construction/maintenance overhead; heavier infra.
**Token efficiency:** Reports **up to +18.5% accuracy and ~90% latency reduction** vs baselines on LongMemEval by retrieving temporally-scoped facts instead of dumping history — use when "what's true *now* vs what *was* true" matters (e.g., evolving tuning constants, deprecated approaches).
Source: [arXiv:2501.13956](https://arxiv.org/html/2501.13956v1) · [Graphiti / Neo4j](https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/)

---

## 5. Knowledge-graph retrieval — Microsoft GraphRAG ^5

**Source.** Edge, Trinh, Cheng, Bradley, Chao, Mody, Truitt, Metropolitansky, Ness, Larson (Microsoft), **"From Local to Global: A Graph RAG Approach to Query-Focused Summarization"** (arXiv 2404.16130, Apr 2024).

**Mechanism.** Two-stage index: (1) LLM extracts an **entity knowledge graph** from source docs; (2) detect entity **communities** and **pre-generate community summaries**. At query time, two modes: **Local query** (precise fact lookup over a subgraph) and **Global query** (map-reduce over community summaries → partial answers → final synthesis). Hierarchy is explicit (entities → communities → corpus).

**Strengths.** Wins exactly where vanilla RAG fails — **global sensemaking** over a whole corpus, **multi-hop** traversal, and **contradiction surfacing** (conflicting edges become visible). Strong on million-token corpora. **Weaknesses.** Expensive index build (LLM over the whole corpus); index must be rebuilt/maintained as knowledge grows. Lightweight alternative: **wikilink-style graphs** (manual [[links]] between notes) get much of the relational benefit at near-zero infra cost — a natural fit for a docs/ corpus.

**Token efficiency:** Pre-computed community summaries mean a global question costs a few summary reads instead of scanning the corpus — front-load tokens at index time to save them at query time.

Source: [arXiv:2404.16130](https://arxiv.org/abs/2404.16130) · [graphrag.com](https://graphrag.com/appendices/research/2404.16130/)

---

## 6. Reflection / consolidation at WRITE time — Generative Agents ^6

**Source.** Park, O'Brien, Cai, Morris, Liang, Bernstein (Stanford/Google), **"Generative Agents: Interactive Simulacra of Human Behavior"** (arXiv 2304.03442, Apr 2023).

**Mechanism.** A **memory stream** of natural-language observations, each with a timestamp, last-accessed time, and an LLM-assigned **importance score (1–10)**. Retrieval = weighted sum of **recency** (exponential decay), **importance**, and **relevance** (embedding similarity). Critically, **reflection**: periodically (triggered when summed importance of recent events crosses a threshold) the agent **synthesizes raw episodes into higher-level insights**, which are written back as new, higher-importance memories the agent can later retrieve.

**Strengths.** The canonical "**consolidate raw episodes into reusable insights at write time**" pattern — directly relevant to turning experiment logs into transferable lessons (your [[iteration_findings|iteration_findings.md]] → `docs/concepts/` flow is essentially this). Importance+recency scoring beats pure similarity for "what matters now." **Weaknesses.** Reflection costs LLM calls; importance scores are noisy; the raw stream still grows unboundedly underneath.

**Token efficiency:** Reflection compresses many episodes into one high-value insight, so future retrieval pulls the *lesson* (cheap) instead of replaying the *episodes* (expensive).

Source: [arXiv:2304.03442](https://ar5iv.labs.arxiv.org/html/2304.03442)

---

## 7. Procedural memory / "skills" — store compiled procedures, don't re-reason ^7

### Voyager (skill library)
**Source.** Wang, Xie, Jiang, Mandlekar, Xiao, Zhu, Fan, Anandkumar (NVIDIA/Caltech), **"Voyager: An Open-Ended Embodied Agent with LLMs"** (arXiv 2305.16291, NeurIPS 2023).
**Mechanism.** An **ever-growing skill library of executable code**. The agent writes a program to accomplish a task, verifies it (self-verification + environment feedback + error iteration), and on success **stores the function**, indexed by an embedding of its description. Later tasks **retrieve and compose** stored skills instead of reasoning from scratch. Plus an automatic curriculum.
**Strengths.** Compounding capability — skills become building blocks; generalizes zero-shot to new worlds (3.3× more items, up to 15.3× faster milestones vs prior SOTA). **Weaknesses.** Skills can be brittle to environment changes; library needs curation to avoid near-duplicates.
**Token efficiency:** Retrieving a *verified procedure* is far cheaper than re-deriving it each time — directly applicable: store your validated maneuvers (compliant-capture sweep, throw decomposition) as callable skills.
Source: [arXiv:2305.16291](https://arxiv.org/abs/2305.16291)

### Anthropic Agent Skills
**Source.** Anthropic Engineering, **"Equipping agents for the real world with Agent Skills"** (Dec 18, 2025; published as an open standard).
**Mechanism.** A **skill = a folder** with a `SKILL.md` (instructions) plus scripts/resources, **discovered and loaded dynamically** only when relevant (progressive disclosure: the agent reads the skill name/description first, loads the body on demand). Captures **procedural knowledge** as portable, composable files. Adopted across VS Code, GitHub, Cursor, Goose, Amp.
**Strengths.** Hardware-honest version of Voyager for *real* agents; composable, shareable, filesystem-native (fits the just-in-time model in [[#^2|§2]]). **Weaknesses.** Discipline needed to keep skills atomic and discoverable.
**Token efficiency:** Only the *triggered* skill's body enters context — the rest cost only their one-line descriptions.
Source: [anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

---

## 8. Cognitive-architecture framing — CoALA ^8

**Source.** Sumers, Yao, Narasimhan, Griffiths (Princeton), **"Cognitive Architectures for Language Agents"** (arXiv 2309.02427, Sep 2023).

**Mechanism.** A taxonomy (drawing on Soar/ACT-R) organizing agents along three axes: (i) **memory** — short-term **working** memory plus optional long-term **episodic** (experiences), **semantic** (knowledge/facts), and **procedural** (code/skills/LLM weights); (ii) **action space** — internal (memory read/write/reflect) vs external (tools/environment); (iii) a **decision loop** of planning + execution.

**Why it matters for you.** It's the *organizing frame* for everything above: vanilla RAG ≈ semantic memory only; Generative Agents adds episodic + reflection; Voyager/Skills are procedural memory; MemGPT manages working↔long-term paging. Designing a memory system = deciding which of these four stores you need and how they interact, rather than reaching for one mechanism.

**Token efficiency:** Not a mechanism but a *design discipline* — separating episodic/semantic/procedural lets you keep the working window tiny and route each query to the right (cheap) store.

Source: [arXiv:2309.02427](https://arxiv.org/abs/2309.02427)

---

## Synthesis: RAG is not the only way — when to use which

Vanilla RAG is a single point in a much larger design space. CoALA's lesson is to first ask *what kind of knowledge* you're storing, then pick the mechanism:

| Knowledge type | Bad fit | Good fit |
|---|---|---|
| **Static facts / reference** (semantic) | — | Vanilla RAG, or just-in-time file reads over curated docs |
| **Experiences / "what happened"** (episodic) | RAG (no recency/importance) | Generative-Agents memory stream + **reflection** to distill insights |
| **Reusable procedures** (procedural) | RAG (retrieves text to re-reason from) | **Voyager skill library / Anthropic Skills** — store the verified procedure |
| **Relationships / multi-hop / causal** | RAG (similarity ≠ traversal) | **GraphRAG / A-MEM / Zep** knowledge graphs |
| **Evolving / contradictory facts** | RAG (stale chunks coexist) | **Zep** temporal graph or **Mem0** consolidation (update, don't append) |
| **Whole-corpus sensemaking** | RAG (no global view) | **GraphRAG** community summaries |
| **Knowledge ≫ context window, long sessions** | stuff-the-window | **MemGPT/Letta** paging, **Claude memory tool** + compaction |

Three cross-cutting principles that beat naive RAG on tokens:
1. **Do work at write time, not read time.** Mem0's consolidation, Generative Agents' reflection, GraphRAG's community summaries, Voyager's skill verification all front-load LLM effort so retrieval is cheap and high-signal. Plain RAG does zero write-time work and pays for it on every query.
2. **Retrieve structure, not chunks.** Links (A-MEM), graph neighborhoods (GraphRAG/Zep), whole files (just-in-time) and time-scoped facts (Zep) preserve the relationships chunking destroys — fewer, more relevant tokens.
3. **Just-in-time + curated index is the strongest default for a coding/robotics agent.** You already have a filesystem, a `CLAUDE.md` index, and `docs/concepts/`. The Anthropic context-engineering pattern (lightweight identifiers → load on demand) plus Skills for procedures plus reflection-style consolidation of [[iteration_findings|iteration_findings.md]] into linked concept notes gives most of the benefit of the heavyweight memory layers with near-zero new infrastructure — and reportedly ~84% token savings in extended workflows. Reach for a temporal KG (Zep) or consolidation layer (Mem0) only once contradiction/staleness across many sessions becomes the actual bottleneck.

**Concrete recommendation for your agent:** layer three stores — (a) **semantic/procedural = files + Skills**, navigated just-in-time over a curated index (cheapest, structure-preserving); (b) **episodic = an append log** (experiment runs) that a **reflection pass periodically distills** into linked concept notes (Generative-Agents pattern, your existing `docs/concepts/` discipline made automatic); (c) add a **lightweight wikilink graph or A-MEM-style linking** between concept notes for the multi-hop/causal queries ("which controller layer fixes which failure mode"). Defer Mem0/Zep/MemGPT until cross-session contradiction or window pressure forces it.

### Sources
- Anthropic — [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) (Sep 2025)
- Anthropic — [Managing context on the Claude Developer Platform](https://anthropic.com/news/context-management) + [Memory tool docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) (2025)
- Anthropic — [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) (Dec 2025)
- Packer et al. — [MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/abs/2310.08560) (arXiv 2310.08560, 2023) / [Letta](https://www.letta.com/)
- Mem0 — [Building Production-Ready AI Agents with Scalable Long-Term Memory](https://arxiv.org/abs/2504.19413) (arXiv 2504.19413, 2025)
- Xu et al. — [A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/pdf/2502.12110) (arXiv 2502.12110; NeurIPS 2025) / [GitHub](https://github.com/WujiangXu/A-mem)
- [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/html/2501.13956v1) (arXiv 2501.13956, 2025) / [Graphiti (Neo4j)](https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/)
- Edge et al. (Microsoft) — [From Local to Global: A Graph RAG Approach](https://arxiv.org/abs/2404.16130) (arXiv 2404.16130, 2024) / [graphrag.com](https://graphrag.com/appendices/research/2404.16130/)
- Park et al. — [Generative Agents: Interactive Simulacra of Human Behavior](https://ar5iv.labs.arxiv.org/html/2304.03442) (arXiv 2304.03442, 2023)
- Wang et al. — [Voyager: An Open-Ended Embodied Agent with LLMs](https://arxiv.org/abs/2305.16291) (arXiv 2305.16291, NeurIPS 2023)
- Sumers, Yao et al. — [Cognitive Architectures for Language Agents (CoALA)](https://arxiv.org/abs/2309.02427) (arXiv 2309.02427, 2023)
- RAG-weakness evidence — [When Retrieval Succeeds and Fails (arXiv 2510.09106)](https://arxiv.org/pdf/2510.09106) · [Survey of Graph RAG (arXiv 2501.13958)](https://arxiv.org/pdf/2501.13958) · [GraphRAG multi-hop analysis (SingleStore)](https://www.singlestore.com/blog/rethinking-rag-how-graphrag-improves-multi-hop-reasoning-/)

---

I did not write any file — this digest is returned inline as requested. 16 primary/strong sources cited, organized to the eight requested sections plus a decision-table synthesis. The most actionable finding for your project: the just-in-time-files + Skills + reflection-into-linked-concept-notes stack maps cleanly onto infrastructure you already have (`CLAUDE.md`, `docs/concepts/`, [[iteration_findings|iteration_findings.md]]), and defers the heavyweight memory-layer services until cross-session contradiction or window pressure actually demands them.
