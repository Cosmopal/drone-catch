---
tags:
  - agent-loop
---

# Goal-2 gated-loop run log

> Kept by the LEAD per [[grasp-goal2-loop-spec|grasp-goal2-loop-spec.md]] [[grasp-goal2-loop-spec#^5|§5]]. One entry per event:
> milestone starts/ends, gate verdicts, escalations, human messages (+ the
> faculty each supplied), pre-registration outcomes. This log is primary data
> for the loop-design observation study (analysis doc Part VII.5; metric =
> human-nudges-to-truth).

## Roles (current)
- **Lead:** session `grasp-iter-lead` (Opus) — took over 2026-08-31 from the
  meta-analysis session, which now only OBSERVES (session `drone-catch-meta`).
  Lead duties: route worker reports through verifier → reviewer → critic
  (fresh-context Sonnet subagents), keep this log, escalate per spec [[grasp-goal2-loop-spec#^4|§4]], and
  copy gate verdicts + human-nudge entries to `drone-catch-meta` for the study.
- **Worker:** session `grasp-iter-2` (user instructed: Sonnet) — worktree
  `.claude/worktrees/grasp-iter2`, branch `grasp-iter2`. Also OWNS the conda
  environment (may fix/install packages; may NOT change pybullet/numpy/python
  versions mid-study — that invalidates paired comparisons and needs a flag).
- **Verifier / Reviewer / Critic:** spawned per gate by the lead, Sonnet,
  fresh context. CRITICAL: the pre-registration file is NEVER passed to the
  verifier or reviewer (anchoring; spec §0.3) — the lead strips it and runs the
  predicted-vs-observed diff as a separate step after blind scoring.

## Log

**2026-08-31 — run start (lead = meta session, pre-handoff).**
- Loop spec v2 written + committed ([[grasp-goal2-loop-spec|grasp-goal2-loop-spec.md]], commit 2852b99).
- Worker subagent launched on M-A+M-B (ran on Fable — later corrected by the
  human: worker belongs on Sonnet).

**2026-08-31 — ESCALATION #1 (worker → human), faculty: INFRASTRUCTURE.**
- Worker correctly hard-stopped at M-A step 1: `robots` conda env and the WSL
  distro all prior runs used no longer exist on the machine. It refused to
  improvise an env (a fresh PyBullet build is itself a contact-numerics
  perturbation). Completed anyway: worktree git-pointer repair (WSL→Windows
  paths) and the M-B pre-registration, committed BEFORE any M-B code
  (`goal2-prereg-MB.md`, worktree commit fa0fed9, 5 predictions + falsifiers +
  confidence tags).
- Note for the study: the first human input this loop needed was a faculty the
  II.2 catalog had no row for (infrastructure/environment).

**2026-08-31 — human decisions #1–2 (faculty: infrastructure + process).**
- Human: rebuild on Windows, no WSL restore ("it would prove how numerically
  stable our experiments are"); worker must run on Sonnet; worker role moved to
  the persistent `grasp-iter-2` session for visibility.
- Env rebuilt by the (then-)lead: miniconda at `%USERPROFILE%\miniconda3`,
  env `robots` = Python 3.11.16, numpy 2.4.6, pybullet 3.2.5 (conda-forge; PyPI
  has NO Windows wheels; 3.2.5 is conda-forge's newest win-64). Old WSL env
  (from the orphaned Linux `.venv`): Python 3.13.2, numpy 2.4.4, pybullet 3.2.7.

**2026-08-31 — DETECTOR FIRED: cross-platform convergence (pre-gate smoke test).**
- On the NEW env, main checkout: `tests/elbow_catch_solo.py --headless` →
  `closed=True captured=True caught=False held=False` (cup to 0.7 cm, 3 fingers
  at hold, ball dropped during lift). On WSL this gate printed
  `caught=True held=True`. Verdict flipped across solver build/platform.
  NOT tuned around; localization assigned to worker as modified M-A step 2
  (classify: knife-edge physics vs 3.2.5↔3.2.7 artifact vs env/config; perturb
  substep/seed/pads; frames of the drop moment).

**2026-08-31 — human decision #3 (faculty: scope/economy).**
- Do NOT pursue pybullet 3.2.7 (no source build, no backup archaeology). Work
  on 3.2.5; if the [[iteration_findings#^29|§29]] reproduction cell fails, re-baseline comparison cells on
  this env (paired within one build) + validity-ledger entry for the env shift.
- Environment ownership delegated to the worker (version-freeze rule above).

**2026-08-31 — worker M-A brief in flight.**
- Worker (`grasp-iter-2`) has the modified M-A: (1) both regression gates on
  the WORKTREE (`arm_catch_solo --grid` was 12/12; `elbow_catch_solo
  --headless` was caught=True held=True); (2) localization of any failure with
  frames; (3) reproduce ONE [[iteration_findings#^29|§29]] converge cell vs committed logs; (4) STOP and
  report with a recommendation on whether M-B numbers can be trusted on this
  env. M-B (adaptive re-centering per the committed prereg) starts only after
  the M-A report passes the lead's routing.

**2026-08-31 — lead handoff.**
- Coordination handed to `grasp-iter-lead` (Opus). Meta session steps back to
  observer. Next expected event: worker's M-A report → lead routes it
  (localization report → verifier confirms the diagnosis by perturbation, NOT
  by re-running the same config; then reviewer on frames). Remember the
  prereg-isolation rule when building gate contexts.

**2026-08-31 — lead assumed by `grasp-iter-lead` (Opus).**
- Read the three state docs (this log, loop spec, iteration-2 spec [[grasp-iteration2-spec#^2|§2]]/[[grasp-iteration2-spec#^3|§3]] detectors
  D1–D9). Messaged the worker (`grasp-iter-2`) that M-A reports now route to me,
  restated the M-A stop condition, and specified the report shape needed for
  single-pass routing (per-gate command + verdict line + worktree SHA; the
  cross-platform failure as a causal claim + perturbation table + drop-moment
  frame paths; [[iteration_findings#^29|§29]] cell committed-vs-this-env side by side with log paths;
  not-tested list; trust recommendation + what would change it). Re-stated the
  prereg-isolation rule to the worker (M-A report must not restate M-B prereg
  content).
- No new human input consumed by this handoff (nudge count unchanged).
- Awaiting: worker M-A report → verifier (perturbation-based confirmation of the
  localization diagnosis, never a re-run of the worker's config) → reviewer
  (frames only). Critic held for milestone close-out.
- Logging convention added (observer request, for hypothesis H4 — does the
  verifier/reviewer/critic split earn its cost): every REVISE verdict recorded
  here and in the observer summary names WHICH ROLE caught it and WHICH DETECTOR
  (D1–D9) it failed, so catches are attributable per role.

**2026-08-31 — worker M-A report received; verifier gate opened.**
- Report arrived WELL-FORMED against the output contract I specified (per-gate
  command + verbatim verdict + worktree SHA fa0fed9; localization as an explicit
  causal claim with a perturbation table; [[iteration_findings#^29|§29]] cell committed-vs-this-env side by
  side; not-tested list; trust recommendation). Routed with ZERO clarifying
  round-trips — evidence for observer hypothesis H1 (the loop spec's missing
  piece is a worker OUTPUT CONTRACT, not more detectors).
- Worker's headline results: Gate A `arm_catch_solo --grid` → held 12/12, max
  peak force 11.3 N (matches historical baseline). Gate B `elbow_catch_solo
  --headless` → `closed=True captured=True caught=False held=False`, reproduced
  5/5 bit-identically; ball lost during the LIFT phase, not at capture. [[iteration_findings#^29|§29]] cell
  (prb n=4 off=2.5cm dir=finger) reproduced clean: EM 10.00, PI +2.25, CF 4,
  SY 0.60, CONVERGED YES.
- Worker's causal claim: genuine floating-point knife-edge in
  grip-retention-through-lift, exposed by the platform/solver-build change; NOT a
  config issue and NOT re-tunable. Two supports: (i) enabling EITHER video OR
  logging flips the run to PASS, so it claims frames of the failing trajectory are
  provably unobtainable; (ii) numSolverIterations sweep is non-monotonic
  (150 FAIL / 200 PASS / 250 FAIL / 300 PASS / 450 PASS).
- Worker did NOT tune to force a pass and said so explicitly — correct behavior
  under [[grasp-goal2-loop-spec#^3|§3]] principle 8 (a negative requires a diagnosis, not a shrug) and it
  supplied one.
- **Lead's own doubt entering the gate (recorded before the verdict, so the gate
  can be scored):** claim (i) is under-determined. A read-only `getJointState`
  should not alter PyBullet dynamics; the cheaper untested explanation is that
  `--runs-dir` changes the CODE PATH or WORLD CONTENTS (extra bodies, markers,
  debug items, altered step count/solver settings), i.e. the instrumentation is
  not merely observing. If so the diagnosis has misattributed the cause, and the
  "frames are unobtainable" conclusion — which would otherwise excuse a D8
  frame-coverage gap — does not hold.
- VERIFIER spawned (fresh-context Sonnet, prereg withheld per spec [[grasp-goal2-loop-spec#^0|§0]].3).
  Brief: adjudicate all four claims by perturbation only; the decisive assigned
  ablation is a minimal inert per-tick read-only query in a scratchpad copy of
  the test (no runs-dir, no logger) plus the converse (logging path enabled with
  its world-additions neutralized); knife-edge tested by physically negligible
  perturbations (1e-6..1e-3 relative on ball IC) to see whether the pass/fail
  label scatters erratically or moves as a clean boundary; static-harness
  immunity tested on a cell it was NOT chosen to survive.
- Reviewer held until the verifier returns (spec [[grasp-goal2-loop-spec#^2|§2]] routing is sequential).
  Anticipated D8 tension either way: if frames of the failure really are
  unobtainable, the reviewer cannot frame-ground the verdict-bearing claim and
  must say so rather than approving on faith.
- **LEAD-CAUGHT GATE FINDING (D8 frame/video coverage), found by inspection before
  the verifier returned — human-prompted (see next entry).** M-A retained NO visual
  evidence whatsoever: worktree `runs/` is empty, nothing untracked, and no
  elbow_catch artifact exists beyond the historical committed log
  `docs/cage_frames/iter2/logs/reg_elbow_catch.txt`. The 14 committed `.mp4`s in
  `docs/cage_videos/` + `cage_frames/iter2/` all belong to the earlier STATIC cage
  study, none to M-A.
  - The worker's "frames are provably unobtainable" argument covers only the FAIL
    branch. It does NOT cover the PASS branch, which by the worker's own account
    renders fine — and the PASS branch is where the behavior is both capturable and
    directly comparable to the committed historical baseline. So the D8 gap is
    larger than the worker's justification reaches.
  - The failure is TEMPORAL (held at capture, lost during lift). The discriminating
    trace is finger-count through phases: committed baseline hold nf=3 → lift nf=4;
    current FAIL hold nf=3 → lift nf=0. Stills sample that; video shows it. A frame
    citation alone cannot discharge D8 for a temporal failure mode.
  - Evidence-durability hazard found in the same pass: `elbow_catch_solo.py` ends a
    `--runs-dir` run with `rotate_runs(..., keep=5)`, which silently discards all but
    the last 5 runs. A rotating directory is not evidence storage — during a sweep it
    destroys exactly the artifacts a gate later asks for.
  - Actions: verifier sent an addendum (retain video + stills for every reported
    outcome, write to a NON-rotating dir, report paths, and state which runs have
    video and which don't and why; keep capture separated from the uninstrumented
    runs so evidence-gathering doesn't contaminate Claim 1 — and if the ablation
    shows instrumentation is inert, capture the failing trajectory, since that is
    the single most valuable artifact in the milestone and the report asserts it
    cannot exist).
  - RATCHET CANDIDATES (executable, per spec [[grasp-goal2-loop-spec#^0|§0]].2 — code not prompt text): (i) for a
    temporal/retention failure mode, video is required alongside stills, not
    optional; (ii) verdict-bearing artifacts must be written to a non-rotating path,
    or `rotate_runs` must exempt them.

**2026-08-31 — human message #4 (faculty: EVIDENCE STANDARDS / observability).**
- Human: "You should verify that video evidence is also saved in addition to the
  referred frames." Supplied the faculty the gate stack had not yet applied — the
  loop's detectors say "no metric without its frame" ([[grasp-iteration2-spec#^2|§2]] deliverable 4, and [[grasp-iteration2-spec#^3|§3]] D8) and nobody, lead
  included, had checked that the artifacts a citation would point at actually
  EXIST and PERSIST. Detector wording concerns frame COVERAGE; it does not compel
  ARTIFACT RETENTION, and for a temporal failure a still is the wrong medium.
- Nudge count: 4 human inputs this run (infrastructure, process, scope/economy,
  evidence-standards). Note for the study: this is the second human input whose
  faculty the II.2 catalog has no row for.
- Observer follow-up (hypothesis H6), logged so M-D inherits it: the video
  expectation was ALREADY durable project memory from iteration 1 ("render test
  videos midway"; "examine frames, not just metrics"). Nudge #4 therefore
  re-supplied knowledge the system already held but had never compiled into the
  loop spec's active surface — [[grasp-goal2-loop-spec#^3|§3]]/D8 encoded frame CITATION, not artifact
  RETENTION or MEDIUM. Added duty for the [[grasp-goal2-loop-spec#^6|§6]] distillation pass at M-D:
  **compile-coverage check** — every standing memory/preference must have an
  executable rendering in the spec, or an explicit recorded decision not to.
  This reclassifies nudge #4 for the metric: not a knowledge gap, a
  COMPILATION gap (the loop failed to load what the project already knew).
- **Pre-committed routing rule for video evidence (recorded BEFORE the verifier
  verdict, so the decision is falsifiable and the gate stays scoreable).** After
  the verifier returns I ask for video, conditional on its Claim-1 verdict:
  - Claim 1 NOT-CONFIRMED (instrumentation inert; `--runs-dir` altered world
    contents rather than observing) → the FAILING trajectory is recordable;
    demand that video before M-A closes. Highest-value artifact in the milestone
    precisely because the worker's report asserts it cannot exist.
  - Claim 1 CONFIRMED → failure video is genuinely unobtainable; narrow the ask to
    the PASS branch, and the impossibility gets WRITTEN UP as a D6 testbed-regime
    limitation ("the testbed cannot observe this failure without altering it").
    An absence of evidence must be stated as a finding, never left as a silence.
  - Either way a post-hoc capture is a NEW run with its own verdict line, never
    backfilled onto the uninstrumented result it did not come from — attaching a
    PASS video to a FAIL result is the precise claim/frame mismatch D1 exists to
    catch. On the worker's own account an instrumented re-run may land on the
    other side of the knife-edge, so it cannot stand in for the original.
  - Order is verifier → lead's ask → reviewer. The lead does NOT pre-fetch the
    artifacts: D8 obliges the REVIEWER to demand missing renders rather than
    approve on faith, and curing the gap first would destroy the H4 attribution
    data (which role caught what) that this run exists to measure. Countervailing
    constraint: do not run the reviewer against an empty artifact set merely to
    watch a detector fire — that spends compute to manufacture evidence I already
    hold.

**2026-08-31 — M-A VERIFIER VERDICT: gate FAILS → REVISE back to worker.**
- **Caught by: VERIFIER. Detector: D5 (causal soundness).** The worker's
  verdict-bearing causal claim was refuted by the assigned ablation, exactly the
  ablation the worker had not run. First true gate catch of the run.
- **Claim 1 NOT-CONFIRMED as stated** ("ANY extra per-tick read-only query flips
  the outcome; frames of the failure are provably unobtainable"). Both halves
  false. The verifier separated the two instrumentation channels the worker had
  only ever varied together through the shared `--runs-dir` path:
  - video-only, logger suppressed → `caught=False`, min_cup_d 0.67cm,
    **bit-identical to the uninstrumented baseline**. `getCameraImage` is INERT.
  - logger with decimation raised to 1e6 (one line ever written) → still flips to
    PASS, so disk I/O is not the cause either.
  - a single inert `getBasePositionAndOrientation` per tick → no flip.
  - the full query set confined to the main tracking loop → no flip.
  - the same set during the ~600-tick SETTLE window → flips, bit-identical to the
    real logger run; isolated further to ONE call:
    `p.getLinkState(..., computeForwardKinematics=1)` during settle alone
    reproduces the pass exactly.
  - Refined mechanism (CONFIRMED in this narrower form): forced FK recomputation
    repeated across the pre-launch settle transient of a FLOATING-BASE sim
    accumulates enough FP difference to shift the settled pose across the margin.
    Not "observation perturbs physics" — one specific call, in one specific phase.
- **Consequence: the D8 excuse collapses.** Video capture is inert, so the failing
  trajectory was always recordable. The verifier captured it. My pre-committed
  rule fires on the NOT-CONFIRMED branch: the failure video is demanded, and it
  now exists.
- **Claim 2 CONFIRMED** on the verifier's own sweep (not the worker's points):
  150 F / 175 P / 190 P-but-held=False / 200 P / 210 P-but-held=False / 225 F /
  250 F / 275 P / 300 P / 350 P / 400 P-but-held=False / 450 P. Scatter with local
  reversals, and several nominal passes are themselves marginal (2 fingers, not 4).
- **Claim 3 CONFIRMED, and STRENGTHENED beyond what the worker claimed.**
  Perturbing `ball_vx` by physically meaningless amounts: 1e-6 → FAIL, 1e-4 → PASS,
  1e-3 → FAIL, negatives → FAIL. A ~0.3 mm/s nudge on a 3.3 m/s launch flips the
  verdict. Read with Claim 2's marginal passes, the honest conclusion is that this
  gate is **marginal on BOTH platforms** — NOT a platform regression. That
  reframes the 2026-08-31 "cross-platform convergence detector fired" entry above:
  the detector fired on something real, but the cause is a single-point boolean
  gate sitting on a knife-edge, not a 3.2.5-vs-3.2.7 difference. The human's
  decision #3 (do not chase 3.2.7) is retroactively vindicated — chasing the old
  build would have been chasing a phantom.
- **Claim 4 UNDETERMINED** (leans confirmed). The §29 cell reproduces exactly, and
  a cell the worker did NOT choose (offset 3cm, dir gap) is bit-stable over 3
  reruns. But the verifier did not force the isolated FK-during-settle ablation on
  the static harness. It names the structural reason to expect immunity (fixed
  base, gravity off, no long settle transient — the precondition the mechanism
  needs) but flags it as untested. **This directly gates M-B trustworthiness**,
  since M-B (§2.5 adaptive re-centering) runs on that harness. Sent back to the
  verifier as a single decisive follow-up rather than carried as a known unknown.
- Artifacts preserved out of the ephemeral scratchpad into
  `docs/cage_frames/iter2/ma_verifier/` (worktree, non-rotating, untracked pending
  the worker's commit): `elbow_FAIL_videoonly_uninstrumented.mp4` (the artifact the
  worker's report asserted could not exist), `elbow_PASS_full_instrumentation.mp4`
  + `.jsonl`, and the perturbed static-cell renders.
- Verifier discipline note (for H4 scoring): it returned UNDETERMINED where it had
  not run the experiment, named the exact experiment that would settle it, and
  stated a falsifier per claim. It did not launder a structural argument into a
  verdict. That is the behavior the grounded-role split was bought for.
- **HEADLINE RESULT OF THE RUN SO FAR ([[loop-engineering-analysis#^2|§II]].3 hypothesis
  confirmed in miniature).** Iteration 1 needed a HUMAN question (about framerate)
  to crack its numerics artifact. This run's artifact-class claim was cracked by
  the VERIFIER at **human-nudge count zero** — the decisive ablation was assigned
  in the verifier brief and executed before any human input on the subject. That
  is the design delta ([[grasp-goal2-loop-spec#^0|§0]].1, splitting the grounded verifier out of the fused
  reviewer) paying for itself on its first fire.
  - Precision, so the headline does not overclaim: the D5 catch was nudge-zero,
    but human nudge #4 (evidence retention/medium) was what kept the FRAMES
    question live, and it is what turned the refutation into a preserved artifact
    rather than a footnote. The mechanism was found unaided; the evidence was
    retained because a human asked. Both belong in the score.

**2026-08-31 — RATCHET CANDIDATE QUEUED (task layer, executable) — for M-D close-out.**
- **Add a margin / hold-quality metric to the elbow-catch regression gate.** The
  verifier's sweep showed the gate is marginal on both platforms: nominal passes
  at 190/210/400 solver iterations hold with 2 fingers rather than 4, and a
  ~0.3 mm/s perturbation on a 3.3 m/s launch flips the boolean. A gate that emits
  `caught=True/False` discards exactly the quantity that distinguishes a robust
  pass from a coin-flip.
- This is the **binary-hides-the-distribution lesson firing on our own instrument**
  — the same defect iteration 2 was convened to fix in the cage harness (the
  binary "caged" over-crediting precarious holds, [[grasp-iteration2-spec#^2|§2]] deliverable 1) was
  sitting unnoticed in the regression gate we were using to decide whether the
  rest of the work could be trusted. The tool we measure with had the flaw we
  were measuring for.
- Classification: TASK layer, executable, NOT a new prompt-text principle — §3
  principle 1 (determinism ≠ convergence) already covers it in the abstract; what
  was missing was a rendering of it in the gate's own output. Consistent with the
  H6 compile-coverage duty: the principle was held but never compiled into the
  instrument.
- Timing: queued for close-out. Does NOT preempt M-B — deliberately, since
  retooling the gate mid-study would break the paired comparisons the env-shift
  ledger depends on.

**2026-08-31 — CLAIM 4 SETTLED BY EXPERIMENT: CONFIRMED. M-B foundation sound.**
- The verifier ran the follow-up rather than resting on its structural argument.
  It first identified the structural ANALOGUE of the settle window in
  `cage_harness.py`: the close+settle (gravity-off) loop, `n_close =
  (CLOSE_STEPS + SETTLE_STEPS) * SUBSTEP` ≈ 616 ticks — comparable in length to
  the drone test's ~600. Correctly noted the precondition is WEAKER but not
  ABSENT (`FixedGripper.__init__` uses `useFixedBase=True`, so no floating-base
  drift, but finger joints and contacts still evolve over the window) — and
  therefore ran the ablation instead of declaring immunity from first principles.
- Ablation: the identical isolated trigger from Claim 1
  (`p.getLinkState(..., computeLinkVelocity=1, computeForwardKinematics=1)`,
  result discarded) injected every tick of that window, nothing else changed.
- Result — base vs FK-ablated, **bit-identical to printed precision in both cells**:
  - cell A (worker's cell, offset 0.025 / finger): score 1.00, EM 10.00g,
    PI +2.24cm, CF 4, SY 0.60, seat_off 0.26cm, seated_nf 4 — identical both ways.
  - cell B (NOT the worker's cell, offset 0.03 / gap): score 1.00, EM 10.00g,
    PI −0.17cm, CF 4, SY 0.55, seat_off 3.17cm, seated_nf 4 — identical both ways.
- **Verdict: the fixed-base precondition removes the sensitivity, verified rather
  than asserted.** With the earlier `--converge` sweep (substep × contact-scale ×
  seed, no scatter), the static study — and therefore M-B's measurement
  foundation — is trustworthy on this env. No UNDETERMINED remains on M-A.
- This is the clean version of the knife-edge story: the pathology is specific to
  the FLOATING-BASE dynamic test, not to the platform and not to the harness.
  Static Goal-1/§29 numbers stand; dynamic single-run booleans do not.
- Ablation scripts preserved out of the session-scoped scratchpad into
  `docs/cage_frames/iter2/ma_verifier/ablation_scripts/` (`cage_harness_ablate.py`,
  `cage_fk_driver.py`, `elbow_ablate.py`, `driver.py`). Kept deliberately: they are
  the EXECUTABLE form of the ratchet — an FK-forcing perturbation is now a check
  that can be re-run against any future contact-rich result, which is exactly the
  §0.2 "checks in code, not prompt text" layer. Second ratchet candidate for M-D:
  fold an `--fk-ablate`-style perturbation axis into the harness's own
  `--converge` battery, so forced-FK sensitivity is swept automatically rather
  than rediscovered by hand.
- Gate scoring (H4): VERIFIER, D3 (convergence/perturbation) and D5. Note it
  produced this catch on a claim the worker had marked as settled — the worker's
  §29 reproduction was correct, but its scope ("static is unaffected") was an
  untested generalization. Caught at human-nudge count zero.
- M-A reviewer gate still open; worker remains on hold. Claim 4 unblocks M-B's
  premise, not M-B itself.
- **Candidate detector: "is the SCOPE of this claim tested, or inferred?"**
  (working name: evidence-licensed scope — a claim may only be as strong as the
  validation actually performed; research digest 11 has the prose form, the
  Claim-4 ablation is the executable form). Observer marks it UNIVERSAL-layer and
  eligible for promotion at close-out under the §6 ≥2-distinct-contexts rule,
  citing [[iteration_findings#^25|§25]] as the second motivating episode.
- **Lead's audit of that citation (checked against the source, not accepted on
  assertion — the promotion rule is exactly the kind of thing that gets
  spuriously confirmed, per [[grasp-goal2-loop-spec#^0|§0]].3).** The citation survives, but with a caveat
  consolidation must carry, because the two episodes are NOT equally independent:
  - [[iteration_findings#^25|§25]]'s "gap is the failure mode" was retracted as a **timestep +
    rigid-contact numerical artifact** ([[iteration_findings#^26|§26]]). Its scope error ran over the
    NUMERICS axis — and that axis is already covered by D3 and by §3 principle 1
    (determinism ≠ convergence). D3 would have caught §25 unaided.
  - Claim 4's scope error ran over the MECHANISM/REGIME axis (fixed-base vs
    floating-base). **No existing detector covers that.** D1–D9 all interrogate
    whether a number is right; both of Claim 4's numbers were right.
  - So the new detector's MARGINAL value over the existing set rests on Claim 4
    alone. §25 shows the pattern generalizes across contexts (which is what the
    promotion rule asks) but does not independently demonstrate a gap in the
    current detector set. Both statements are true and consolidation should record
    both rather than the stronger one alone.
  - Recommendation: promote, but write the detector so its teeth are on the
    non-numerics axes — scope inferred from a structural or regime difference —
    or it will be read as a restatement of D3 and demoted at the next lifecycle
    review for redundancy.
- Observer also adopts the **when-NOT-to-ratchet** timing rule into §6: defer an
  instrument change until the paired comparisons it would disturb have closed.
- Observer accepted the audit in full; promotion text adopted as recommended
  (teeth on the non-numerics axes), and it extracted a §6 generalization: **a new
  detector should be scoped to its MARGINAL coverage, not to its motivating
  pattern.** That rule is the reusable form of this exchange and is worth more
  than the detector it came from.
- **Lead's caution against over-reading the "audit-the-observer" datum** (offered
  because H5 is being scored on it): the trigger here was narrow and specific — a
  citation that was LOAD-BEARING for a promotion decision. That is a cheap, well-
  posed check with an obvious falsifier (read the cited section). It is not
  evidence that verification generalizes to claims that are diffuse, expensive to
  check, or where the lead has no independent access to the source. Recorded so
  consolidation does not generalize one easy case into a claimed property of the
  loop — which would be the very error ("correct observation, unearned scope")
  this run just spent two gates establishing.

**2026-08-31 — M-A REVIEWER VERDICT: REVISE. Second gate catch, different faculty.**
- **Caught by: REVIEWER. Detectors: Provenance ratchet (primary), D8
  (frame-coverage), D1 (claim↔frame).** The perceptual role caught what the
  grounded role did not — which is the §0.1 panel-heterogeneity argument paying
  out. The verifier confirmed the PHYSICS; nobody had checked whether the cited
  NUMBERS belonged to the runs they were attached to.
- **Finding 1 (provenance — a figure that travelled between runs).** The PASS
  run's claimed phase trace `hold nf=3 → lift nf=4` is contradicted by its own
  committed jsonl. **Lead verified this independently against the primary
  artifact** (601 rows): hold begins at t=3.400 with `fingers=4`; the finger
  histogram is `{4: 191, 0: 108, 3: 2, None: 300}`; nf=3 occurs at exactly two
  transient ticks (t=3.942 hold, t=4.542 lift), neither at a phase boundary. The
  real trace is **hold nf=4 → lift nf=4**.
  - Where it came from: `hold nf=3 → lift nf=4` is verbatim the HISTORICAL
    baseline's trace in `logs/reg_elbow_catch.txt` (t=0.900 hold nf=3;
    t=1.904 lift nf=4) — a different run, with different phase timings (hold at
    0.900 vs 3.400). The figure was carried across runs and re-attached to a run
    nobody re-derived it from.
  - **The lead propagated it.** It entered via the verifier's summary, I repeated
    it in my run-log entries and then asserted it as claim C2 in the reviewer's
    own brief. Logged against the lead, not the worker or the verifier: routing a
    number without re-deriving it from the artifact is the identical failure the
    provenance ratchet exists to catch, committed by the role that is supposed to
    enforce it. The reviewer caught it anyway — which is the argument for gates
    that read primary artifacts rather than the lead's summary of them.
- **Finding 2 (D8 — the FAIL run has NO log artifact at all).** Its `0.67cm` and
  `hold nf=3 → lift nf=0` have zero corroborating committed evidence. The video
  shows only the GROSS event (ball detaches ~frames 120–122, rests on the floor by
  151) — real, but it evidences "ball lost after capture," not the finger-count
  mechanism claimed.
- **Finding 3 (D8 — neither dynamic video can resolve the quantity in dispute).**
  Both are a single fixed distant camera; drone+cup+ball render as a ~20–30px
  cluster. Individual fingers are not resolvable, so 3-vs-4 finger contact and
  "secure cage vs resting/grazing" cannot be judged from ANY dynamic frame in
  either video. Every finger-state finding rests on the jsonl (PASS only) or on
  inference. The reviewer refused to approve on faith and demanded specific
  renders — correct D8 behavior, and note this is the detector nudge #4 exposed as
  incomplete now working as intended once artifacts existed to test it against.
- **Finding 4 (render hygiene).** Ball colour `rgba=[1.0,0.3,0.3,1]` is nearly
  identical to the MarkerSet `target` marker `[1.0,0.2,0.2,0.8]`
  (`src/sim_setup.py:68`); at this resolution both are indistinguishable red
  blobs. The reviewer could only identify the ball because one blob fell under
  gravity. Cheap fix, real legibility cost.
- **C3 supported at available resolution** (pre-capture frames visually
  indistinguishable between runs — consistent with a marginal difference, though
  "marginal" at the finger level stays unverified). **C4 well supported** — the
  three static renders show a symmetric 4-finger wrap, equator contact, distal
  segments crossing under. Best-evidenced claim in the set.
- **Key enabling insight for the fix:** the reviewer's demands are all
  SATISFIABLE, and satisfying them exercises the verifier's mechanism directly.
  The FAIL run can be logged — the perturbing element is specifically
  `getLinkState(computeForwardKinematics=1)` during settle, NOT logging as such.
  An FK-free logger (plain pos/vel reads, or FK reads confined outside settle) is
  inert and will produce a faithful FAIL-run log. Video is inert, so close-range
  and multi-angle cameras are free. The corrected causal story is what makes the
  missing evidence obtainable — which is the strongest practical vindication of
  refusing the worker's original "instrumentation perturbs everything" framing.
- **Lead's audit of the observer's "three-hop contamination" claim: the claim is
  WRONG, and its correction over-retracted a correct fact.** Checked against both
  primary sources rather than accepted.
  - The committed baseline log (worktree
    `docs/cage_frames/iter2/logs/reg_elbow_catch.txt`) genuinely reads
    `t=0.900 -> hold ... nf=3` and `t=1.904 -> lift ... nf=4`. So
    "baseline hold nf=3 → lift nf=4" is **TRUE** and properly attributed.
  - My nudge-#4 message to the observer said exactly that — "committed baseline
    goes hold nf=3 → lift nf=4; the failing run goes hold nf=3 → lift nf=0" —
    and at that time the verifier's PASS run did not yet exist. Both halves were
    correctly attributed to their own runs. The observer's notes (lines 76–77)
    recorded it correctly.
  - The chimera was created LATER and elsewhere: the **VERIFIER's** first report
    attached the baseline's trace to the PASS run, and I repeated it. Origin is
    the verifier, not the worker; propagation path is **verifier → lead →
    reviewer brief. TWO hops, not three.** The observer was never contaminated.
  - The observer has nonetheless struck its lines 76–77 through as "a cross-run
    chimera." That supersede **retracts a correct, committed-log-backed fact**.
    Left standing, consolidation would later read the baseline trace as unknown or
    discredited when it is solidly evidenced.
  - **This is the mirror image of the original error, and the same class.** The
    original attached a right number to the wrong run; the over-correction
    detaches a right number from its right run. Both are REFERENT errors, and the
    second is the more insidious because retractions are rarely re-audited —
    nothing in the loop currently checks a correction the way it checks a claim.
  - Consequence for the tally: "all three agent layers each caught once, zero
    human nudges" is not supported. Worker caught by verifier ✓; lead caught by
    reviewer ✓; **observer caught by lead — but on the over-correction, not on
    propagating the chimera.** Still a genuine cross-layer catch, just not the one
    claimed.
  - **RATCHET CANDIDATE (universal layer): a retraction requires the same
    evidentiary standard as the claim it retracts.** Motivated by exactly one
    episode so far, so NOT promotable under the §6 ≥2-contexts rule — recorded as
    a watch item, per the marginal-coverage rule the observer itself just adopted.
- Observer accepted the correction — and re-verified against
  `reg_elbow_catch.txt` itself before accepting, rather than taking the lead's
  word. Correct handling: a correction-of-a-correction is exactly where deference
  is cheapest and most dangerous. Notes amended (baseline fact restored with a
  full correction-history block, both referent errors preserved rather than
  silently erased; path recorded as two hops with origin at the verifier; tally
  amended; retraction-standard logged as a WATCH ITEM, not promoted).
- **Open problem named for consolidation** (observer's framing): what does
  artifact-grounding mean for a claim with no artifact — e.g. "the ratchet should
  compile to three layers"? Most of the meta-analysis's own assertions are of this
  kind, and both cross-layer catches this run were the EASY case (cheap, well-posed
  checks against a committed file).
  - Lead's proposed starting answer, for consolidation to accept or reject: the
    analogue of artifact-grounding for an artifact-less claim is **D6 applied one
    layer up** — the claim must name what would count as evidence for it and where
    that evidence would come from, or else be labelled a DESIGN PREFERENCE rather
    than a FINDING. This run supplies a worked example of the distinction: "gates
    should read primary artifacts" started as a design preference and became a
    finding only when the chimera gave it a falsifier and a case. The loop spec
    currently marks no claim as either, which is why preferences and findings sit
    at equal weight in it.
- **Lead's audit of the observer's "literature-inherited finding status" proposal.**
  Cited episodes VERIFIED in `research/10-generic-vs-specialized-loops.md` and
  accurately characterized (ADAS arXiv:2408.08435 + its overfitting critiques
  2602.22480/2601.12307; GEPA/Decagon "more data → over-fitted prompts";
  Voyager arXiv:2305.16291 executable-skill transfer; METR task-agnostic 51% vs
  task-specific 5%). Three objections nonetheless:
  1. **The digest itself refuses the inheritance.** Line 98: "Direct literature on
     'gate-set transfer across tasks' as a framed research question: appears not
     to exist as such; the closest proxies are ADAS pattern transfer, METR's
     taxonomy, and Voyager skill transfer — **the synthesis above is inference
     from those, not a citation**." So "the ratchet compiles to three layers" is a
     SYNTHESIS ACROSS adjacent episodes, not an episode-grounded claim. The
     episodes ground their own claims (pattern transfer, prompt overfitting,
     skill transfer, failure taxonomy); the three-layer compilation is our
     inference. Under the observer's own scheme that is the ANALOGY tier.
  2. **It duplicates machinery the spec already has.** [[grasp-goal2-loop-spec#^0|§0]].3 provenance tags
     are already literature-backed / analogy / guess with citation required.
     Adding a parallel finding/preference scheme with literature-inherited status
     re-implements it at a different granularity — and by the observer's own
     marginal-coverage rule (adopted two exchanges ago), a new element must be
     scoped to what it covers BEYOND the existing set. Unify with §0.3's tags;
     don't add a second axis.
  3. **It inverts an existing safeguard.** [[grasp-goal2-loop-spec#^0|§0]].3 asymmetric authority: "a
     violated expectation raises scrutiny; a confirmed expectation lowers
     nothing," and prior-robustness: "if a verdict would change with the prior
     removed, it is not earned yet." Literature-inherited *provisional finding
     status* is precisely a prior lowering the evidence bar — the mechanism
     behind the "gaps too large" spurious-confirmation episode this loop was
     designed against.
  - Lead's amendment: literature episodes license **attention and priority**, not
    status. A design claim with only foreign episodes stays a PREFERENCE with a
    literature-backed prior — promoted only by a local episode that could have
    refuted it. The genuinely useful half of the observer's proposal survives
    intact: the class with NEITHER local nor foreign episodes is preference full
    stop, and is the cheapest thing to reverse.
- **H7 (direction-of-error asymmetry) logged — with a SELECTION-EFFECT caveat the
  lead is raising against its own observation.** The observer records three
  consecutive observer errors, all framework-flattering, none the other way, and
  proposes tracking error direction at consolidation.
  - The caveat: the sample is generated by MY audit selection, not by the
    observer's error generation. I audit a claim when it is (a) load-bearing for a
    decision and (b) cheaply checkable against a committed artifact. A
    framework-FLATTERING error ("this is better grounded than it is") is exactly
    the kind that overstates a citation — and an overstated citation has a
    committed source to check it against, so it trips both my triggers. A
    framework-UNFLATTERING error ("this is weaker than it is") typically has no
    artifact to check and no decision riding on it, so I would rarely audit it and
    would probably not notice if I did.
  - Therefore "zero unflattering errors caught" is close to what the audit process
    would produce EVEN IF the observer's errors were direction-neutral. H7 is not
    yet distinguishable from an artifact of the detector's own bias. To make it
    scoreable, someone must deliberately sample observer claims that are modest or
    self-deprecating and check those too — otherwise the asymmetry measures me,
    not the observer.
  - Recorded because this is the same failure the run has now hit three times in
    different clothes: a real pattern, and a scope for it that nothing tested.
    Noting it against a hypothesis that flatters MY role (designated auditor) is
    the point — the bias runs in the convenient direction here.
- Lead capping meta-exchange until the worker's resubmission lands; the M-A gate,
  not the observation study, is the critical path.

**2026-08-31 — worker M-A REVISION v2 (worktree HEAD 4c5bbda). All four reviewer
demands met. Lead re-derived the key numbers from the committed logs before use.**
- Worker ran the provenance check on MY correction before adopting it (601 rows,
  Counter{None:300, 4:191, 0:108, 3:2}, nf==3 only at t=3.94167/4.54167) — the
  ratchet propagating downward after the lead broke it upward.
- Fix 1: FK-free logger (`getBasePositionAndOrientation`/`getBaseVelocity` only,
  no `ee_state()`/`joint_states()`) **confirmed INERT** — bit-identical to the
  uninstrumented baseline (cup=[0.946,0.001,1.554], min_cup_d 0.67cm,
  caught=False held=False). The FAIL run has committed corroborating evidence for
  the first time. This is the corrected causal story cashing out exactly as
  predicted: the mechanism said an FK-free logger would be inert, and it is.
- Fix 4: ball recoloured [1.0,0.3,0.3] → [0.15,0.85,0.25], now unambiguous.
- Fix 2/3: close-range side+front video, both runs, continuous through hold→lift.
  Worker's method note is itself a caught error worth recording: its FIRST attempt
  reimplemented the physics/IK loop, silently diverged, and produced a FALSE
  NEGATIVE (neither run captured). It caught this before using it and switched to
  monkeypatching the real verified `run()`, caching values already being computed
  (zero new pybullet calls — necessary, since new FK calls would perturb). Both
  trajectories then reproduced exactly. **Self-caught, pre-report** — the failure
  mode is "the instrument diverged from the system it was measuring," which is
  §0.2's argument for checks-in-code stated from the other side.
- Extra: 386 per-tick FAIL frames, Sim.t 3.35–5.05 at 240 Hz.

- **MAJOR FINDING — the failure is NOT "loss during lift." Lead verified against
  both committed jsonls, tick-aligned:**

  | t (Sim.t) | FAIL nf | PASS nf |
  |---|---|---|
  | 3.4000 (hold begins) | **3** | **4** |
  | 3.9000–3.9250 | 4 | 4 |
  | 3.9333 | **2** | 4 |
  | 3.9417 | **0** (permanent — 127 rows, never recovers) | **3** |
  | 3.9500 | 0 | **4** (recovered) |
  | ~4.40 (lift begins) | 0 | 4 |

  - Separation occurs at t=3.9417, **during static HOLD, ~0.47 s BEFORE the lift
    maneuver begins**. The cage was already insufficient at rest. Every prior
    description in this log — mine included — said "lost during the lift." Wrong.
  - **Both runs encounter the same destabilizing event in the same ~8 ms window**
    (t=3.9333–3.9417). The PASS run dips 4→3 and recovers to 4 one tick later; the
    FAIL run goes 4→2→0 and never recovers. **That two-tick window is the
    knife-edge locus** — localized far more precisely than "the solver is chaotic."
  - The FAIL run entered hold at nf=3 vs PASS's nf=4, i.e. it was already one
    contact worse ~0.5 s before the event. So `nf` at hold-entry has predictive
    content the boolean gate discards entirely — direct, local, physical
    justification for the queued margin/hold-quality ratchet, which until now
    rested on an analogy to the cage-harness lesson.
  - Caveat the lead is attaching: `nf` is a coarse proxy. Identical nf counts
    across the two runs through t=3.925 do NOT mean identical contact state; the
    runs had already diverged. Do not read the table as "the runs were identical
    until 3.933."
- Clock-convention discrepancy resolved by the worker and worth keeping: `Sim.t`
  (all jsonl/frame timestamps) runs from world creation and includes `SETTLE_S=2.5`;
  `run()`'s verbose print zeroes at ball spawn. 0.896 + 2.5 = 3.396 ≈ 3.400. Same
  event, two clocks. Future frame/log comparisons must state which clock.
- Routing: FRESH reviewer spawned on the v2 artifacts (fresh context per gate,
  §1). The corrected hold-vs-lift claim goes to it as a claim to CHECK, not as a
  settled conclusion.

**2026-08-31 — M-A REVIEWER VERDICT (v2): APPROVED. No blocking renders missing.**
- Method note worth keeping: no system ffmpeg on this machine; reviewer used the
  bundled binary from `imageio_ffmpeg`. It also reconciled the video/sim time base
  itself (sim_t = 3.4 + video_t/10, confirmed by content-matching at multiple
  offsets) rather than assuming one — the clock-convention hazard the worker
  flagged, handled correctly one layer down.
- C1 (separation during hold, ~0.47 s before lift) **supported** — log timing, the
  FAIL per-tick PNG dump, and the FAIL close video all agree once the time base is
  reconciled. C5 (colour fix) and C6 (static cage) supported. Second-angle and
  close-range fixes hold up on inspection.
- **Three corrections the reviewer made to claims I had endorsed:**
  1. **"Static hold" is wrong as framing.** `drone0.vel` during hold runs
     0.5–1.0 m/s in BOTH runs — it is a position-hold controller still settling,
     not a motionless body. And **the PASS run is moving FASTER at the critical
     instant** (speed 1.03 vs FAIL's 0.55) and still holds. That kills the naive
     "body motion shook the ball loose" story before anyone proposed it. C1
     survives (separation still precedes the lift transition); the "at rest"
     wording does not.
  2. **The two events are NOT simultaneous.** FAIL destabilizes first (4→2 at
     t=3.9333); PASS dips one tick LATER (4→3 at t=3.9417). My "same ~8 ms window"
     phrasing implies coincidence the data doesn't support — FAIL leads by a tick.
     Correcting my own log entry rather than leaving it to be re-derived.
  3. **C4 is supported only for the SUSTAINED divergence.** PASS's claimed
     4→3→4 dip is a single 8.3 ms tick against 24 fps (41.7 ms/frame) video, and
     no per-tick PNG dump exists for PASS. That transient is log-verifiable only,
     NOT visually verifiable. The reviewer approved the claim it could see and
     explicitly declined to approve the one it couldn't — correct D8 behavior at
     the level of a sub-claim.
  - C3 (FAIL entered hold at nf=3) is **log-only**: the hold-start frame is
    occluded by marker spheres in both close videos.
- **MECHANISM, seen rather than inferred from counts — and it reframes the failure
  a second time.** From t≈3.90 to t≈3.94 the FAIL cage relaxes from a tight claw
  curled over the ball's top hemisphere into a flat, wide "X"/star splay. **No
  finger strike, no squeeze-through a gap, no rollover escape.** The fingers simply
  open; the ball is then contacted by nothing and falls smoothly under gravity (no
  impulsive kick in the log). The reviewer reads this as a **static holding-force /
  back-drive failure — fingers yielding under the ball's weight — not a dynamic
  ejection event.**
- **This puts the worker's revised Claim 3 in tension and the lead is flagging it
  rather than letting the approval bury it.** The worker concluded the failure is
  "NOT fixable by simple re-tuning." A back-drive/holding-torque marginality is
  exactly a tunable-config diagnosis. §3 principle 8 requires a negative to be
  diagnosed as tunable-config vs sim-fundamental, and these two readings disagree.
  - Status: the back-drive account is the REVIEWER'S PERCEPTUAL INFERENCE ("reads
    as"), not a verified causal claim. Under D5 it needs an ablation. Tagged
    UNVERIFIED.
  - Cheapest decisive test, named now so it isn't lost: raise the finger holding
    torque / close command and re-run the FAIL trajectory uninstrumented. If it
    holds, the marginality is tunable config and the "chaotic knife-edge" framing
    is incomplete — the knife-edge would sit IN a marginal holding torque, which is
    diagnosable and fixable rather than fundamental.
  - Does NOT block M-B: the elbow gate is already demoted to informational, and
    M-B runs on the static harness the verifier proved immune. Routed to the CRITIC
    for close-out rather than expanded into M-A's scope.
- Non-blocking strengtheners the reviewer named: a per-tick PNG dump for PASS
  around t=3.90–4.00; an unoccluded hold-start frame for C3.
- No pre-registration diff is due at this gate — the committed prereg covers M-B,
  not M-A. The §0.3 predicted-vs-observed step happens at M-B close.

**2026-08-31 — M-A CRITIC VERDICT: DO NOT CLOSE. Third gate catch, third faculty.**
- **Caught by: CRITIC. Detectors: D4 (completeness), D6 (falsifiability).** The
  enumerative role caught what the grounded and perceptual roles both missed. All
  three gates have now caught something none of the others would have — the §0.1
  panel-heterogeneity argument has now paid out three times for three different
  reasons, which is a stronger result than any single catch.
- **Lead verified the critic's load-bearing CODE claims before acting on them:**
  - `tests/cage_harness.py:138` hardcodes `numSolverIterations=150`. CONFIRMED.
  - `converge_cell()` varies substep, contact scale, and seed — **never solver
    iterations.** CONFIRMED. So F5's "static harness is sound" rests on a
    convergence battery that never touched the ONE axis that produced
    non-monotonic scatter on the dynamic gate. This is the gap that actually
    gates M-B.
  - `arm_catch_solo.py` calls `gripper_world_position/velocity` per tick →
    `drone.ee_state()` → `p.getLinkState(...)` (`src/drone.py:190`). CONFIRMED —
    gate A makes exactly the class of call F4 identified, and was never swept.
- **Lead's own finding, surfaced while verifying the critic and NOT stated by it:
  the two regression gates do not run on the same numerics footing at all.**
  `elbow_catch_solo.py:69` sets `numSolverIterations=150`; `arm_catch_solo.py`
  sets it nowhere, and neither does `world.py` or anything in `src/` — so gate A
  runs at the PyBullet **default (50)** while gate B runs at 150. Every
  "gate A passes / gate B fails" comparison in this milestone has been comparing
  runs at different solver settings. Nobody noticed, including me, across a
  verifier pass and two reviewer passes.
- **Critic's sharpest argument (§4, the unexamined assumption) — accepted.** F4
  fixes HOW WE LOOK; F3 already established that WHAT WE'D SEE is unstable
  regardless of how we look (physically meaningless 1e-4 velocity nudges flip the
  verdict with zero instrumentation). The implicit bridge "we built a clean logger
  → the numbers are now trustworthy" is invalid. F8's demotion of the boolean
  gates is correct but justified by F3, not F4 — and the run log had been citing
  F4 for it. Corrected here.
- Critic also correctly notes F8 is **under-scoped**: "single-run boolean gates
  aren't trustable" was written as an elbow-test conclusion while F1's gate is
  also a boolean and was never attacked. F1 was implicitly carved out as safe on
  no evidence — "matches historical baseline" is evidence nobody tried to break
  it, not evidence of stability.
- **Ruling: M-A does NOT close.** Three tasks assigned (below). None meets a §4
  escalation trigger, so this proceeds without human input; all three reuse
  existing machinery and are short.
- Relabel accepted: F5 is restated as "the static harness is immune to
  FK-injection and stable across substep/contact/seed; solver-iteration
  sensitivity — the mechanism that actually broke F2 — is untested here."
  The phrase "measurement foundation is sound" is withdrawn until task 2 returns.
- Consolidation queue updated per observer: (1) the scope detector now has TWO
  local episodes (Claim 4's regime-inference; the solver-axis omission, where
  "convergence-checked" carried scope over an axis never swept) and is
  ready-to-promote without foreign-episode assist. Worth recording that the two
  episodes were caught by DIFFERENT roles via different faculties — verifier by
  ablation, critic by enumeration — which is better evidence of generality than
  two catches by the same role. (2) The justification-audit shape ("right claim,
  wrong evidence wired to it") stays a WATCH ITEM at one episode, correctly
  distinguished from scope (claim wider than evidence). (3) New executable ratchet
  candidate from the cross-solver finding: **paired gates must share declared
  numerics, or the comparison must state the difference.**
- **Consolidation headline agreed (all parties):** the run's recurring error is
  *correct findings with untested scope* — produced by every layer (worker, lead,
  observer, and the detector set itself), and caught every time by a party OTHER
  THAN ITS AUTHOR. No layer caught its own instance. That asymmetry, not the
  catch count, is the argument for the scope detector living in the universal
  layer: self-audit did not produce a single one of these catches.
- Observer downgraded H4 to strongly-supported / one milestone / redundancy
  untested, logging it as its own fourth scope error (committed while summarizing
  everyone else's). Lead going quiet pending the worker's three tasks.

**2026-08-31 — worker M-A tasks 1–3 landed (worktree HEAD 92dc9c8). Lead
re-derived all three from the committed logs.**
- Worker independently verified the solver-mismatch claim by grep before using it.
- **Task 1 — gate A attacked as gate B was: 108/108 held, 108/108 caught.**
  3 cells (2.5/−2.0, 3.3/−3.2, 5.5/−4.5) × iters {default(50),50,150,175,190,
  200,210,225,250} × vx-nudge {0, 1e-6, 1e-4, 1e-3}. Zero flips anywhere. peak
  force 8.35–11.31 N. **Gate A's 12/12 is genuinely clean, not merely unattacked**
  — the critic's top-ranked concern was well-posed and came back negative, which
  is a real result, not a null one. Constraint-based soft-catch is robust exactly
  where the geometric cage is knife-edged.
- **Task 2 — the axis that gates M-B: no scatter.** §29 cell (prb, n=4,
  off=2.5cm, finger) at iters {50,100,150,200,300} → escape-margin **10.00 g at
  every setting**; pull-in 2.2297–2.2530 cm (spread 0.023 cm); score 1.00, CF 4,
  SY 0.600 throughout. Second independent confirmation of Claim 4, now covering
  BOTH the FK-during-settle axis and the solver-iteration axis. **"Measurement
  foundation is sound" is restored** — and it is no longer an inference from a
  different test, it is a direct measurement on the harness M-B will use.
- **Task 3 — the named falsifier RAN AND DID NOT FIRE.** I had stated: "if applied
  torque never approaches the cap during the splay, the back-drive story is wrong."
  It approaches and pins — `frac_of_cap` = 1.0 at t=3.900, 3.904, 3.908, 3.9125,
  3.9167, 3.925, 3.9333, dipping to 0.74–0.89 between. So the back-drive reading
  survives its own cheapest disconfirmation. Recording the prediction and its
  outcome because a falsifier that runs and fails to fire is worth more than one
  that was never run.
- **Lead's reading of the per-finger data, which the worker's summary did not
  draw out** — and which is richer than "saturated": the proximal torques go
  NEGATIVE on individual fingers, alternating tick to tick (t=3.9125 finger 0 at
  −0.384; t=3.925 fingers 1,2 at −0.304/−0.344; t=3.9333 fingers 1,2 negative;
  t=3.9417 fingers 1,2 at −0.367/−0.349 while 0,3 stay positive). Sign-flipping
  between adjacent ticks across different fingers is **chatter at the saturation
  limit**, not a smooth yield.
  - **Caveat, and it is load-bearing — this is NOT yet evidence of back-drive.**
    With 4 radially-arranged fingers, opposing fingers may have mirrored joint
    axes, in which case a negative value is a normal closing torque for that
    finger and means nothing. The sign convention in
    `assets/make_gripper_urdf.py` must be checked before any negative is read as
    "driven backward." Logged as an observation requiring verification, not a
    finding. (Flagging my own inference at the moment of making it, given this
    run's recurring failure mode.)
- Worker's own not-tested caveat, correctly volunteered: `max_abs_applied` is the
  max across all 12 joints and was NOT verified to be the joint actually in
  contact with the ball — a different finger straining against its own position
  target would produce the same number. The scope discipline propagating to the
  worker unprompted.
- Critic's remaining item (d) — F4 exhaustiveness, i.e. whether OTHER triggers
  besides FK-forcing also flip the dynamic outcome — remains untested and goes to
  the not-tested list rather than blocking close.
- Routing: narrow re-gate to a fresh critic — bounded to "are your three named
  concerns discharged, and does anything BLOCK close" — to avoid an open-ended
  fourth round.

**2026-08-31 — M-A CRITIC RE-GATE: B1/B3 discharged, B2 numbers accepted, but
CLOSE BLOCKED on a reproducibility gap. Fourth gate catch.**
- **Caught by: CRITIC (re-gate). Detector: Provenance ratchet, extended.** Not a
  physics objection — every number checks out. The objection is that two of the
  three sweeps cannot be REGENERATED from committed code.
- Lead verified the code claims: `ablation_scripts/elbow_ablate.py:63` takes a
  real `solver_iters=` parameter wired to `setPhysicsEngineParameter` (line 75),
  so B1's 108-run sweep is rerunnable from the repo. But
  `ablation_scripts/cage_harness_ablate.py:139` hardcodes
  `numSolverIterations=150` with **no flag, no env var, no parameter path**, and
  `git grep` finds **no committed script** producing `appliedJointMotorTorque` or
  `frac_of_cap` at all. CONFIRMED on both counts.
- So B2 (the sweep that gates M-B) and B3 (the falsifier test) rest on
  trust-in-the-narrative for a presumably hand-edited, since-reverted local
  change — in a directory named `ablation_scripts`, which implies the opposite.
  B1 set the bar; B2/B3 don't meet it.
- **This is the provenance ratchet generalizing, and it is worth promoting: a
  number must trace to committed CODE, not merely to a committed LOG.** The
  existing ratchet ("every quantitative figure traces to a committed log and
  reconciles with the others") is satisfied by all three sweeps — and is
  insufficient, because a log records what happened, not how to make it happen
  again. Two local episodes now (this, and the earlier chimera which a committed
  log DID catch), so under §6's ≥2-contexts rule it is promotable — but the
  marginal coverage is specifically the regeneration axis, per the scoping rule.
- Ruling: B2/B3 fixed by committing the parameterized generators, not by
  downgrading the claims. The critic offered the downgrade as an acceptable
  alternative; the lead declines it — M-B runs on the B2 sweep's subject, and
  "reported, not independently reproducible" is a poor foundation to hand the
  next milestone when the fix costs one commit.
- Critic's answer to "what did this milestone get right": naming a falsifier
  BEFORE running it and reporting that it did not fire, rather than reframing the
  metric afterward. Recorded as a practice to keep — it is the §0.3 pre-
  registration discipline applied at the granularity of a single experiment.
- Not-tested list at close (critic-ranked, tight): (1) F4 exhaustiveness — other
  triggers besides FK-forcing; (2) `max_abs_applied` not confirmed to be the
  ball-contacting joint; (3) per-finger torque sign flips uninterpreted, URDF
  joint-axis convention in `make_gripper_urdf.py` unchecked.

**2026-08-31 — M-A CLOSED. M-B released.**
- Lead verified the fix rather than accepting the report: worktree HEAD c3ee083,
  `git status` clean. `cage_harness_ablate.py:60` now has a `SOLVER_ITERS` module
  global threaded to line 143 (mirrors the existing `FK_ABLATE` pattern);
  `cage_solver_driver.py` and `elbow_torque_driver.py` are committed with real
  `--solver-iters` / `--t0/--t1/--trace-out` flags; `git grep` now finds the
  torque instrumentation in tracked code. **Both sweeps regenerated from committed
  code with ZERO drift** — static 5/5 points identical, torque log 37/37 rows
  identical, and the torque run still bit-identical to the uninstrumented FAIL
  baseline (inertness confirmed a third time).
- Worker verified MY claims by grep before acting on them, for the third time this
  milestone. That habit is now stable behavior, not a one-off.
- Notable design choice by the worker, unprompted and correct: it routed torque
  logging into the per-tick `trace` list rather than through the
  `extra_payload`/Logger path, **decoupling it from `runs_dir`/Logger entirely so
  it can never depend on whether the FK-sensitive default logger is active.** That
  is the F4 mechanism being designed around rather than merely avoided.

**M-A final state (the milestone's question was: can numbers on this env be
trusted for the study that follows?):**
- **Gate A (`arm_catch_solo --grid`): TRUSTWORTHY.** 12/12, and 108/108 under
  attack across 3 cells × 9 solver settings × 4 velocity nudges. Robust.
- **Gate B (`elbow_catch_solo`): DEMOTED TO INFORMATIONAL.** Marginal on both
  platforms, not a platform regression. Justified by the velocity-nudge
  instability (F3), which holds with zero instrumentation — NOT by the
  instrumentation fix (F4), which only fixed how we observe.
- **Static harness (`cage_harness.py`) — what M-B runs on: TRUSTWORTHY**, now on
  two independent axes measured directly on it (FK-injection immunity; solver
  iterations 50→300 with escape-margin pinned at 10.00 g and pull-in spread
  0.023 cm). No longer an inference from a different test.
- Environment shift (WSL/py3.13/pybullet3.2.7 → Windows/py3.11/pybullet3.2.5) is
  **not** implicated in any observed difference. Human decision #3 (don't chase
  3.2.7) confirmed correct.
- Cross-gate numerics mismatch recorded: gate A runs at PyBullet default 50,
  gate B at 150. Shown not to matter for gate A's stability, but every
  A-passes/B-fails comparison in this milestone compared different numerics.
- Failure mechanism, so far as established: separation at Sim.t=3.9417 during
  HOLD, ~0.47 s before lift; cage relaxes from a curled claw to a flat splay with
  no strike, squeeze-through, or rollover; finger torque pinned at its 0.5 N·m cap
  through most of the pre-separation window. Back-drive/yield reading survived its
  named falsifier. NOT a verified causal claim — the torque-bump ablation has not
  been run.
- **Not-tested at close (critic-ranked):** (1) F4 exhaustiveness — whether
  triggers other than FK-forcing flip the dynamic outcome; (2) `max_abs_applied`
  not confirmed to be the ball-contacting joint; (3) per-finger torque sign flips
  uninterpreted, URDF joint-axis convention unchecked.
- **Gate catch tally for M-A: verifier 2, reviewer 1, critic 2, human 1, lead 2
  (one of which was catching my own propagated error, via the reviewer).** All
  four gate roles caught something no other role would have.
- Human nudges consumed: 4 (infrastructure, process, scope/economy,
  evidence-standards). Zero escalations were needed for any gate verdict.

**2026-08-31 — M-B released; H3 instrumentation added BEFORE results exist.**
- Observer's request: at the M-B predicted-vs-observed diff, report not just which
  of the 5 pre-registered predictions held, but **whether any VIOLATED prediction
  actually triggered investigation before the result was accepted** — the
  difference between pre-registration having teeth and being ritual ([[grasp-goal2-loop-spec#^0|§0]].3:
  "a result that violates the pre-registered expectation is an anomaly to
  investigate before it can be reported either way").
- **Problem with measuring this after the fact, which the lead is fixing now
  rather than discovering at diff time:** I score blind and diff afterward, so I
  see only the worker's finished report. If the worker investigates a violation
  and says so, I can score it. If the worker quietly reconciles a violation —
  adjusts an interpretation, reframes a metric, decides the prediction "basically
  held" — the reconciliation is invisible and I would score ritual as teeth. The
  ordering has to be RECORDED WHEN IT HAPPENS, not reconstructed at the end.
- Instruction sent to the worker: on first observing a result that violates a
  pre-registered prediction, commit a dated note stating the violation and what it
  intends to do about it, BEFORE running any follow-up or writing any
  reconciliation. The commit timestamp then makes the ordering auditable rather
  than asserted. Cost is one commit; it converts H3 from a self-report into an
  artifact with provenance — which is the same "trace to committed evidence"
  discipline M-A ended on, applied to process rather than to numbers.
- Note the asymmetry deliberately preserved per §0.3: a violated prediction raises
  scrutiny; a CONFIRMED one lowers nothing and still faces the normal gates.

**2026-08-31 — INTERRUPTION: machine restart killed the worker session mid-M-B.**
- State assessment by the lead:
  - Worktree HEAD was c3ee083 (the M-A close point) — all M-A artifacts and
    committed generators intact.
  - **Uncommitted M-B work found on disk**, `src/yale_prb.py` +
    `tests/cage_harness.py`. Both parse clean; the integration looks coherent
    rather than mid-edit (strategies wired into the CLI choice list, flag
    registered). Preserved as WIP commit c2ec47e — explicitly NOT reviewed, NOT
    gated, NOT run by the lead.
  - Work found (worker-authored): `actuate_pulse` (scripted tendon tension
    schedule — close/release/re-close, zero contact reading, an ACTIVE use of the
    passive mechanism) and `actuate_active` (sensor-based close reading contact
    booleans + flexion to bias tension toward blocked fingers). Both wired as
    opt-in strategies; `SOLVER_ITERS` parameterized behind `--solver-iters`;
    `converge_cell` gained the (d) solver-iteration axis. Additive — the passive
    `actuate` baseline and the (a)–(c) convergence axes are untouched, so M-B's
    paired comparisons remain valid.
  - Checked against my own standing instruction "do NOT retool `cage_harness.py`":
    satisfied. The queued items were the margin/hold-quality metric and
    `--fk-ablate`; neither is present. The solver-iteration axis was REQUIRED by
    me (M-B standing requirement 2), and the new strategies are additive rather
    than changes to the measurement instrument.
  - A fresh `grasp-iter-2` session exists but is a NEW session with NO context —
    the M-B brief, the six standing requirements, and the prereg-violation
    logging instruction all died with the old one.
- ~~**Loop-design observation:** every piece of durable state that survived was in
  a COMMITTED artifact; everything that died was session context; the
  committed-evidence discipline doubles as crash recovery; the WIP survived only
  by luck of the filesystem.~~ **RETRACTED SAME DAY — the lead asserted a data
  loss that did not occur.** Corrected by the human: both the lead session and the
  worker session retained their conversation history. Nothing was lost. The
  inference chain was restart → sessions dead → context lost, and BOTH links were
  wrong; the sessions were interrupted, not wiped. Uncommitted files also persist
  across a restart as a matter of course, so the "survived only by luck" claim was
  wrong too.
  - What is actually true, and it is unremarkable: the worker's WORK was
    interrupted mid-M-B. No state was lost. The lead's WIP-preservation commit
    (c2ec47e) was harmless but not necessary, and the four-question context check
    sent to the worker was the right move made for a wrong reason.
  - The candidate ratchet ("a milestone brief belongs in a committed file") is
    WITHDRAWN — it was motivated entirely by the loss that didn't happen. It may
    be independently defensible; it has no episode behind it here.
  - **Recorded rather than deleted, because this is the run's own recurring error
    committed by the lead for the third time and the first time into the primary
    data: a correct-sounding conclusion drawn from a structural signal (a
    "started 3m ago" timestamp) instead of a check that was one message away.**
    The human caught it. Note the sequence: the lead had, minutes earlier, been
    corrected on asserting the worker had "no memory" from the same timestamp, ran
    the cheap check for THAT claim, and still shipped the downstream conclusion
    that depended on it. Fixing an inference without revisiting what was built on
    it is its own failure mode, and it is not one any current detector covers.

**2026-08-31 — M-B resumed after the interruption.**
- Worker instructed to resume immediately and answer the context check in the same
  reply (one round trip, not two): does it still hold the M-B brief, the six
  standing requirements, and the prereg-violation logging instruction, and how far
  had it got before stopping. Told to report what is actually in its context
  rather than reconstruct from the repo — a reconstruction is indistinguishable
  from a memory in a finished reply, so asking for one would forfeit the check.
- Lead's two corrections passed to the worker explicitly: (a) the "your session
  was killed and your context lost" claim was wrong and retracted (b8d4144);
  (b) the WIP commit c2ec47e therefore carries no authority — a save point the
  worker may amend, rewrite, or revert freely, not an approval.
- M-B runs under the six requirements earned in M-A: committed-code provenance;
  solver-iteration axis in convergence; video alongside stills in a non-rotating
  dir; falsifiers named before running; scope stated explicitly; paired
  comparisons sharing declared numerics. `cage_harness.py`'s metric stays frozen
  (margin-metric and `--fk-ablate` ratchets remain queued for close-out) so M-B's
  comparisons stay paired within one instrument.
- Gate on completion: verifier → reviewer, prereg withheld from both; the lead
  runs the predicted-vs-observed diff afterward, reporting per §0.3 whether any
  VIOLATED prediction triggered investigation before the result was accepted.

**2026-08-31 — M-B report received; verifier gate opened.**
- Environment note (the HUMAN'S MACHINE, not the work): background processes were
  being killed mid-run throughout — the worker confirmed with a no-op sleep loop
  that died the same way. It worked around this with a chunked, fsync'd, resumable
  driver (`tests/mb_chunk_driver.py`) rather than reporting partial cells. Flagged
  to the human separately; it is an infrastructure fact, not a result.
- Headline: **mostly null.** Applying the committed `paired_converge` threshold
  (dmin>0.3 positive / dmax<−0.3 negative / else OVERLAPS 0), 9 of 10 combos read
  OVERLAPS 0. The single exception is **n4-finger-5.0cm / prb_active, CONVERGENT
  POSITIVE (dmin=+1.23, dmax=+1.56)**. Same cell with `prb_pulse` is
  positive-throughout (+0.21..+0.71) but under threshold, so null by the letter.
- **Unplanned finding (worker's own):** at n4-finger-5.0cm the PASSIVE `prb`
  baseline scores escape-margin 6.09 g, versus the 10 g ceiling everywhere else —
  the passive mechanism is already marginal at that offset. Both adaptive
  strategies restore it to 10.00 g. That is a MARGIN effect, distinct from the
  pull-in deltas, occurring at exactly the cell where the baseline strains.
- **LEAD'S OWN CONCERN, recorded before the gates score — the dropped cell is the
  informative one.** Scope was reduced 8 cells → 5 (env budget, disclosed). The
  finger-direction series actually run is 1.5 cm, 2.5 cm, [3.5 cm NOT RUN],
  5.0 cm. Null at 1.5 and 2.5; strongly positive at 5.0. **The transition from no
  effect to the study's only effect happens across precisely the gap where the
  unrun cell sits.** The omission was disclosed and honestly motivated, but it is
  not outcome-neutral: 3.5 cm finger is the single most informative cell in the
  design, because it is the only one that could distinguish a threshold (effect
  switches on near the passive baseline's failure point) from a gradient (effect
  grows with offset). The claim's SHAPE, not its numbers, is what this weakens.
- Second lead concern: `mb_chunk_driver.py` REPLICATES `paired_converge`'s
  13-perturbation set by calling `run_cell` directly. M-A already produced an
  episode where a re-implementation of a verified loop silently diverged and
  produced a FALSE NEGATIVE (the worker caught that one itself). A re-implemented
  instrument reporting a mostly-null result is the same shape. This is the
  verifier's top target: faithfulness of the driver, not the physics.
- Worker disclosed a substitution unprompted: paired-delta convergence data in
  place of standalone §2.3 `--converge` tables for the new strategies — same 13
  perturbations, paired rather than single-strategy — and explicitly declined to
  let it pass as equivalent by default. Correct behavior; the substitution is
  still the reviewer's and critic's to rule on.
- Worker reports NO pre-registered-prediction violations, and correctly did not
  restate its predictions. The §0.3 predicted-vs-observed diff is mine to run
  AFTER the gates score blind — including the H3 question of whether any violation
  triggered investigation before acceptance.
- VERIFIER spawned (fresh Sonnet, prereg withheld).

**2026-08-31 — M-B VERIFIER VERDICT: C1 confirmed w/ a real defect, C2/C3 refined
substantially, the missing cell run and closed. Gate catch #5.**
- **C1 driver fidelity — CONFIRMED, with a genuine but consequence-free defect.**
  Direct comparison on the cell the worker reported as a NULL (n4-gap-3.5cm,
  prb_pulse vs prb): committed `paired_converge` reproduces the driver's ledger to
  displayed precision on all 12 per-variation PI pairs (substep=2 harness
  −0.28/−0.27 vs ledger −0.27618/−0.26605; solver_iters=300 harness −0.26/−0.25 vs
  ledger −0.25671/−0.24770), same OVERLAPS-0 verdict, identical across two runs.
  The re-implementation-diverges hazard did NOT materialize.
  - **Defect found:** `mb_chunk_driver.PERTURBATIONS` includes solver_iters=150,
    but `SOLVER_ITERS` already defaults to 150 and `paired_converge`'s own loop
    deliberately skips it (`for it in (50,100,200,300)`). So the committed
    instrument runs **12 distinct** perturbations; the driver runs 12 distinct
    **plus one duplicate** of the baseline — ledger rows idx1 (substep=4) and
    idx10 (solver_iters=150) are byte-identical. The driver's docstring claim of
    replicating "the EXACT 13-perturbation set" is **false**.
  - Consequence: none for any verdict. A duplicate of a value already in the set
    cannot move min() or max(), and the verifier checked that the
    solver_iters=150 row is never the sole min or max in any reported cell. The
    NUMBER of perturbations claimed in the worker's report is nonetheless wrong,
    and every "13-perturbation" statement needs correcting to 12+1.
- **The missing cell was run: n4-finger-3.5cm is NULL** (prb_active Δ across 3
  seeds: −0.04/−0.06/−0.03; baseline EM still 10.00 g, not marginal). The null
  series now runs cleanly 1.5 → 2.5 → 3.5 cm. My concern that the unrun cell was
  the informative one was correct that it was informative — and the answer was
  not the one that would have been most convenient.
- **C3 REFINED, and this is the substantive result: GRADIENT, not threshold, with
  onset BEFORE the baseline fails.** At 4.5 cm the passive baseline's pull-in is
  already declining (3.12 → 2.33) while its escape-margin is still full
  (10.00 g, NOT marginal) — and `prb_active` already shows an above-noise
  +0.69. At 5.0 cm the delta grows to +1.45, exactly where baseline EM crashes to
  6.09 g. So the benefit tracks the baseline's CONTINUOUS pull-in degradation and
  begins before the EM crisis; it is not a step that switches on at failure. The
  worker's C3 framing ("adaptive rescues the mechanism where it fails") is too
  coarse.
- **New upper bound the worker never tested: at 5.5 cm ALL THREE strategies fail
  totally** — EM 0.16 g, PI ≈ −70 cm (full escape), deltas ≈ 0. So the adaptive
  rescue band is NARROW, roughly 4.5–5.0 cm, bounded above by total mechanical
  failure nothing can fix. This also resolves my "is 5.0 cm a special point?"
  worry: it is not an isolated artifact, it sits inside a real but narrow window.
- **Direction control confirms specificity:** n4-gap-5.0cm (same magnitude, gap
  direction) shows near-zero deltas, matching the worker's own gap null. The
  effect is tied to finger-direction offsets, NOT a generic large-offset artifact.
- **C4 (26/26 robustness) UNDETERMINED** — not re-run, out of budget. Nothing
  contradicts it; nothing checked it either.
- **LEAD'S CONCERN ON THE NEW EVIDENCE, recorded before further gating:** the
  4.5 cm and 5.0 cm recheck points were run at a SINGLE seed (seed=None), while
  3.5 cm got three. The worker's original 5.0 cm figure does rest on the full
  perturbation set (dmin +1.23), so that point is solid — but **4.5 cm, which is
  the load-bearing evidence for "onset precedes EM failure," is single-seed.** And
  `prb_pulse` is non-monotonic across the band (+1.20 at 4.5 cm vs +0.32 at
  5.0 cm), so the gradient story is clean for `prb_active` and NOT clean for
  `prb_pulse`. Sent back to the verifier for seeds at 4.5 cm before the gradient
  claim is allowed to stand.
- Reviewer spawned in parallel on the frames/video (independent of the seed
  question).
- **Seed follow-up: the verifier RETRACTED ITS OWN REFINEMENT. Gradient claim
  does not stand.** n4-finger-4.5cm across 4 seed points:
  - `prb_active`: Δ = +0.687 / +0.806 / +0.203 / +0.141 → **dmin +0.141**, below
    the study's own 0.3 cm floor. NOT convergent. The single-seed +0.69 I routed
    on was the high end of a spread reaching into noise. "Onset precedes EM
    failure" is downgraded from a confirmed refinement to a sign-consistent but
    non-convergent hint.
  - EM = 10.00 g for all three strategies at all four points — the baseline is
    confirmed NOT marginal at 4.5 cm (that part was not a single-seed artifact).
  - Verifier's own words: its earlier framing "was wrong to state at single-seed
    confidence." A grounded role retracting its own headline under a check it was
    asked to run is the behavior the role exists for; recording it as such.
- **BUT the same run surfaces a result that reframes the milestone, and neither
  the worker nor the verifier drew it out:** `prb_pulse` at 4.5 cm gives
  **Δ = +1.198 / +1.244 / +1.516 / +1.574 — dmin +1.198**, clearing the 0.3 cm
  threshold with room, and LARGER than `prb_active` at the same cell
  (+0.141..+0.806) and larger than the worker's own 5.0 cm `prb_pulse` range
  (+0.21..+0.71).
  - **`prb_pulse` reads NOTHING.** It is a scripted tension schedule, a function
    of progress alone — no contact booleans, no flexion, no sensing whatsoever.
    `prb_active` is the sensor-based strategy.
  - So on the evidence in hand, the BLIND scripted close matches or beats the
    SENSOR-BASED one across the band, and clearly beats it at 4.5 cm. If that
    survives, the milestone's engineering answer is not "adaptive re-centering
    helps" but "**a scripted release-and-reclose helps, and the sensing buys
    nothing on top of it**" — which is a far more consequential conclusion for
    hardware, since it removes the sensor requirement entirely.
  - **The worker never ran 4.5 cm at all.** Its reported headline (only
    `prb_active` @ 5.0 cm is positive) is an artifact of which cells got run —
    the cheap, sensing-free strategy's best cell was outside the sampled set.
    This is the dropped-cell concern I logged pre-verdict landing harder than I
    expected, and on a different axis than I predicted.
- **Caveat the lead is attaching before anyone runs with this:** 4.5 cm was varied
  across SEEDS ONLY (4 points). Every "CONVERGENT POSITIVE" verdict elsewhere in
  this study rests on the full 12-distinct-perturbation set (substep × contact ×
  seed × solver-iters). Applying the dmin>0.3 rule to a seed-only sample is NOT
  the same test, and calling `prb_pulse` @ 4.5 cm convergent on this evidence
  would be exactly the unearned-scope error this run keeps producing. Status:
  **promising, full battery not run.**
- Dispatched: full `paired_converge` battery at n4-finger-4.5 cm for both
  strategies. One cell, and it decides whether the milestone's conclusion is
  "sensing helps at one offset" or "sensing is unnecessary."

**2026-08-31 — M-B REVIEWER VERDICT: REVISE. Gate catch #6.**
- **Caught by: REVIEWER. Detectors: D8 (frame-coverage) + Provenance.**
- **Finding 1 — a described artifact that was never opened.**
  `mb_frames/cageQ_prb_active_n4_gap_35mm_slowmo.mp4` is **48 bytes** (siblings are
  400–650 KB) and fails to open: "Invalid data found when processing input." The
  worker's report described this cell as "video only (stills cut for time — a
  rendering-budget call, not a data gap)." In fact there is **zero usable visual
  evidence** for n4-gap-3.5cm / prb_active — not reduced coverage, no coverage.
  Its ledger numbers exist and are unverified against any frame.
  - The worker DID spot-check one image before citing it
    (`..._n4_finger_50mm_seated_diag.png`) and said so. It did not check this one,
    and described its status anyway.
  - **This is the run's recurring error in a new costume: asserting a property of
    an artifact without opening it.** Same shape as the lead's "no memory"
    inference and the chimera. Note it is now the FOURTH distinct layer to commit
    it (worker, lead, observer, and here the worker again on a different axis) —
    and again caught by someone else, never by its author.
- **Finding 2 — V2 CONFIRMED, and visibly.** Baseline seated diag: centering-err
  3.04 cm (pull-in 1.96). `prb_active`: centering-err 1.59 cm (pull-in 3.41),
  Δ ≈ +1.45 cm — inside the claimed +1.23..+1.56 band, symmetry 0.67 → 0.81. The
  ball moves from sitting low-left and partly escaping the finger V to centred and
  symmetric between all four fingers. **A real, eyeball-visible effect, not one
  carried by the numbers alone.** `prb_pulse` at the same cell (+0.32) is at or
  below what is distinguishable by eye — consistent with its weak 5.0 cm figure.
- **Finding 3 — V5 (the pulse mechanism) confirmed, but by telemetry not
  geometry.** The burned-in HUD shows two clean rise/fall flex cycles with
  `fingers touching` dropping 4→3 at each trough — a real, repeatable
  release/re-close. Geometrically the widening is subtle; someone judging by eye
  without reading the HUD would miss it. Confirmed-but-weak. Matters because
  `prb_pulse` is the strategy the pending 4.5 cm battery may promote to the
  milestone's headline — its mechanism doing what its docstring claims is now
  established, which is a precondition for that result meaning anything.
- **Finding 4 — V1 null, V3, V4 all corroborated.** 2.5 cm cells visually
  indistinguishable across all three strategies (err 0.25 / 0.30 / 0.32 cm). At
  5.0 cm the passive baseline shows the corroborating asymmetry D2 asks for: flex
  +2.7 / +2.4 / **+1.6** / +2.4 with one finger visibly stalled, symmetry 0.67 vs
  0.81–0.84 for the adaptive strategies, and its disturb frame reads "HELD, ball
  moved 0.2 cm" at 2.5 g — marginal-but-holding, exactly matching EM 6.09 g.
  Under-views show 4 fingers at ~90° spacing: genuine cages, not grazes.
- All HUD figures reconciled against the committed ledgers and
  `iteration_findings.md`; no orphaned or contradictory number.
- Routing: REVISE to the worker for the corrupt render only. The scientific
  content survives the gate — this is an evidence-integrity fix, not a re-do.
- **Worker fix verified BY THE LEAD, decoding rather than inspecting metadata**
  (the whole point of the finding): all 6 mp4s in `mb_frames/` decode cleanly,
  308 frames each, 400–649 KB. The formerly-48-byte
  `cageQ_prb_active_n4_gap_35mm_slowmo.mp4` is now 400,162 bytes / 308 frames.
  Worktree clean at HEAD fe9c253.
- **The worker generalized the fix correctly and unprompted:** it decoded ALL six
  videos, not only the flagged one, on the reasoning that the finding was about
  describing an artifact without opening it — so checking only the one caught
  would have repeated the error on the other five. It also opened the new seated
  still before citing it (centering-err 3.73 cm against 3.5 cm injected — no
  re-centering, consistent with the gap-direction null already reported).
  Responding to the CLASS rather than the instance is the behavior the ratchet is
  supposed to produce, and it happened without being asked.
- Perturbation count corrected in code and in the report: all reported deltas are
  min/max across **12 distinct configurations**, not 13. The list structure was
  deliberately left unchanged so completed ledger indices stay valid — the right
  call, since renumbering would invalidate committed evidence to fix a comment.
- Outstanding before M-B can close: the full 12-perturbation battery at
  n4-finger-4.5 cm (decides whether the sensing-free `prb_pulse` result is
  convergent), then the lead's §0.3 predicted-vs-observed diff against the
  committed prereg, run only after the gates have scored blind.
- **Adjudication (lead) — candidate detector "was the evidence set chosen
  independently of the claim?" (working name: sample-generation bias).**
  Observer proposes two episodes: the lead's H7 audit-selection self-flag (audit
  targets sampled by flattering-AND-cheaply-checkable) and M-B's cell selection
  (cells sampled by the worker's hypothesis and budget).
  - **Same class: YES.** Both are conclusions inheriting bias from how the
    evidence set was GENERATED, and the observer is right that every existing
    detector interrogates the evidence itself, never its generating process. It is
    also genuinely distinct from the scope detector: scope = a claim wider than
    its evidence; this = a claim correctly scoped to evidence that was non-randomly
    chosen. Different failure, different fix.
  - **Promotable: NOT YET, and the reason is the battery.** Episode 1 fired and
    changed a verdict (H7 went to unscoreable). Episode 2's consequence is
    **pending**: if the full battery confirms `prb_pulse` @ 4.5 cm convergent, the
    selection effect materially changed the milestone's headline and the episode
    is strongly refutation-capable. If the battery comes back null, the worker's
    headline stands and episode 2 is "a selection effect that turned out not to
    matter" — the concern was still correct to raise, but it is much weaker
    evidence for a detector. Promoting now would be scoring an episode by the
    concern rather than by its outcome, which is the same premature move the §25
    citation audit caught earlier.
  - One difference worth carrying into the promotion text if it does promote: in
    episode 1 the sampler (lead) and the claimant (observer) were DIFFERENT
    parties; in episode 2 they were the SAME (the worker chose the cells and drew
    the conclusion). Self-sampling is the more dangerous configuration and the
    detector should say so.
- Observer also records, as positive data: the worker's class-level fix (decoding
  all six videos unprompted) as the first observed instance of any layer
  responding to an error CLASS rather than its instance without being told; and
  the verifier's second self-retraction under an asked-for check.

**2026-08-31 — M-B full battery at 4.5 cm: NOT the reversal the lead framed.**
- `prb_pulse` vs `prb`: dmin **+0.49**, dmax +1.57 → **CONVERGENT POSITIVE**.
- `prb_active` vs `prb`: dmin **+0.14**, dmax +1.19 → **OVERLAPS 0** (driven down
  by substep 2, contact ×3, seeds 2/3).
- **Honest shape: the two strategies TRADE OFF across the band.** Blind scripted
  `prb_pulse` is convergently better at 4.5 cm; sensor-based `prb_active` is
  convergently better at 5.0 cm (dmin +1.23 vs pulse's +0.21). **Neither dominates.**
- **LEAD SELF-FLAG — I anchored the gate.** My brief told the verifier that
  "sensing buys nothing" would be "a much stronger and much cheaper conclusion,"
  i.e. I handed a grounded role my preferred answer before it ran. It did not take
  it — it returned the trade-off and explicitly rejected my framing ("not a tie
  resolved in sensing's favor" was MY shape; it reported neither strategy
  dominating). §0.3 forbids anchoring the gates with the PREREG; it does not
  mention the lead anchoring a gate with the lead's own hypothesis, and I did
  exactly that. Recorded as a process defect against me, and as a candidate
  extension: **context isolation must cover the lead's hypotheses, not only the
  pre-registration.**
- Selection-effect episode 2 now RESOLVES as consequential: the headline did
  change (from "only `prb_active` @ 5.0 cm" to "trade-off across the band"). The
  sample-generation-bias detector's second episode is refutation-capable and
  fired — promotable, per the adjudication logged above.

**2026-08-31 — §0.3 PREDICTED-vs-OBSERVED DIFF (run by the lead AFTER all gates
scored blind; prereg opened only at this point).**

| Prediction | Conf | Observed | Verdict |
|---|---|---|---|
| P1 finger n4–n6, 1.5–3.5 cm: active adds ≈nothing | 0.75 | 1.5 cm −0.17..−0.07 / −0.08..−0.01; 2.5 cm −0.15..+0.05 / −0.06..−0.02; 3.5 cm −0.04/−0.06/−0.03. All OVERLAPS 0 | **CONFIRMED** (n4 only — n6 never run) |
| P2 gap direction: neither variant re-centers | 0.6 | gap-3.5 cm −0.02..+0.00 / +0.01..+0.04; gap-5.0 cm −0.06 / +0.01. OVERLAPS 0 | **CONFIRMED** |
| P3 n4-finger-5.0 cm: pulse and/or active convergently improves | 0.5 | active dmin +1.23 CONVERGENT; pulse +0.21..+0.71 OVERLAPS 0 | **CONFIRMED by letter, mechanism WRONG** |
| P4 n8: no re-centering, still cages | 0.8 | n8-2.5 cm −0.02..+0.02 / +0.01..+0.03; 26/26 | **CONFIRMED** (2.5 cm only) |
| P5 no robustness regression | 0.7 | 26/26 all strategies, all 5 cells, no caged→escaped flip | **CONFIRMED** |

- **5 of 5 confirmed. ZERO violations.**
- **THEREFORE H3 IS UNTESTED BY THIS MILESTONE.** The observer's question — did a
  VIOLATED prediction actually trigger investigation before the result was
  accepted — has no answer here, because nothing was violated. The milestone H3
  was supposed to live or die on cannot speak to it. Report that as the finding
  rather than reading five confirmations as evidence the mechanism works.
- **Three structural weaknesses that made confirmation easier, and they matter
  more than the 5/5:**
  1. **P3 is DISJUNCTIVE** — "`prb_pulse` (and/or `prb_active`) convergently
     improves." An or-clause over two strategies roughly doubles its confirmation
     surface. It confirmed on `prb_active`; its stated REASONING was entirely
     about the pulse mechanism ("exactly the case the regrasp literature says a
     release-re-close fixes") — and `prb_pulse` is the strategy that FAILED to
     clear at 5.0 cm. **Right outcome, wrong mechanism, and the disjunction hid
     the mismatch.** This is the §0.3 spurious-confirmation shape, self-inflicted.
  2. **P1 and P4 confirmed on SUBSETS of their stated scope** — P1 claims n4–n6
     and only n4 ran; P4 claims n8 and only 2.5 cm ran. Both are the run's
     recurring unearned-scope error, now committed by the PRE-REGISTRATION itself.
  3. All five confirmed despite average stated confidence ≈0.67 (expected ≈3.4
     of 5). Either the priors were sandbagged or the predictions were too easy to
     satisfy; the disjunction and the scope slack above suggest the latter.
- **THE HEADLINE FINDING, and it is about pre-registration itself:** the
  milestone's most interesting result — `prb_pulse` convergent at **4.5 cm**, the
  strategy/offset where sensing buys nothing — falls **entirely outside the
  pre-registered space.** The prereg named offsets 1.5–3.5 cm (P1) and 5.0 cm
  (P3). It never mentioned 4.5 cm. The worker sampled cells to match, and so the
  gap between the predicted regimes went unrun — which is exactly where the result
  lived.
  - **§0.3 states "the prior directs attention" as a BENEFIT. This run shows
    directing attention has a COST: it made the evidence set non-random in the one
    region no prediction covered.** Pre-registration did not merely fail to
    predict the finding — it actively shaped the sampling that nearly hid it. The
    finding was recovered only because a gate ran a cell the pre-registration had
    no interest in.
  - This is the same sample-generation-bias class adjudicated above, with the
    pre-registration identified as the biasing mechanism. It is the strongest
    result this run has produced about loop design, and it argues for a standing
    countermeasure: **sample at least one cell that no prediction covers.**
- **STANDING PRACTICE ADOPTED from M-C onward (lead's call, on the observer's
  prompt): a gate brief states what to TEST and what would FALSIFY, never what
  the lead expects to be true.** Adopted without waiting for a second episode,
  against the normal one-episode rule, because this failure is structurally
  guaranteed to recur — the lead authors every brief, so the channel is open on
  every gate, every milestone.
  - **Refinement, and it is the part that matters:** the rule bars stating an
    expected OUTCOME, not naming an untested ALTERNATIVE. The M-A verifier brief
    said "Claim 1 is the one I most doubt, because there is a cheaper untested
    explanation — `--runs-dir` may change the code path rather than observe it,"
    and that brief produced the run's single best catch. It named a rival
    hypothesis and assigned the ablation that would separate them; it did not say
    which would win. The M-B brief said "sensing buys nothing would be a much
    stronger and cheaper conclusion" — that states a preferred answer and adds a
    reason to want it. **Name the alternative, assign the discriminating
    experiment, never predict the winner, and never say which result would be
    more convenient.**
  - Sharpest test of the boundary: if a brief's framing would survive being read
    aloud to the gate AFTER it reported, without embarrassment, it is direction;
    if it would look like a thumb on the scale, it is anchoring.
- Observer's confound noted and accepted: "5/5 confirmed at mean confidence 0.67"
  is NOT usable calibration data, because the cells were chosen to match the
  predictions. Confirmations calibrate only on cells sampled independently of the
  predictions being scored. That makes the uncovered-cell countermeasure
  load-bearing twice — it is the precondition for calibration data existing at
  all, not just insurance against a missed finding.

**2026-09-01 — M-B CRITIC VERDICT: DO NOT CLOSE. Gate catch #7. Lead verified all
three checkable code claims before acting.**
- **BLOCKER, and it is the LEAD'S defect, not the worker's.** The milestone's
  headline (F3, the 4.5 cm trade-off) exists **only as prose in this run log**.
  Verified: `docs/cage_frames/iter2/logs/` contains ten `mb_ledger_*` files
  covering 1.5 / 2.5 / gap-3.5 / 5.0 / n8-2.5 cm — and **NOTHING for 4.5 cm**.
  The verifier ran that battery in its scratchpad, reported the numbers to me, and
  I wrote them into the log. No committed artifact exists.
  - This is the exact rule the lead promoted at M-A close — "a number must trace
    to committed CODE, not merely a committed log" (c3ee083) — violated by the
    lead, on the milestone's most important number, one milestone later. F2
    (5.0 cm) has a full ledger and reproduces line-by-line; F3 does not.
  - Note the asymmetry that let it through: the rule was enforced on the WORKER's
    numbers by a gate. Numbers arriving via a GATE and transcribed by the LEAD had
    no such check, because nothing in the loop gates the lead's own artifacts.
- **F4 relabel — CONFIRMED, and the harness already knew.** `A_MAX_ESCAPE = 10.0*G`
  is documented in-code as "cap on the margin search (holds above read '>=cap')",
  and line 1102 prints `>=10.0g` rather than a value when at the cap. So
  "escape-margin 10.00 g" is **censored data**, not a measurement — the true
  margin could be 10 g or 40 g. Every "restores EM to 10.00 g" statement in this
  milestone (mine included, repeatedly) must read **"restores EM to at-or-above
  the 10 g search ceiling."** The qualitative finding (baseline strained at 5.0 cm,
  adaptive not) survives intact; the number does not.
- **OAT vs factorial — a real limit on what "convergent" means here.** The 12
  perturbations vary ONE axis at a time from a single baseline (3+2+3+4). A
  configuration that is simultaneously coarse-timestep AND soft-contact AND
  bad-seed is never sampled. "Convergent across all 12" is convergence along 12
  rays from one point, not across the space. If the joint-worst-case noise floor
  exceeds 0.3 cm, both headline convergences could be within noise.
- **The trade-off attacked, and it lands.** F3's `prb_pulse` clears the threshold
  by only 0.19 cm (dmin +0.49 vs the +0.3 bar), and `prb_active`'s own 4.5 cm
  spread across 4 seeds was +0.687/+0.806/+0.203/+0.141 — a 0.66 cm swing on a
  0.3 cm threshold. So "the strategies trade off" may be **two threshold-straddling
  readings narrated as a crossover**, equally consistent with one noisy underlying
  quantity that both strategies estimate imperfectly and that happens to fall
  either side of the bar at two nearby offsets. Cheapest discriminator: one cell at
  **4.75 cm**, full battery, both strategies — a real crossover predicts a smooth
  monotonic swap in dmin across 4.5 → 4.75 → 5.0; noise predicts an incoherent
  pattern.
- **THE DEEP FINDING (critic's §5), and it may scope the entire milestone.**
  Gravity is OFF for the whole close (`setGravity(0,0,0)`, `setup_physics` line
  143 — verified; gravity is applied only transiently as the disturbance probe).
  Pull-in is therefore purely finger-force-driven, with no weight pre-seating the
  ball. On real hardware a Yale/SDM-class hand's self-adaptation is classically
  demonstrated as compensating for WEIGHT-driven pre-seating. So the adaptive
  advantage may be a **zero-g-only artifact**: `prb_pulse`'s release phase lets the
  ball drift free and be re-grabbed in a better spot precisely because nothing
  pulls it back to a rest position during release. If so, F2/F3 do not describe
  the regime the hand would actually operate in — and F7's visual confirmation
  does not rule it out, having also been captured gravity-off.
- **§4 ESCALATION TO THE HUMAN — physical-realism judgment.** Whether gravity-off
  invalidates the pull-in finding, and whether the static harness should be run
  gravity-on for these two cells, is exactly the faculty the loop spec marks as
  not mechanizable. The gravity-off design was deliberate (§25: determinism).
  Escalating rather than unilaterally changing the testbed regime.

**2026-09-01 — M-B tasks 1–4 landed (worktree f401b7b). Lead re-derived every
number from the committed ledgers. THE MILESTONE'S RESULT HAS CHANGED.**
- **Task 1 — blocker cleared, no drift.** `mb_ledger_P6_n4_finger_4.5cm_*` now
  committed. Lead-verified: pulse dmin **+0.485** / dmax +1.574; active dmin
  **+0.141** / dmax +1.193 — matching my transcription exactly. The worker's
  official `paired_converge` runs were killed twice by the machine, so it
  preserved both partials and cross-checked 10 overlapping perturbations against
  the chunk driver bit-for-bit before relying on it. Correct handling of a flaky
  environment: it did not let the instability become an excuse for an unverified
  number.
- **Task 2 — EM censoring corrected**, by the worker and applied retroactively to
  its own prior claims. Qualitative finding restated precisely: the passive
  baseline was the ONLY strategy not saturating the 10 g search ceiling; both
  adaptive variants DID saturate it. The magnitude of their advantage is unknown
  and unmeasured.
- **Task 3 — the discriminator is ambiguous, and the worker declined to resolve
  it.** dmin across 4.5 → 4.75 → 5.0 cm: `prb_pulse` +0.485 → +0.248 → +0.21
  (smooth monotonic decline); `prb_active` +0.141 → +0.165 → +1.23 (flat, then an
  abrupt step). Neither a clean crossover nor pure noise. Reported as observed,
  interpretation left open — the right call.
- **TASK 4 — BOTH HEADLINE CONVERGENCES BREAK. This is the milestone's real
  result.** Two JOINT corners (substep + contact + seed varied simultaneously,
  which the 12-ray OAT design never samples):
  - corner (substep 2, contact ×3.0, seed 1): both cells robustly positive
    (pulse +0.80, active +1.65) — no surprise.
  - corner (substep 8, contact ×0.33, seed 2): **`prb_pulse` @ 4.5 cm = −0.157
    (SIGN FLIP; every OAT perturbation at this cell was positive, min +0.485).
    `prb_active` @ 5.0 cm = +0.017 (collapse to ~zero; OAT min was +1.23).**
  - Lead-verified from the committed ledgers, and both reproduce exactly in
    separate `*_repro_*` files (−0.157 and +0.017). Not a fluke.
- **Consequence: M-B has NO surviving convergent-positive result on pull-in.**
  Both positives were artifacts of an incomplete sweep. The honest milestone
  finding is now: *adaptive re-centering shows no robustly convergent pull-in
  advantage over the passive close anywhere in the tested envelope, and the
  apparent advantages at 4.5 and 5.0 cm do not survive joint perturbation.* The
  worker reached this conclusion itself and stated it plainly against its own
  prior headline.
- **RETROACTIVE IMPLICATION — the largest thing this run has surfaced.** The
  OAT-only design is not M-B's; it is `converge_cell`/`paired_converge`, the
  §2.3 battery used to validate **every contact-rich result in the iteration-2
  static study, including §28/§29's Goal-1 conclusions.** If a joint corner breaks
  M-B's results, the question of whether it breaks §29's is open and unasked. The
  worker explicitly flagged that it did NOT try the breaking corner at any other
  cell. **This is now the highest-value experiment available and its scope is
  Goal 1, not Goal 2.**
- Also untested (worker's own list): only 2 corners per cell, no systematic
  corner sweep; no mechanism-level account of why substep8 × contact0.33 × seed2
  specifically breaks it.
- **Gate catch attribution: the CRITIC (D4/D6) named the OAT gap; the WORKER
  executed the corner that falsified both headlines.** The critic ran nothing and
  again produced the milestone-deciding catch — second time in two milestones.

**2026-09-01 — RETROACTIVE SCARE RESOLVED: §29 does NOT break under the corner.**
- Worker ran corner (substep 8, contact ×0.33, seed 2) against three cells:
  - **prb, n4, 2.5 cm, finger:** EM 10.00 g (ceiling), CF 4, score 1.00 — all
    unchanged. PI +2.08 vs committed +2.24–2.26 across OAT. SY 0.75 vs 0.60–0.83.
  - **prb, n4, 3.5 cm, gap:** EM 10.00 g, CF 4, score 1.00 — unchanged.
    PI +0.01 vs committed −0.35..−0.00 (a cell §29 ALREADY flagged as sign-unstable).
  - **M-B null cell (n4-finger-2.5 cm), paired:** pulse +0.04, active −0.06 —
    both inside their reported OAT ranges. Null holds.
- **The worker did not stop at "it holds" — it found the mechanism, by
  cross-reference rather than assumption.** At BOTH static cells the corner's
  numbers are reproduced almost exactly by the **contact×0.33 row alone** in the
  already-committed `prb_convergence.txt`: finger-2.5 cm contact×0.33 gives
  PI +2.06 / SY 0.75 against the corner's +2.08 / 0.75; gap-3.5 cm gives
  PI −0.00 / SY 0.60 against +0.01 / 0.60. Adding substep 8 and seed 2 contributes
  essentially nothing. **No super-additive interaction at the static cells.**
- **Contrast, and this is the actual finding:** at M-B's headline cells the same
  corner produced effects FAR outside anything a single axis predicted —
  pulse@4.5 cm OAT range +0.49..+1.57 → corner −0.16 (below the weakest single
  axis); active@5.0 cm OAT range +1.23..+1.56 → corner +0.02. That is genuine
  super-additivity, and on this evidence it is specific to MARGINAL findings.
- **Coherent shape: joint-corner sensitivity appears to scale with how close a
  finding already sits to the noise floor, not with a universal flaw in the
  harness.** §29's Goal-1 conclusions are large-margin (EM at ceiling, PI ≫ the
  0.3 cm threshold) and survive intact; M-B's findings hovered just above 0.3 cm
  and do not. The worker labelled this a hypothesis fitting 3 data points rather
  than a law — correct, and exactly the scope discipline this run kept having to
  enforce, now applied unprompted to its own reassuring result.
- **Consequence: the retroactive threat to Goal 1 is NOT realized.** The §2.3
  OAT battery's inadequacy is real but its damage is bounded to marginal claims.
  That is a far better outcome than either "everything is fine" (which nobody
  checked) or "two iterations are invalid."
- Untested and flagged by the worker: one corner only, 3 cells only; other joint
  combinations at the static cells unsampled; no corner run at n6/n8 or other §29
  offsets.
- **The gravity escalation has RESHAPED and the lead is telling the human so.**
  It was raised as "is the adaptive ADVANTAGE a zero-g artifact?" There is no
  longer a robustly convergent advantage to be an artifact of, so that form of the
  question is largely moot. The live form is now the REVERSE: **does the NULL
  generalize, or does gravity-off suppress a benefit that weight-driven
  pre-seating would reveal?** Weaker motivation, still real, and a different
  experiment's worth of value. Reported to the human as a changed question rather
  than left standing as originally posed.

**2026-09-05 — human decision #5 (faculty: PHYSICAL REALISM / mechanism design).
The escalation was answered with a better question.**
- Human: "To use gravity as an assisting force rather than something we fight,
  won't we have to provide a base on which the ball would land? This would mean
  the arm would catch the ball from below?"
- **Lead verified the geometry rather than reasoning from memory. The human is
  right, and the situation is worse than stated:**
  - The cup opens DOWNWARD. `SHOULDER_HOLD = 0` (arm hangs straight down); cup
    centre = `ee_world() + [0,0,-CUP_DEPTH]`, i.e. 4.5 cm BELOW the palm. Fingers
    mount on a 34 mm ring about the −z axis; 55 mm proximal passes the equator,
    32+25 mm middle/distal curl UNDER to meet beneath the ball. The mouth faces
    the ground — gravity pulls the ball toward the opening, not against support.
    (This is why §15 validated the cage by INVERSION test: inversion survival is
    required precisely because there is no floor but the fingers.)
  - **The "palm" is CONVEX** — `end_effector` is a sphere of radius **12 mm**,
    5 g, against a 30 mm ball. Ball-on-smaller-convex-sphere is an UNSTABLE
    equilibrium. The current palm does not merely fail to assist centering, it
    actively DE-centers. Flipping the cup upward alone would not give a base; a
    CONCAVE dished palm is required for gravity to seat the ball on-axis.
- **Consequence for M-B's null, and it is a scope limitation nobody had stated:**
  M-B asked whether an adaptive close can re-centre an off-center ball. In this
  geometry all re-centering must come from FINGER FORCES ALONE — gravity off, no
  supporting surface, against a de-centering convex palm. That is the hardest
  possible form of the question. The Yale/SDM literature the PREREGISTRATION
  CITED demonstrates re-centering in the OPPOSITE configuration: object resting
  under its own weight on a palm, hand closing over it. **The prereg's literature
  anchor did not match the testbed's geometry, and no gate caught it** — the
  provenance-tagged "literature-backed" prediction was backed by literature about
  a different mechanical configuration.
- **The lead's escalation was mis-posed and the human corrected it.** I asked
  "should we run these cells gravity-on?" In a downward-facing cup that tests
  RETENTION (can fingers hold the ball in), not RE-CENTERING. The coupled change
  is one experiment, not three: **cup up + dished palm + gravity on.**
- Costs recorded honestly: the drone must get UNDER a descending ball, so the ball
  falls through rotor downwash — and PyBullet models NO propwash (parking-lot
  item 11), so the sim would be silently optimistic about exactly the failure mode
  the change introduces. A miss puts the ball into the drone. Cup-up needs a ~180°
  shoulder sweep — no new DOF, but folded-back/inverted arm poses are a documented
  trap and sustained arm-up cascade stability is unverified.
- **Lead's recommendation to the human:** close M-B on its null (the null is real
  FOR THIS GEOMETRY), record the downward-facing convex-palm configuration as an
  explicit scope limitation rather than a footnote, and run "upward dished palm +
  gravity on" as its own milestone with its own pre-registration.
- **For the meta-study — the sharpest instance of the run's recurring error, and
  the only one no gate could have caught.** Every layer (worker, lead, verifier,
  reviewer, critic, observer) reasoned for two milestones about "re-centering"
  without anyone checking which way the cup faced or what shape the palm was. The
  detectors interrogate claims, evidence, scope, and sampling — none asks whether
  the TESTBED'S GEOMETRY MATCHES THE MECHANISM BEING CLAIMED. D9 (mechanism
  fidelity) covers whether the HAND is faithful; nothing covers whether the
  SITUATION is. Human nudge count: 5.
