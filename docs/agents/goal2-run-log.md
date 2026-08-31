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
- **Loop-design observation, unprompted by the interruption's content:** every
  piece of durable state that survived was in a COMMITTED artifact — the run log,
  the M-A evidence, the generator scripts. Everything that died was in session
  context: the brief, the standing requirements, the routing state. The
  committed-evidence discipline this run kept ratcheting toward for epistemic
  reasons turns out to double as crash recovery. The one gap was the WIP itself,
  which survived only by luck of the filesystem.
  - **RATCHET CANDIDATE (process layer): a milestone brief belongs in a committed
    file, not only in a session message.** One local episode; recorded as a watch
    item, not promoted.
