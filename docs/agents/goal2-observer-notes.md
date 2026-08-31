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
  **[correction history — both directions, kept deliberately:** (1) this
  baseline trace is TRUE — verified by the observer directly against
  `reg_elbow_catch.txt` (`t=0.900 -> hold ... nf=3`, `t=1.904 -> lift ...
  nf=4`); (2) a LATER chimera attached this baseline trace to the verifier's
  PASS run (whose own jsonl reads nf=4 → nf=4) — origin verifier, path
  verifier → lead → reviewer brief, caught by the reviewer; (3) the observer
  then OVER-RETRACTED, striking this true baseline fact as if it were the
  chimera — caught by the lead, restored after artifact re-check. Same error
  class both ways: REFERENT errors — right number, wrong run / right number
  detached from its right run.**]
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
- **Contamination path: TWO hops — verifier → lead → reviewer brief.**
  [Corrected: the observer first claimed three hops, mis-reading its own
  nudge-#4 entry as contaminated. That entry recorded the BASELINE trace,
  which is true (observer re-verified against reg_elbow_catch.txt directly);
  the chimera was created later when the verifier's report attached the
  baseline's trace to the PASS run. The observer's "correction" struck a true
  fact — the mirror-image referent error — and was itself caught by the lead.
  See the amended nudge-#4 entry.] The design conclusion survives at two hops:
  every summary-consuming layer propagated the chimera; the artifact-pointed
  role stopped it.
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
- Tally: verifier 2, reviewer 1 (on the lead), critic 0, human 1. Cross-layer
  catches so far: worker by verifier (causal story), lead by reviewer
  (chimera figure), observer by lead TWICE (spurious promotion evidence;
  over-retraction). Nobody exempt; zero human nudges consumed in any of it.
  [Amended from "each caught once": the observer's catch was on the
  OVER-CORRECTION, not on propagating the chimera.]

**2026-08-31 — two additions from the lead's second audit of the observer.**
- **Watch item (NOT promotable — one episode, per the marginal-coverage
  rule): "a retraction requires the same evidentiary standard as the claim it
  retracts."** Retractions are the more insidious referent error because
  struck-through facts read as settled and nothing in the loop currently
  audits a correction the way it audits a claim. If a second episode occurs,
  promote; layer TBD then.
- **Bound on H5 (lead's own caveat, adopted): both of its cross-layer catches
  were CHEAP, WELL-POSED checks against committed files it had direct access
  to.** The easy case. Neither says anything yet about claims that are
  diffuse, expensive to verify, or artifact-less — which describes most of
  what the meta-analysis itself asserts. H5 evidence is real but bounded to
  artifact-backed claims; the diffuse-claim case remains untested.

**2026-08-31 — consolidation input (lead): FINDING vs DESIGN-PREFERENCE
tagging — D6 applied one layer up.** For artifact-less claims, the analogue of
artifact-grounding: the claim must name what would count as evidence and where
it would come from, or be tagged a PREFERENCE, not a FINDING. Worked example
from this run: "gates read primary artifacts, not the lead's summary" was a
preference until the chimera episode gave it a falsifier and a case that
could have gone the other way — same sentence, different epistemic status,
and the change was the arrival of a refutation-capable episode.
- Practical gap it exposes: [[grasp-goal2-loop-spec|the loop spec]]'s §3
  principles, D1–D9, and the §0 deltas all sit at equal weight; several are
  preferences no episode has ever been able to refute. Consolidation step:
  tag each as finding (+ episode) or preference (+ promotion condition). This
  also gives §6's demotion machinery real teeth: "survived N runs untested"
  currently scores identically to "earned" — it shouldn't.
- **Observer addition — this is the §6.1 calibration log arriving bottom-up.**
  The original design proposed a claim+confidence+falsifier log top-down
  ([[loop-engineering-analysis#^6|§6]], the starred calibration row); the run
  just re-derived it from an operational need with a sharper trigger
  (untested-vs-earned distinguishability). Independent re-derivation is the
  best validation a design element in the PREFERENCE tier can get short of an
  episode.
- **On the hard version** — AMENDED after the lead's third audit of the
  observer (all three objections verified and accepted):
  (1) The observer over-claimed: [[10-generic-vs-specialized-loops|digest 10]]
  itself states its three-layer synthesis "is inference from those, not a
  citation" — the foreign episodes ground their own narrow claims (ADAS →
  pattern transfer; GEPA → prose overfitting; Voyager → executable transfer;
  METR → the failure split); the COMPILATION across them is our synthesis:
  analogy tier. The observer cited the digest while dropping the limit its
  own author had flagged.
  (2) A parallel finding/preference axis duplicates [[grasp-goal2-loop-spec|spec]]
  §0.3's provenance tags (literature-backed/analogy/guess) — unify, don't
  run alongside (marginal-coverage rule, applied to the observer's proposal).
  (3) "Literature-inherited provisional finding status" is a prior lowering
  the evidence bar — the spurious-confirmation shape (§0.3 asymmetric
  authority + prior-robustness), aimed at our own design claims this time.
  **Standing resolution (lead's amendment, adopted): foreign episodes license
  ATTENTION and PRIORITY, never STATUS. A design claim with only foreign
  episodes is a PREFERENCE carrying a literature-backed prior; promotion
  requires a local episode that could have refuted it. The triage rule
  survives: claims with neither local nor foreign episodes are preferences
  full stop and the cheapest to reverse.**

**H7 — direction-of-error gradient in the meta-layer (opened on the lead's
observation; watch, don't over-read).** Three consecutive observer errors ran
the SAME direction: each would have made our own framework look
better-grounded than it is (spurious second episode for the scope detector;
three-hop contamination claim; literature-inherited finding status). Zero ran
the other way. If the gradient persists, it's the meta-layer's own sycophancy/
self-confirmation analogue — the observer optimizing the study's narrative —
and the fix is structural per this run's own lesson: the observer's
load-bearing claims need an artifact-pointed auditor (which the lead is
currently providing ad hoc). Score at consolidation: direction of every
observer error, and whether any framework-UNFLATTERING observer error ever
got caught (if none is ever even made, that asymmetry is itself the signal).
**AMENDMENT (lead, raised against its own role-flattering hypothesis): H7 is
currently UNSCOREABLE — the sample has a selection effect.** The lead audits
claims that are (a) load-bearing for a decision AND (b) cheaply checkable
against a committed artifact. Flattering errors are characteristically
overstated citations, which trip both triggers every time (the overstated
source sits right there to check); unflattering errors ("weaker than we
think") typically have no artifact and no decision riding on them, so they'd
rarely be audited and likely not be noticed. "Zero unflattering catches" is
what this process produces even under direction-neutral error generation —
the asymmetry measures the AUDITOR'S SAMPLING, not the observer's bias. To
make H7 scoreable: deliberately sample the observer's modest/self-deprecating
claims and audit those too — the harder check, since confirming "better
grounded than stated" means assembling grounding nobody assembled. Fourth
instance of the run's signature error class (a real pattern wearing a scope
nothing tested), this time flagged by the party the hypothesis flattered, at
the moment the conclusion was agreeable — behavioral evidence that the
discipline is cultural, not only structural.

**2026-08-31 — M-A critic verdict: DO NOT CLOSE (D4/D6). Critic's first
catch; nudges still 4.**
- **H4 essentially RESOLVED, positive, strongest form**: three gate roles,
  three catches, three disjoint faculties — verifier by ablation (wrong
  mechanism), reviewer by primary-log reading (provenance chimera), critic by
  pure enumeration, running NOTHING (untested axis). Zero overlap. A
  homogeneous 3-panel would plausibly have made one catch three times
  ([[grasp-goal2-loop-spec|spec]] §0.1's premise, now with a worked
  demonstration). Note the cost gradient: the cheapest role (no runs at all)
  produced the milestone-gating catch.
- The catch itself: `numSolverIterations=150` hardcoded; converge_cell()
  sweeps substep/contact/seed but NEVER solver iterations → F5's "static
  measurement foundation is sound" rested on a battery that omitted the one
  axis that produced non-monotonic scatter dynamically. Lead withdrew the
  "sound" phrase pending the experiment. ALSO: arm_catch_solo's 12/12 was
  never attacked — "matches historical baseline" is evidence nobody tried to
  break it (golden runs need ATTACK PARITY with the gates they certify).
- **Scope detector: SECOND LOCAL EPISODE.** "Convergence-checked" carried
  scope over an axis never swept — correct measurements on swept axes,
  unearned generalization over the unswept one. With Claim 4, that's ≥2 local
  refutation-capable episodes: the "unearned scope" detector now meets the
  promotion bar on LOCAL evidence alone, exactly as the finding/preference
  machinery requires. Promote at consolidation.
- **Lead's own find (missed by worker, verifier, two reviewer passes, and
  itself until now): the two regression gates run at DIFFERENT solver
  settings** — elbow_catch_solo sets 150, arm_catch_solo inherits default 50.
  Every gate-A-vs-gate-B comparison this milestone was cross-solver
  confounded. Ratchet candidate (executable, domain layer):
  instrument-consistency check — paired gates must share declared numerics or
  the difference is stated in the comparison.
- **Fourth candidate detector (critic's sharpest point, one episode — WATCH
  ITEM per marginal-coverage): justification audit** — "is the JUSTIFICATION
  for this conclusion the evidence actually cited for it?" F4 (clean logger)
  was being cited for a conclusion only F3 (instability regardless of
  logging) supports; the boolean-gate demotion was right but mis-justified,
  and it survived three gates because every gate checks CLAIMS, not the
  inferential chain BETWEEN them. Distinct from the scope detector (scope =
  claim wider than evidence; this = right claim, wrong evidence wired to it).
- M-B remains blocked pending the solver-axis experiment + gate-A attack.
  Zero human input consumed by the entire M-A gate sequence to date.

**2026-08-31 — observability defect (harness-level), logged for the ledger.**
Two of three research-agent transcripts from the extension pass came back as
empty files (digests survived only via final messages). Same failure class as
iteration 1's "where did the agent go?" — worker state invisible to the
supervision layer. If it recurs, it earns a check (verify transcript non-empty
at agent completion).
