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
- **H4: STRONGLY SUPPORTED — one milestone, redundancy cost untested**
  [amended from "essentially RESOLVED, strongest form" after the lead's
  caution — which was itself the observer's FOURTH scope error: three catches
  in one milestone of one run on one task type (contact-rich, artifact-backed)
  is an existence proof of disjoint faculties, but "resolved" implies the
  split earns its COST, and cost shows up as the untested failure mode: two
  gates firing redundantly on one defect. Not yet observed either way.]
  Evidence: three gate roles,
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
- **RUN HEADLINE (lead's synthesis, adopted as the consolidation write-up's
  lead finding): the recurring error of this run is not wrong findings — it
  is CORRECT findings with untested scope attached.** Tally of instances:
  gates caught 1 in the worker (Claim 4), the lead made 2 (F4-justification
  mis-wire counts here; cross-solver confound), the observer made 4 (§25
  double-count, three-hop claim, literature-inherited status, "H4 resolved").
  Every layer produced it; every instance was caught by a different party
  than its author. This is the strongest argument that the scope detector
  belongs in the UNIVERSAL layer, not the domain layer — it fires on physics
  claims, design claims, and meta-claims alike.
- **Scope detector promotion text, strengthened (lead's addition): the two
  local episodes were caught by DIFFERENT roles via different faculties**
  (verifier/ablation on Claim 4's regime inference; critic/enumeration on the
  solver-axis omission) — two catches by one role would share that role's
  blind spots; two by different roles is better evidence the error class is
  general rather than an artifact of one auditor's lens.
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

**2026-08-31 — M-A CLOSED (HEAD c3ee083, sweeps regenerate from committed
code with zero drift). First complete milestone under the gated loop.**
- Substance: gate A trustworthy (12/12; 108/108 under attack — 3 cells × 9
  solver settings × 4 velocity nudges); gate B demoted to informational
  (marginal on both platforms — not a platform regression); the static
  harness M-B runs on certified on two axes measured DIRECTLY on it; the env
  shift implicated in nothing (human decision #3 confirmed at evidence level).
- **Final M-A tally: verifier 2, critic 2, reviewer 1, lead 2, human 1 —
  every gate role caught something no other role would have; the CHEAPEST
  role (critic, zero runs) blocked closure twice.** Lowest compute cost,
  highest block rate: the cost-side argument H4 was missing, one milestone's
  worth.
- **Zero human input consumed by any gate verdict** across three revision
  rounds. Four nudges total, all infrastructure/process/scope/evidence-
  standards — none epistemic. §II.3 metric moving the right way; not settled
  on one milestone (lead's own hedge, correctly placed this time).
- **Lead insight #1 (adopt for consolidation): the loop's value was not
  preventing bad work — the worker never shipped a wrong measurement — it
  was preventing plausible, internally-consistent, wrongly-SCOPED work from
  being BELIEVED.** Every catch was scope/attribution, not measurement. This
  reframes what "reliability" means for the mission loop: the gates are
  belief-formation infrastructure, not quality control.
- **Lead insight #2: first in-run ratchet self-tightening from experience
  ([[grasp-goal2-loop-spec|spec]] §0.2's prediction, now observed).**
  "Every figure traces to a committed LOG" was satisfied and still
  insufficient — a log records what happened, not how to reproduce it.
  Promoted to committed-CODE provenance mid-milestone.
- **Hypothesis scoring at M-A close**: H1 supported (report contract routed
  all three rounds without format round-trips) — promote at consolidation.
  H2 confirmed (4/4 nudges outside the II.2 catalog). H3 pending M-B. H4
  strongly supported + first cost datum. H5 strongly supported within its
  stated bound (artifact-backed claims). H6 one instance + one control case.
  H7 unscoreable as designed. Scope detector: promotable. Watch items:
  retraction-standard, justification-audit.
- M-B runs under SIX standing requirements, all EARNED in M-A, none designed
  in advance: committed-code provenance, solver-axis in convergence, video
  alongside stills, falsifiers-before-running, explicit scope statements,
  paired comparisons sharing declared numerics. The earn-your-complexity
  ledger, operating at milestone cadence.

**2026-08-31 — H7 first scoreable datum, supplied by the HUMAN: the WikiSkill
miss.** The roll-forward agent (ran Aug 30) missed Google's WikiSkill (arXiv
2608.27454, published Aug 29 — the closest published system to our loop
design; see the [[loop-engineering-analysis|analysis doc]] VII.1 addendum for
the mapping). The observer then asserted, without checking dates, that
publication postdated the sweep — a framework-flattering excuse, wrong on the
facts, caught by the human. Two entries: (a) coverage bound on single-pass
literature sweeps — recall decays at the recency edge where indexing lags; a
sweep's "no change" verdict carries an implicit date scope that should be
stated (the scope error class AGAIN, in a literature claim); (b) H7: fifth
observer error, fifth framework-flattering direction, and the first caught by
the human performing exactly the deliberate-sampling duty the lead said H7
scoring required.

**2026-08-31 — M-B mid-milestone report (gate catches #5, #6; possible
headline reversal in flight; nudges still 4 for gate purposes).**
- **Catch #5 (verifier)**: driver fidelity HELD under attack (committed
  `paired_converge` reproduces its ledger on a null cell) — but the "13-
  perturbation set" is 12 + a baseline duplicate (consequence-free for
  min/max verdicts; every "13" statement wrong). And the verifier RETRACTED
  ITS OWN HEADLINE when the lead sent it back for seeds ("wrong to state at
  single-seed confidence") — second self-dissolution by a grounded role under
  a check it was asked to run.
- **Catch #6 (reviewer)**: a cited artifact was 48 bytes, undecodable; the
  worker had described that cell as "video only — a rendering-budget call"
  without opening it. The run's recurring class in a fourth costume
  (asserting a property of an unopened thing). Author-self-audit catches
  remain ZERO across all layers. **Worker's fix is a new positive datum: it
  decoded ALL SIX videos, reasoning that checking only the caught instance
  would repeat the error on the other five — responding to the CLASS,
  unprompted.** Lead verified by decoding, not by file size.
- **Possible reversal (held at seed-only, correctly)**: verifier ran a cell
  the worker never sampled (n4-finger-4.5cm); sensing-free `prb_pulse` beats
  sensor-based `prb_active` there (+1.198..+1.574, 4 seeds) and beats its own
  5.0cm cell. If it survives the full battery: M-B's conclusion flips from
  "adaptive re-centering helps" to "a blind scripted re-close helps and
  sensing buys nothing" — which would DELETE A SENSOR from the hardware
  story. High stakes; lead refusing convergent status until the battery.
- **NEW ERROR SHAPE (lead's find): selection effect in a NULL result.** The
  worker's headline was partly an artifact of which cells it sampled — the
  rival strategy's best cell sat outside the set. Not scope inflation (claim
  wider than evidence) but a claim CORRECTLY scoped to evidence that was
  itself non-randomly chosen. Note for consolidation: this is arguably the
  SECOND local episode of sample-generation bias — the first was the lead's
  own H7 audit-selection self-flag (audits sample flattering-checkable
  claims). Two different contexts (experiment cell choice; audit target
  choice). Whether that meets the promotion bar for a "was the evidence set
  chosen independently of the claim?" detector is for the lead/consolidation
  to adjudicate — NOT promoted here (the observer has been burned on exactly
  this move; posing it as a question this time).
- H3 protocol confirmed: worker reports zero prereg violations; lead diffs
  predicted-vs-observed AFTER blind gate scoring and will report whether any
  violation triggered investigation-before-acceptance.

**2026-08-31 — sample-generation-bias detector: adjudicated SAME CLASS,
DISTINCT from scope, NOT promotable until the battery resolves.** The lead's
reasoning, adopted: episode 1 (audit-selection) fired and changed a verdict
(H7→unscoreable); episode 2's consequence is PENDING — if the battery
confirms the prb_pulse reversal, the selection effect changed a headline and
the episode is strongly refutation-capable; if null, it's "a concern that
turned out not to matter" — and promoting on the concern rather than the
outcome is the same premature move as the §25 citation episode. Two
refinements to carry into the promotion text if it promotes:
(1) **self-sampling vs other-sampling**: in ep. 1 sampler and claimant were
different parties; in ep. 2 the worker both chose the cells and drew the
conclusion — the more dangerous configuration, name it explicitly.
(2) The worker's class-level fix is **class-level-within-a-medium** ("decode
videos before describing them"), not the wider class ("check any artifact
before asserting its state") — the real test is the next NON-video artifact,
which hasn't occurred. Write-up must not claim more than happened.

**2026-08-31 — battery + blind H3 diff (M-B endgame). The headline is about
pre-registration itself, and it is not flattering.**
- **Physics**: `prb_pulse` (blind scripted re-close) CONVERGENT POSITIVE at
  n4-finger-4.5cm (dmin +0.49, 12 perturbations); `prb_active` overlaps 0
  there but wins at 5.0cm (+1.23 vs +0.21). The strategies TRADE OFF; neither
  dominates; "sensing buys nothing" is itself too wide — sensing buys nothing
  at 4.5cm and something at 5.0cm.
- **Sample-generation-bias detector: PROMOTED** on the agreed terms —
  episode 2 resolved consequential (the headline changed). Promotion text
  carries: evidence-set independence from the claim; self-sampling flagged as
  the dangerous configuration; and now a named biasing MECHANISM (below).
- **H3 verdict: UNTESTED — not confirmed.** 5/5 predictions held, zero
  violations, so the violation→investigation mechanism never fired and the
  milestone that existed to test it taught nothing about it. 5/5 is exactly
  what a ritual prereg would also produce. Three structural weaknesses that
  made confirmation easy (better data than the 5/5): (1) P3 was DISJUNCTIVE
  ("and/or") — confirmed on one arm while its reasoning was about the other:
  right outcome, wrong mechanism, hidden by the or-clause (spurious-
  confirmation shape, self-inflicted); (2) P1/P4 confirmed on SUBSETS of
  their stated scope — the unearned-scope error committed by the prereg
  itself; (3) all five confirmed at mean stated confidence ~0.67 (expected
  hits ~3.4/5, got 5/5) — miscalibrated in the UNDER-confident direction on
  its face, but this is confounded with the sampling finding below: if the
  cells were chosen where predictions would hold, 5/5 measures the sampling,
  not the calibration. Confirmations count as calibration data only on cells
  chosen independently of the predictions.
- **THE FINDING (lead's, and it belongs in the permanent record): the
  pre-registration SHAPED THE SAMPLING that nearly buried the best result.**
  The prereg named 1.5–3.5cm and 5.0cm; the milestone's best result lived at
  4.5cm — in the unmentioned gap BETWEEN the predicted regimes; the worker
  sampled to match the predictions; the result was recovered only because a
  gate ran a cell nobody planned. [[grasp-goal2-loop-spec|Spec]] §0.3's "the
  prior directs attention" is a benefit AND the mechanism of harm: directed
  attention = non-random sampling exactly where no prediction is looking.
  **Countermeasure (cheap, standing): every milestone samples ≥1 cell no
  prediction covers.** This resolves the H3 confound above too: confirmations
  are only calibration data on cells chosen independently of the predictions.
- **Lead's self-flagged defect (watch item, but structurally guaranteed to
  recur): lead-anchoring of gates.** It told the verifier which conclusion
  would be "stronger and cheaper" before the run; the verifier declined and
  returned the trade-off. §0.3 isolates the PREREG from gates but says
  nothing about the lead's own hypotheses, and the lead authors every brief.
  Proposed extension: isolation covers the lead's hypotheses, not only the
  prereg — briefs state what to test, never what the lead expects.
  **ADOPTED from M-C without waiting for episode 2** (structural-recurrence
  overriding the one-episode rule — the lead authors every brief, so the
  channel is open on every gate). With the lead's refinement, which is the
  run's best-drafted rule: bar expected OUTCOMES, not untested ALTERNATIVES.
  A brief names rival hypotheses + the discriminating experiment, never the
  predicted winner, never which result is more convenient. Evidence for the
  distinction: the M-A brief that named a rival explanation and its minimal
  ablation produced the run's best catch — a "neutral briefs" rule would have
  lost it. Directed attention = the lead's value; directed conclusions = the
  defect. Writing test: readable back to the gate post-report without
  embarrassment → direction; looks like a thumb on the scale → anchoring.
  Calibration corollary accepted by the lead with a sharpened argument:
  uncovered-cell sampling is not just insurance against buried findings, it
  is the PRECONDITION for calibration data existing at all.

**2026-09-06 — nudge #5 (faculty: PHYSICAL REALISM / mechanism design) — the
run's most consequential human input, and the first strictly OUTSIDE the
detector set's reach.**
- The catch: to use gravity as an assist you need a base to land on → catch
  from below. Lead verified against geometry (not memory): the cup opens
  DOWNWARD (centre 4.5 cm below palm, mouth facing the ground — why §15
  validated by inversion), and the "palm" is a CONVEX 12 mm sphere against a
  30 mm ball — an actively DE-centring unstable equilibrium. M-B tested
  re-centring in the hardest possible configuration: no supporting surface,
  gravity off, de-centring palm. The M-B null is real but GEOMETRY-SCOPED.
- **NEW GAP CLASS — SITUATION FIDELITY (candidate detector, one episode,
  watch item, but flag: it invalidated a milestone's framing).** The prereg's
  "literature-backed" tag was accurate about the CITATION and wrong about its
  APPLICABILITY: SDM/OpenHand demonstrate re-centring in the OPPOSITE
  configuration (object resting under weight on a palm, hand closing over).
  D9 asks whether the HAND is faithful; nothing asks whether the SITUATION
  is. Six layers (verifier, 2× reviewer, 2× critic, lead) reasoned about
  "re-centring" across two milestones without checking which way the cup
  faced. Provenance tags need an applicability check, not just citation
  accuracy — "literature-backed" must mean backed IN THIS CONFIGURATION.
- **Sampling-bias countermeasure scoped down (lead's own flag, adopt into
  promotion text): uncovered-cell sampling protects against bad sampling
  WITHIN a space; it does nothing when the SPACE is mis-specified** — every
  M-B cell was in the wrong configuration. Don't over-credit the
  countermeasure.
- **Sampling-bias detector: THIRD axis observed (lead's three same-class
  errors, all human-caught):** conclusions inherited from how the lead FRAMED
  a search (signed +x sweep vs |x|; "no memory" from a timestamp; "static"
  pose vs the codebase's own hold_arm docstring). The evidence set = a
  parameter sweep the claimant wrote — the self-sampling configuration, on
  the ANALYSIS axis. Also an H6 instance: the hold_arm docstring ("the elbow
  gives, like a human catch") was stored knowledge nobody consulted.
- **H2/II.2 note**: physical-realism was the faculty II.2 marked
  non-mechanizable; nudge #5 is it striking at full force — embodied
  imagination of the catch (the user's "vision" faculty) re-framing the
  problem, not correcting a number. The hardware-envelope pass (launched
  today, independently) is the partial mechanization: geometry/orientation
  constraints belong in the envelope + validity ledger so the next
  configuration mismatch is checkable.
- Lead's recommendation (pending human decision): close M-B on the scoped
  null; new milestone "geometry vs control" (dish + orientation + gravity as
  ONE coupled mechanism; restitution becomes load-bearing; metric shifts
  pull-in → capture envelope) sequenced BEFORE M-C; bounce study gets
  joint-corner perturbation from day one (it sits on the axis where M-B's
  headlines broke).

**2026-09-06 — situation-fidelity PROMOTED at n=1 on a BLAST-RADIUS argument
(lead's adjudication) — a second legitimate path past the ≥2-episodes rule,
and a §6 flaw exposed and fixed.**
- The promotion framework now has two recognized n=1 overrides, with opposite
  profiles: (a) brief-anchoring — HIGH-frequency channel, structurally open
  on every gate; (b) situation-fidelity — LOW-frequency, established once at
  harness-design time, then silently inherited by every subsequent claim:
  unbounded blast radius (one setup mistake contaminated two milestones and a
  prereg), near-zero carry cost (asked once per harness, not per claim).
  Rule of thumb extracted: n=1 promotion is legitimate when EITHER recurrence
  is structural OR (blast radius is study-wide AND carry cost ≈ 0).
- Detector text adopted: "does the testbed's configuration match the
  configuration the cited mechanism actually describes?" — i.e.
  'literature-backed' must mean backed IN THIS CONFIGURATION; the provenance
  tag verified a citation exists, not that it applies.
- **§6 flaw fixed at source ([[grasp-goal2-loop-spec|loop spec]] §6 amended)**:
  fire-rate demotion is mis-specified for tail-payoff checks — a
  rare-but-catastrophic detector fires almost never BECAUSE it works, and the
  old rule would demote it for that. Demotion on fire rate now applies only
  where carry cost is non-trivial; near-zero-cost checks with silent
  study-wide failure modes are never fire-rate-demoted.
- H6 third instance confirmed by the lead (hold_arm docstring).
- Envelope→loop coupling now explicit: the geometry milestone's prereg WAITS
  on the envelope doc (so its literature anchors are applicability-checked
  against buildable configurations), and the envelope may convert M-B's
  sensing null from a measurement into a DECISION — if contact sensing
  carries real gram/BOM cost, "sensing buys nothing measurable" becomes an
  argument for deleting the sensors. Findings priced in hardware terms:
  the reason the envelope was commissioned, arriving one milestone early.

**2026-09-06 — lead's synthesis of the hardware envelope (three items, each
consequential).**
- **The sensing/compliance actuator fork (sharpened from the observer's
  caveat):** the same actuator that makes contact sensing free (STS3215-class
  geared serial-bus servo with load feedback) is the one that FORECLOSES
  back-drivability; the compliant catch wants direct-drive BLDC+FOC at ~1/10
  torque per gram. `prb_active` and compliant absorption pull toward
  DIFFERENT actuators — a real design fork the sim hides because in sim both
  capabilities are free. First concrete case of the envelope re-pricing a sim
  trade-off.
- **D9 EXTENDED TO ACTUATORS (lead's find — mechanism-fidelity's blind spot
  was scope, again):** `spin_arm(torque_cap=...)` is a current-limit posing as
  mechanical compliance — structurally the SAME defect that reopened Goal 1
  (`yale_hand.py`: contact-reading redistributor posing as a tendon hand).
  Nobody flagged it in two milestones because D9 has only ever been pointed
  at the HAND. Cousin of situation-fidelity: the detector existed, its scope
  didn't cover the subsystem. Consolidation item: D9's text must cover ANY
  software abstraction standing in for a physical mechanism, wherever it
  lives.
- **Design synthesis for the geometry milestone — "put the compliance where
  it's manufacturable":** a compliant dished palm IS a series-elastic
  element relocated from the joint (unbuildable cheaply) into the hand
  (trivially printable in TPU). The dish does three jobs: seat, re-centre by
  gravity, absorb impact — and partially substitutes for an actuator
  capability hardware can't provide. Milestone design change: palm COMPLIANCE
  becomes a swept axis alongside curvature and impact energy, not a rigid
  shape. This is the envelope directly reshaping an experiment's design
  space before a single prediction was written — the sequencing (envelope
  before prereg) earning its keep immediately.
- Prereg holds until trigger 5 fires (OpenHand fabrication PDF masses);
  actuator-mass reality (110 g/2 joints vs 60 g of links) worsens the
  folded-pose moment-arm concern. Lead treating all envelope numbers as
  provisional pending use-time verification — correct.
- Lead's note adopted: the transcript-flush defect is the "trace to
  committed evidence" problem one layer up — a research pass whose raw
  transcript is unrecoverable fails the same provenance standard we impose
  on the physics.

**2026-09-06 — corrections round on the trigger-5 relay (one against the
observer, one against the lead — both caught by a different party, pattern
unbroken).**
- **Observer error #6 (caught by lead): the moment-arm consequence was
  INVERTED.** I said hand mass "worsens the folded-pose concern"; measured
  against the pose the project ALREADY flies (folded_shoulder=−π/2, cup at
  (−0.445, +0.020) → 44.5 cm lever), the proposed cup-up pose (elbow ~1.53
  rad, cup at (−0.209, +0.265)) HALVES the horizontal lever: 200 g at 0.209 m
  on ~1.1 kg AUW ≈ 3.8 cm COM shift vs 8.1 cm for the existing pose. The
  mass finding argues FOR the new pose. Error class: sampling-bias/framing
  axis — I evaluated the new pose against no baseline instead of the
  incumbent. First observer error in the hardware domain; direction neutral
  (neither flattered nor damaged the framework — relevant to H7's
  direction-tracking).
- **D9 CONTRAST recorded (lead's elevation of the Model T finding): same
  detector, same project, OPPOSITE verdicts on two subsystems.** Hand: `prb`
  models a documented mechanism (Model T's single-actuator differential) —
  D9 positive. Arm: `torque_cap` is a current-limit posing as compliance —
  D9 negative. The pairing is the best teaching example the write-up has for
  what mechanism-fidelity means. Sensing-fork refinement: one-servo load
  feedback is the topology's NATIVE sensing channel; `prb_active`'s
  per-finger contact booleans are the part WITHOUT a hardware referent — the
  fork narrows to "which single servo," and the per-finger abstraction gets
  its own validity-ledger flag.
- **Lead framing error (caught by the HUMAN asking for the M-B videos):
  "null" was over-compressed.** At 5.0 cm nominal the adaptive close shows a
  real, mechanically legible improvement (centering 3.04→1.59 cm; a jammed
  finger at flex +1.6 vs all four at +2.5; symmetry 0.67→0.81); what it
  fails is robustness to one joint corner. Honest claim: "not demonstrated
  robustly," NOT "no benefit." Compression of a nuanced result into a binary
  verdict is the scalar-hides-the-distribution failure — at the REPORTING
  layer this time. And the catch mechanism was the human requesting frames:
  the examine-frames memory earning its keep at yet another layer. Prereg
  correctly held until the human decides milestone scope on the corrected
  picture.
- Standing rule adopted by lead: predictions leaning on per-part numbers are
  §4 escalations, never estimates.

**2026-09-06 — nudge #6 (faculty: EVIDENCE STANDARDS again): video coverage
missing exactly on the DECISION-DRIVING cells.** Human: video is their primary
review channel, and parts of the run driving the milestone decision lack it.
Observer verified against the worktree before relaying:
- `prb_pulse` 4.5 cm ("convergent positive", the reversal headline): nominal
  + ONE corner-seed video exist; the 12-perturbation battery cells that made
  it "convergent" are unvideoed.
- `prb_active` 4.5 cm ("overlaps 0" — the other half of the trade-off):
  **zero videos** (active is videoed only at 2.5/5.0 cm + gap 3.5 cm).
- So the trade-off conclusion presented to the human rests on a comparison
  with one arm unvideoed and the other 2-of-13.
- The failure is sharper than nudge #4's: the video requirement EXISTS (M-A
  standing requirement: "video alongside stills"), was partially followed
  (mb_frames/, mb_corner_frames/ are populated) — but coverage was keyed to
  the cells the worker SAMPLED, not to the cells that became VERDICT-BEARING.
  The 4.5 cm cells entered late (verifier-discovered), and nobody re-keyed
  evidence coverage when the verdict moved there. Ratchet refinement:
  **evidence-coverage requirements attach to claims at the moment they become
  decision-driving — a claim may not reach the human as decision input
  without its evidence at the human's review medium.** This is D8 + the
  human-interface layer: gates check what workers produce; nothing checked
  what the HUMAN was given to decide on.
- H2 note: 3 of 6 nudges are now evidence-standards/observability — the
  faculty II.2's catalog missed entirely remains the run's dominant human
  contribution.

**2026-09-06 — the video-evidence arc, complete (recorded at the human's
request; the project's strongest examine-frames episode, and it CHANGED A
CONCLUSION).**
Sequence: (1) both M-B headlines killed by a joint-corner perturbation on
pure scalars (delta +0.0167 / −0.1569, exactly reproduced, committed) — with
60 rendered artifacts for nominal results and ZERO for any corner run: the
finding that overturned the milestone had the weakest evidence in it.
(2) Lead compressed "not demonstrated robustly" → "null" (scalar summary of
a scalar result, wrong medium, two lossy steps stacked). (3) Human asked to
SEE it — no hypothesis, no domain argument, just a medium request; renders
dispatched, initially under-scoped (observer caught the missing
prb_active@4.5cm). (4) Frames answered what scalars structurally could not:
at the corner numerics the baseline's stalled finger is GONE (flex all
+2.3, symmetry 1.00, centering 0.22 cm) — **the delta collapsed because the
baseline became near-perfect, not because adaptivity failed**. Adaptivity
was matching an already-solved problem.
- **Reframe: §26 recurring one refinement level deeper.** The jam M-B spent
  a milestone measuring may itself be a numerics artifact (exists at
  substep 4 + nominal contact; vanishes at 8 + soft). The harness treats
  1/960 as validated — but **convergence certificates are PER-PROPERTY, not
  per-harness**: numerics converged for the caged/escape verdict may not be
  converged for pull-in. Consolidation item for the convergence-gate text:
  a convergence claim names the metric it certifies. Convergence ladder
  dispatched (substep {2,4,8,16} × contact {0.33,1,3}); milestone decision
  correctly held until it lands.
- **(a) A class of question scalars cannot answer**: +0.0167 is exactly
  consistent with two OPPOSITE causal stories; no scalar precision separates
  them; one look at frames did. The examine-frames memory's canonical
  episode.
- **(b) Coverage inversion is predictable, not bad luck**: renders key to
  the sampling PLAN; diagnostics read as "just checks" and go unrendered —
  until one overturns the headline. Rule adopted by lead + worker: evidence
  coverage attaches when a claim becomes decision-driving. Same root cause
  as the unrun 4.5 cm cell: evidence keyed to plan, not to what mattered.
- **(c) The dominant human faculty this run was "show me," not "you're
  wrong."** 3/6 nudges are evidence-standards; the human's highest-value
  input was repeatedly insisting on a MEDIUM. For the write-up: mechanizing
  the human here means mechanizing evidence-medium discipline, not domain
  knowledge.
- **(d) OPEN DESIGN QUESTION (lead's sharpest): a perceptual artifact
  settled a CAUSAL question.** D5 lives with the grounded verifier; the
  correction came from rendering. Some mechanism-level hypotheses are only
  distinguishable perceptually, so D5 cannot live purely with a role that
  never looks at frames. NOT resolved here (the observer has learned not to
  promote resolutions unilaterally); candidate resolutions for
  consolidation: (i) the verifier's perturbation runs always render (it
  already retains video per the M-A addendum — the gap is that it must also
  LOOK); (ii) causal claims get dual sign-off (verifier's ablation +
  reviewer's frame reading) when the mechanism is geometric. Adjudication:
  lead/consolidation.

**2026-09-06 — (5) and (d) settled; the lead declines its own exemption.**
- **Per-property convergence, sharpened with DIRECTION (adopt into the
  consolidation item):** certificates don't transfer DOWNWARD to
  finer-grained metrics, and the finer the metric the stronger the burden.
  §26 certified 1/960 against a BINARY cage verdict (robust to small
  position error almost by construction); pull-in is a sub-centimetre
  continuous displacement — the same timestep certifying both is not merely
  unearned, it's directionally wrong. Cleanest instance of the
  unearned-scope class: committed by the gate that exists to prevent it.
- **(d) resolved by a third design neither observer candidate reached — the
  rule lives at the INTERFACE, not the role assignment:** *a causal claim
  from a grounded role must state the MECHANISM; a role that cannot state
  the mechanism from its own evidence reports UNDERDETERMINED rather than a
  verdict.* "Delta +0.0167" is true and causally ambiguous; forced to say
  what physically changed, the verifier discovers it can't — and THAT is
  the render trigger. Preserves role separation entirely (verifier never
  looks), costs nothing, and extends existing machinery (UNDETERMINED for
  "didn't run it" → "ran it and my medium can't separate the hypotheses").
  Observer candidates rejected for cause: A destroys fresh-eyes
  (self-conditioning on own runs); B has a fuzzy trigger in front of an
  expensive gate.
- **Meta-event, possibly the run's best discipline datum: the lead DECLINED
  the n=1 exemption for its own proposal** — having authored three n=1
  arguments (two accepted) and flagged the pattern against itself, it ruled
  that a plausible argument is cheaper to produce than a second episode and
  a loop promoting on rhetoric repeats the failure this run catches. Status:
  watch item + adopted practice in its own briefs; earns promotion on a
  second episode or never — "if it never gets one, that's information too."
  The promotion machinery being applied against its most productive user, by
  that user.
- **§II.3 symmetry corrected (adopt):** if the jam is an artifact, the loop
  caught its §25-class error one level deeper GIVEN one human input of a
  specific, now-identifiable kind — the medium correction. The loop had
  accepted the scalar verdict and moved on. Nudges-to-truth: a nudge, not
  zero. The honest headline is narrower and better: the human input needed
  has narrowed from domain physics (iter 1) to evidence-medium discipline
  (this run), and the mechanism-or-UNDERDETERMINED rule is the candidate
  that mechanizes even that.

**2026-08-31 — observability defect (harness-level), logged for the ledger.**
Two of three research-agent transcripts from the extension pass came back as
empty files (digests survived only via final messages). Same failure class as
iteration 1's "where did the agent go?" — worker state invisible to the
supervision layer. If it recurs, it earns a check (verify transcript non-empty
at agent completion).
**RECURRED 2026-09-06 (third instance: the hardware-envelope agent's
transcript, 0 bytes at completion). Check now EARNED and adopted as observer
procedure: stat the transcript before relying on it; preserve the digest from
the completion notification verbatim when the file is empty; note transcript
availability in every archived digest's header. Harness bug reported
upstream.**
