---
name: autonomy-general-detectors-not-failure-maps
description: "For autonomous loops on novel problems, install domain-general failure DETECTORS + a ratchet, don't pre-enumerate specific failure modes"
metadata: 
  node_type: memory
  type: project
  originSessionId: d155edbe-7048-4315-a7e7-ea544c31734d
---

The drone-catch autonomy program's core design principle. You cannot pre-enumerate
the *specific* failure modes of a blue-sky problem — the grasp experiment proved it:
nobody (sub-agent, orchestrator, OR the user) anticipated the §26 timestep artifact,
and the user's own "gaps too large" hypothesis was wrong (the bug spuriously
confirmed it). The artifact fooled all three "judges" because they shared one frame
("does it look right?"); only **running the experiment at varied numerics** recovered
truth.

**Why:** specific/content failures are unknowable in advance; general/structural
failures are a small, domain-agnostic, knowable set (the physics of measurement
error): metric ill-conditioning, goal≠proxy, causation-without-ablation,
testbed-can't-represent-the-property.

**How to apply:** install the ~6–10 **general detectors** (convergence/sensitivity
gate = vary timestep/contact-model/seed, require invariant verdict; falsifiability
gate = prove the testbed separates X from not-X; goal-vs-proxy critic; causal-ablation
gate) rather than a specific failure list. When a detector fires, the agent LOCALIZES
the specific cause (it's good at this once an anomaly exists) and that specific check
is RATCHETED into the permanent gate set. The failure map is GROWN, not pre-built —
this is the accreting "validity ledger" / "expertise of practical limitations."
Corollary: mechanical perturbation beats human review, because review can't catch a
numeric that looks right to every reviewer. Multi-perspective panels help ONLY if
deliberately diverse in what each attends to AND ≥1 member is grounded (runs the
perturbation), else they converge on a shared delusion. Full reasoning in
`docs/agents/loop-engineering-analysis.md` Parts II–IV. Relates to
[[examine-frames-not-just-metrics]].
