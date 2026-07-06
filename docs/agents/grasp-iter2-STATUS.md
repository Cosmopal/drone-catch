# Grasp study, iteration 2 — STATUS / handoff (resume here)

> Single "pick up here" doc for the cage-robustness iteration-2 work. The technical
> artifacts live on a **separate branch** (`grasp-iter2`); this doc + the spec +
> `docs/agents/grasp-experiment-reflection.md` live on `thrust-vectoring-platform`.

## Where the work lives
- **Branch `grasp-iter2`**, worktree at `.claude/worktrees/grasp-iter2/`.
  Based on the iteration-1 agent branch, **not** current main (~28 behind); **not merged** (deferred by choice).
- Spec: `docs/agents/grasp-iteration2-spec.md` (reopening banner + §2A faithful-Yale + §3 detectors D1–D9 + provenance ratchet).
- Method: a **worker + reviewer** sub-agent loop; the reviewer gatekeeps under D1–D9 + a provenance ratchet before anything closes.

## `prb` = the FAITHFUL Yale hand
- Strategy **`prb`** (`src/yale_prb.py`) = faithful **pseudo-rigid-body** Yale hand: flexure = revolute chains + torsional return springs + a **physical constant-tension tendon** (self-distribution emergent, NOT contact-reading). Inertia ×50-regularized (a stated discretization choice, invariance-verified).
- Strategy **`yale`** (`src/yale_hand.py`) = the OLD **contact-reading stand-in** (docstring corrected; superseded). `prb` vs `yale` in any log = faithful vs stand-in.
- Ceiling (honest): static / fixed-base / gravity-off / **sphere only**; no shape adaptation (that needs MuJoCo — PyBullet has no continuous compliance / native tendons).

## Goal 1 — CLOSED, reviewer-approved
The faithful hand **reverses** iteration-1's "Yale ejects the off-center ball" (that was a stand-in artifact). Faithful hand **cages as robustly as `fixed` AND re-centers** in the FINGER direction (n4–n6, offset 1.5–3.5 cm, pull-in +1.3..+3.1) — **more than `fixed`**, **ties `soft`** on magnitude but with clean convergence (soft was a knife-edge) + a **timestep-stable boundary to ≥5 cm**. Honest nulls: no re-center in the GAP direction or at n8.
- Findings: `docs/iteration_findings.md §29` (+ §28 for soft/fixed/stand-in), `docs/concepts/13-adaptive-underactuated-grasping.md`.
- Harness + quality metrics: `tests/cage_harness.py` (escape-margin, pull-in, #contacts, symmetry; `--quality-grid/--converge/--paired/--boundary/--quality-frames`; `--strats`, `--compare`, `--paired-a/-b`, `--prb-inertia`).
- Data logs: `docs/cage_frames/iter2/logs/prb_*.txt`. Frames: `docs/cage_frames/iter2/cageQ_prb_*` + `.../prb/` (D9 proof). Videos: `docs/cage_videos/cagevid_prb_*_slowmo.mp4` (win/null/boundary, slow-mo HUD).
- **Regression gate (must stay green):** `python tests/arm_catch_solo.py --grid` → held 12/12; `python tests/elbow_catch_solo.py --headless` → caught=True held=True.

## Goal 2 — NEXT (not started)
Per spec §2.5–§2.7, via the worker+reviewer loop:
1. **Adaptive re-centering** (§2.5) — a close that senses/adjusts for an off-center ball, measured on the quality metric vs the rigid close.
2. **Dynamic layered test** (§2.6), kept SEPARATE from the static study — ball velocity × approach angle × catch pose vs trajectory, quality at capture. **Give the faithful hand its FAIR regime here**: gravity-on / momentum-seated vs soft/fixed (the static sim structurally can't see an underactuated hand's benefit).
3. **Explicit "what I did NOT test" list** (§2.7).

## To resume
Point a session at branch `grasp-iter2`; read `§29` + `concepts/13` + the spec §2A; confirm the regression gate is green; then run Goal 2 through the worker+reviewer loop. Standing reviewer detectors: D1–D9 + provenance ratchet (incl. **D9 mechanism-fidelity** — a behavioral stand-in does NOT count as testing a mechanism).
