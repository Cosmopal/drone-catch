---
name: grasp-iter2-state
description: Where the grasp iteration-2 (cage-quality + faithful Yale hand) work lives and its status
metadata: 
  node_type: memory
  type: project
  originSessionId: 2809acdf-6cf1-469a-90e6-84f65a23096b
---

Cage-robustness **iteration 2** (static hold-QUALITY characterization + a faithful
Yale hand) lives on git branch **`grasp-iter2`** (worktree at
`.claude/worktrees/grasp-iter2`). It is based on the iteration-1 agent branch, NOT
current main, and is **not merged** — it remains the full historical experiment
record (frames/videos/logs/harness/PRB hand source), left as-is.

**2026-07-06: `thrust-vectoring-platform` was fast-forwarded into `main`** (was a
pure fast-forward, 0 conflicts) — `main` is now the working branch again;
`thrust-vectoring-platform` is stale/superseded (main has since gained one more
commit past it). Do not treat `thrust-vectoring-platform` as current.

**Same day: ported grasp-iter2's core-code + docs delta onto `main`** (commit
`ca9eb6a`), without rebasing/merging the branch. Investigation found that despite
zero shared commit history between `grasp-iter2` and `thrust-vectoring-platform`
(patch-id comparison came up empty — real independent parallel work, not a git
artifact), by the time `thrust-vectoring-platform` reached its tip, EVERY
overlapping file except two had converged to byte-identical content (37 of 39
files). The only two with real delta were confirmed via direct tip-to-tip diff to
be **pure additive, zero deletions**: `Drone.external_gripper` delegation hook +
`Drone.finger_reaction_ff` (+ its `ThrustVectoringDrone` mirror) in `src/drone.py`
/ `src/thrust_vectoring_drone.py` (both default-off/None, no behavior change), and
genuinely new write-up in `docs/iteration_findings.md` (§25-29, append-only after
the prior last line) and `docs/concepts/13-...md` (three "Update" sections
inserted before the pre-existing "Buildable at home" closer, which was preserved,
just reordered to stay last). Applied via `git diff <a> <b> -- <files> | git apply`
rather than `git merge`/`git rebase`, since git has no common-ancestor commit for
these files to three-way-merge against (would show false conflicts despite the
content being a clean superset). Regression gate green after applying:
`arm_catch_solo.py --grid` 12/12 held (max peak force 11.3N unchanged),
`elbow_catch_solo.py --headless` caught=True held=True. `grasp-iter2` branch
itself was not touched by this port.

**`prb` = the FAITHFUL Yale hand** (`src/yale_prb.py`), pseudo-rigid-body model:
flexure = revolute chains + torsional return springs + a *physical* constant-tension
tendon (self-distribution emergent, NOT contact-reading). Strategy **`yale`** in the
harness is the OLD discredited **contact-reading stand-in** (`src/yale_hand.py`, now
docstring-corrected). So `prb` vs `yale` in any log = faithful vs stand-in. See
[[mechanism-fidelity-not-behavioral-standin]].

**Goal 1: CLOSED, reviewer-approved (D1–D9 + provenance ratchet).** Result: the
faithful hand REVERSES iteration-1's "Yale ejects the off-center ball" (that was a
stand-in artifact). Faithful hand cages as robustly as fixed AND re-centers in the
FINGER direction (n4–n6, offset 1.5–3.5 cm, pull-in +1.3..+3.1) — more than fixed,
ties `soft` on magnitude but with clean convergence (soft was a knife-edge) + a
timestep-stable boundary to ≥5 cm. Honest nulls: no re-center in the GAP direction
or at n8. All static / fixed-base / gravity-off / sphere-only.
- Findings: `docs/iteration_findings.md §29` (+ §28 for soft/fixed/stand-in), `docs/concepts/13-adaptive-underactuated-grasping.md`.
- Data logs: `docs/cage_frames/iter2/logs/prb_*.txt`. Frames: `docs/cage_frames/iter2/cageQ_prb_*` + `.../prb/` (D9 proof). Videos: `docs/cage_videos/cagevid_prb_*_slowmo.mp4`.
- Harness: `tests/cage_harness.py` (quality metrics: escape-margin, pull-in, #contacts, symmetry; `--quality-grid/--converge/--paired/--boundary/--quality-frames`).
- Regression gate: `python tests/arm_catch_solo.py --grid` → 12/12; `python tests/elbow_catch_solo.py --headless` → caught=True held=True.
- Spec: `docs/agents/grasp-iteration2-spec.md` (UNTRACKED — has the reopening banner, §2A faithful-Yale build/prove/redo, §3 detectors D1–D9 incl. D9 mechanism-fidelity + provenance ratchet).

**NEXT — Goal 2 (not started):** adaptive re-centering (§2.5) + a dynamic layered
test (§2.6) where the faithful hand gets its FAIR gravity-on / momentum-seated regime
vs soft/fixed (the static sim structurally can't see an underactuated hand's benefit)
+ an explicit "what I did NOT test" list (§2.7). Run via the worker+reviewer loop.
