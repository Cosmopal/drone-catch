# Goal-2 gated-loop run log

> Kept by the LEAD per `grasp-goal2-loop-spec.md` §5. One entry per event:
> milestone starts/ends, gate verdicts, escalations, human messages (+ the
> faculty each supplied), pre-registration outcomes. This log is primary data
> for the loop-design observation study (analysis doc Part VII.5; metric =
> human-nudges-to-truth).

## Roles (current)
- **Lead:** session `grasp-iter-lead` (Opus) — took over 2026-08-31 from the
  meta-analysis session, which now only OBSERVES (session `drone-catch-meta`).
  Lead duties: route worker reports through verifier → reviewer → critic
  (fresh-context Sonnet subagents), keep this log, escalate per spec §4, and
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
- Loop spec v2 written + committed (`grasp-goal2-loop-spec.md`, commit 2852b99).
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
  on 3.2.5; if the §29 reproduction cell fails, re-baseline comparison cells on
  this env (paired within one build) + validity-ledger entry for the env shift.
- Environment ownership delegated to the worker (version-freeze rule above).

**2026-08-31 — worker M-A brief in flight.**
- Worker (`grasp-iter-2`) has the modified M-A: (1) both regression gates on
  the WORKTREE (`arm_catch_solo --grid` was 12/12; `elbow_catch_solo
  --headless` was caught=True held=True); (2) localization of any failure with
  frames; (3) reproduce ONE §29 converge cell vs committed logs; (4) STOP and
  report with a recommendation on whether M-B numbers can be trusted on this
  env. M-B (adaptive re-centering per the committed prereg) starts only after
  the M-A report passes the lead's routing.

**2026-08-31 — lead handoff.**
- Coordination handed to `grasp-iter-lead` (Opus). Meta session steps back to
  observer. Next expected event: worker's M-A report → lead routes it
  (localization report → verifier confirms the diagnosis by perturbation, NOT
  by re-running the same config; then reviewer on frames). Remember the
  prereg-isolation rule when building gate contexts.
