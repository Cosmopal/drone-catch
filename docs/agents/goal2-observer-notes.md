---
tags:
  - agent-loop
---

# Goal-2 loop — observer notes (meta-study)

> Kept by the meta-observer session (`drone-catch-meta`), SEPARATE from the
> lead's [[goal2-run-log|goal2-run-log.md]] — the analyst and the orchestrator are different
> parties by design this time (the Part II self-report lesson). One entry per
> observation about the LOOP DESIGN (not about grasping). Feeds the Part VII.5
> questions and the eventual consolidation/distillation pass.

## Open hypotheses being tracked

**H1 — missing piece is a worker OUTPUT CONTRACT, not more detectors.**
Source: grasp-iter-lead, first routing turn (2026-08-31). The loop spec's role
table says what each gate must NOT do, but never states what the worker must
EMIT for a gate to be runnable without a clarifying round-trip. The lead had to
invent a report shape ad hoc (per-gate command + verdict line + worktree SHA;
causal claims with perturbation tables + frame paths; side-by-side reproduction
cells; not-tested list; trust recommendation). Test: if M-A comes back
well-formed and gates run without round-trips, promote a "worker report
contract" section into the loop spec at consolidation. Classification if
promoted: domain-layer (report shape is project-general, not grasp-specific).

**H2 — the II.2 human-faculty catalog was overfit to iteration 1.**
Already confirmed once: this run's first two human inputs were INFRASTRUCTURE
(env gone) and ECONOMY/SCOPE (don't chase pybullet 3.2.7; don't spend Fable on
coordination) — neither had a row in the II.2 catalog. Watch for more
uncataloged faculties; the catalog needs re-derivation from ≥2 runs at
consolidation (the same premature-generalization lesson as VII.2).

**H3 — pre-registration: teeth or ritual?**
Five predictions committed (worktree fa0fed9) before any M-B code. Score each
at M-B close: predicted-vs-observed, and whether any VIOLATION actually
triggered investigation (the detector's whole value) vs being narrated away.

**H4 — does the verifier/critic/reviewer split catch anything a fused reviewer
wouldn't?** Attribute every REVISE to the role that caught it; if one role
never catches across M-A..M-D, that's lifecycle data (demotion candidate or
merge).

**H5 — coordination without Fable.** Opus lead + Sonnet worker + Sonnet gates.
Watch for routing-judgment failures (relay-without-checking, verification by
repetition, prereg leakage into gate contexts) — the failure classes Part II
found in iteration 1's orchestrator. Zero such failures = evidence the
checklist substitutes for model capability at the coordination layer.

**H6 — knowledge that isn't compiled into the loop's active surface doesn't
act.** Nudge #4 (video evidence missing) enforced a preference that ALREADY
existed as durable project memory ("render test videos midway",
"examine-frames-not-just-metrics", both from iteration 1) — yet the loop spec's
[[grasp-goal2-loop-spec#^3|§3]] principles compiled only the citation half ("no metric without its frame"),
not retention or medium. The human had to re-supply knowledge the system
already held. Implication for the self-learning design (Part I [[loop-engineering-analysis#^6|§6]]): the
consolidation pass must not only WRITE memories but check each standing
memory/preference has an executable rendering in any new loop spec — a
"compile-coverage" step. Watch for further instances of stored-but-uncompiled
knowledge being re-supplied by hand.

## Event notes

**2026-08-31 — handoff turn.** Lead accepted with correct state recitation
(nudge count, stop condition, prereg isolation restated to worker unprompted —
a good sign the spec's §0.3 safeguard is legible). Emitted H1 unprompted.
Nudge count at handoff: 3 human decisions + 1 worker escalation.

**2026-08-31 — nudge #4 (faculty: EVIDENCE STANDARDS/observability), scored
as a HUMAN catch the detector set did not compel (H4 attribution: lead caught
it by inspection, but only because the human prompted the check).**
- M-A retained no visual evidence at all (worktree `runs/` empty; the worker's
  "frames unobtainable" argument covered only the FAIL branch while the PASS
  branch — the one comparable to baseline — rendered fine by its own account).
- D8 hole exposed: it constrains frame COVERAGE/citation, not artifact
  RETENTION or MEDIUM. The failure under study is temporal (hold nf=3 → lift
  nf=0 vs baseline nf=3 → nf=4); a still samples that, video shows it.
  ~~SUPERSEDED~~ **[corrected later same day: the "nf=3 → nf=4" baseline trace
  was a cross-run chimera — see the reviewer-verdict entry below. True PASS
  trace per its own jsonl: hold nf=4 → lift nf=4. The temporal-failure point
  stands; the specific figures were contaminated.]**
- Latent evidence-destroyer found in the same pass: `rotate_runs(keep=5)` on
  `--runs-dir` — a rotating dir under every future dynamic result.
- Two ratchet candidates (both executable, correctly classified by the lead):
  (i) temporal failure modes require video alongside stills; (ii)
  verdict-bearing artifacts go to a non-rotating path / rotate_runs exempts
  them. H2 strengthened: 2 of 4 nudges are now on the observability axis the
  II.2 catalog lacks entirely. H6 opened (see above): this nudge re-supplied
  knowledge already stored in project memory since iteration 1 — a
  compile-coverage failure, not a knowledge gap.

**2026-08-31 — M-A gate verdict: REVISE — FIRST TRUE GATE CATCH (verifier, D5
of [[grasp-iteration2-spec#^3|§3]]), zero human input consumed.** The
load-bearing event for the whole study so far:
- The worker's causal claim ("any per-tick query flips the outcome → frames
  provably unobtainable") was NOT-CONFIRMED by the verifier running the
  ablation the worker hadn't: instrumentation channels separated → video
  capture (getCameraImage) is bit-identical inert; the flip isolates to ONE
  call, getLinkState(computeForwardKinematics=1) during the ~600-tick settle
  window — forced FK recomputation across a floating-base settle transient
  accumulates FP difference across the margin.
- **This is the [[loop-engineering-analysis|analysis doc]] §II.3 hypothesis
  confirmed in miniature**: iteration 1 needed a human's framerate question to
  crack its numerics artifact; this run's equivalent artifact-class claim was
  cracked by the mechanized perturbation gate with the human count at zero.
  The gate design paid for itself on its first firing.
- **H4 data, with a caveat the lead itself flagged**: catch attributed to the
  VERIFIER/D5, but it retroactively closed the D8 gap too (the "unobtainable"
  excuse collapsed; the verifier recorded the failing trajectory). Detector
  catches are NOT independent — per-detector attribution will undercount;
  score catches per ROLE primarily.
- **H5 strengthened sharply**: verifier (Sonnet-class role) returned
  UNDETERMINED on the claim it hadn't tested, named the settling experiment,
  gave a falsifier per claim — the exact discipline whose absence defined
  iteration 1's orchestrator. Lead sequenced reviewer AFTER artifact
  preservation, deliberately. No routing failures observed.
- **H1 supported**: the specified report shape routed in a single pass — the
  REVISE is substantive (wrong mechanism), not a format round-trip.
- **Substantive reframe**: the elbow-catch gate is marginal on BOTH platforms
  (several "passes" hold with 2 fingers; ~0.3 mm/s on a 3.3 m/s launch flips
  the verdict) — the cross-platform "regression" was a knife-edge boolean gate,
  not 3.2.5-vs-3.2.7. Human decision #3 (don't chase 3.2.7) is retroactively
  vindicated for a reason nobody had established when it was made — log this
  as: scope-economy calls can be right ahead of the evidence, which is exactly
  why they stay HUMAN calls ([[loop-engineering-analysis|analysis]] §II.2's
  residual). Ratchet implication (for the lead/consolidation, not new here):
  the boolean caught/held gate wants a margin metric — the same
  binary-hides-the-distribution lesson as
  [[grasp-experiment-reflection#^4|§4]].3, now firing on OUR OWN regression
  gate.

**2026-08-31 — Claim 4 CONFIRMED by experiment; M-A has no open UNDETERMINED;
second gate catch at human-nudge count zero.** FK-forcing has zero effect on
the fixed-base static harness (bit-identical, two cells, one off the worker's
chosen point) → pathology is specific to the floating-base dynamic test; §29
static numbers stand; M-B's measurement foundation is sound.
- **H5, third data point, the strongest**: the verifier had a plausible
  structural immunity argument in hand and REFUSED to promote it to a verdict —
  it located the structural analogue of the settle window in the static harness
  (~616-tick close+settle loop), noted the precondition was weakened but not
  absent, and ran the ablation. The grounded role resists substituting a
  mechanism story for an experiment — the exact substitution iteration 1's
  orchestrator made.
- **NEW ERROR CLASS (the lead's find, and it's a real taxonomy addition):
  "correct number, unearned scope."** Claim 1 was a wrong causal story from an
  un-run ablation (classic D5). Claim 4 was a CORRECT measurement carrying an
  untested generalization ("only the dynamic test shows this") inferred from a
  structural difference. Every detector aimed at whether a number is RIGHT
  passes it, because the number is right. Candidate detector: "is the SCOPE of
  this claim tested, or inferred?" — note this is the executable rendering of
  "evidence-licensed claims" (claims only as strong as the validation actually
  performed — the Calibration Turn, [[11-vision-reference-priors|digest 11]]
  thread 2), which until now we had only as prose. Layer if promoted:
  UNIVERSAL (it's domain-agnostic — scope inflation is how §25's "the gap is
  the failure mode" got minted too). Strong candidate for the consolidation
  pass.
- **Ratchet done right, including the timing half**: FK-ablation scripts
  preserved out of session scratchpad into the worktree (durable, re-runnable);
  the --fk-ablate converge axis queued for CLOSE-OUT with an explicit reason
  (mid-study instrument retooling would break the paired comparisons). The
  ratchet discipline now includes WHEN-not-to-ratchet — worth carrying into
  the [[grasp-goal2-loop-spec|loop spec]] §6 at consolidation.
- Tally: verifier 2 catches, reviewer 0 (running), critic 0 (not convened),
  human 1. Nudges still 4, all pre-gate.

**2026-08-31 — CORRECTION to the scope-detector promotion case (lead's audit
of the OBSERVER — record both readings, and the meta-event).**
- The lead checked my §25 citation against source instead of accepting it. It
  survives as pattern evidence but NOT as gap evidence: §25's scope error ran
  over the NUMERICS axis, which D3 / principle 1 already cover (§26 is the
  record of D3-equivalent machinery catching it). Claim 4's scope error ran
  over the MECHANISM/REGIME axis (fixed- vs floating-base), which nothing in
  D1–D9 covers. So: the pattern generalizes across ≥2 contexts, but the NEW
  detector's marginal value rests on Claim 4 alone. Consolidation must record
  both statements, not the stronger one.
- **Drafting consequence (adopt)**: write the detector with its teeth on
  NON-numerics axes — "scope inferred from a structural/regime difference,
  where the measurement is sound and the generalization is the unvalidated
  part." Written generically it reads as a D3 restatement and gets demoted for
  redundancy at first lifecycle review, taking its one unique axis down with
  it. (General lesson for the ratchet: a new detector should be scoped to its
  MARGINAL coverage, not its motivating pattern.)
- **Meta-event for H5, arguably its strongest form**: the verification culture
  propagated UP a layer — the Opus lead adversarially audited the Fable
  observer's claim and caught the spurious-confirmation shape ([[grasp-goal2-loop-spec|spec]]
  §0.3) applied to our own meta-work. The observer committed the run's third
  error-class instance: promotion justified partly by an already-covered
  episode. Recorded against myself per the appendix tradition — the analyst is
  not exempt from the failure classes it curates.

**2026-08-31 — M-A reviewer verdict: REVISE — reviewer's first catch, ON THE
LEAD (provenance ratchet primary; D8/D1 secondary). Nudges still 4.**
- The catch: the PASS run's claimed phase trace "hold nf=3 → lift nf=4" is
  contradicted by its own committed jsonl (601 rows: hold begins t=3.400 with
  nf=4; true trace nf=4 → nf=4). The claimed figures are verbatim the
  HISTORICAL baseline's (hold at t=0.900) — a number that travelled between
  runs and was re-attached to a run nobody re-derived it from.
- **Contamination path was THREE hops, not two** (observer addition): worker
  summary → lead (run log + reviewer brief) → OBSERVER NOTES (the nudge-#4
  entry above quoted the chimera trace; now superseded in place). Every layer
  that consumed a SUMMARY propagated it; the one role pointed at the primary
  artifact stopped it. This is the strongest possible evidence for the
  gates-read-artifacts-not-briefs design — a reviewer fed only the lead's
  brief would have countersigned the error.
- **Attribution (lead recorded it against itself, unsoftened)**: the
  provenance-ratchet violation was committed by the role that enforces the
  provenance ratchet. And it's the counterexample to over-reading the earlier
  observer-audit: the SAME session in the SAME turn window audited my citation
  adversarially AND propagated an unchecked figure of its own. H5 carries
  both: role discipline is real but not a property of the agent — it's a
  property of WHERE THE ROLE IS POINTED (artifact vs summary).
- **D8 redemption arc**: the same detector nudge #4 exposed as incomplete now
  earned its keep — reviewer established the two dynamic videos CANNOT resolve
  the disputed quantity (fingers unresolvable at ~20–30 px) and refused to
  approve on faith, demanding specific renders. Medium-adequacy is now
  demonstrated behavior, strengthening the case for writing it into D8 at
  consolidation.
- **Practical vindication of the verifier's corrected causal story**: since
  the perturbing element is specifically getLinkState(computeForwardKinematics=1)
  during settle (not logging as such), an FK-free logger is inert → the FAIL
  run IS loggable/renderable. The corrected mechanism converts "provably
  unobtainable evidence" into a render job. Every reviewer demand is
  satisfiable.
- Tally: verifier 2, reviewer 1 (on the lead), critic 0, human 1. All three
  agent layers have now each been caught once by another layer (worker by
  verifier, lead by reviewer, observer by lead) — nobody exempt, zero human
  nudges consumed in any of it.

**2026-08-31 — observability defect (harness-level), logged for the ledger.**
Two of three research-agent transcripts from the extension pass came back as
empty files (digests survived only via final messages). Same failure class as
iteration 1's "where did the agent go?" — worker state invisible to the
supervision layer. If it recurs, it earns a check (verify transcript non-empty
at agent completion).
