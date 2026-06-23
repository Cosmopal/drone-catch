# Agent status — robust caging under cm-scale position uncertainty

Branch: `thrust-vectoring-platform` (isolated worktree). Env: conda `robots`
(`conda run -n robots ...`). Run all commands from the repo root.

## Objective
Solve robust **caging** of a ball under cm-scale position uncertainty for the
catcher's caging gripper — with a TRUSTWORTHY test harness, because prior quick
experiments (iteration_findings §24) gave noisy/contradictory results.

## Follow-up: faithful Yale-OpenHand underactuated hand (§27)
`src/yale_hand.py` — a numerically-stable position-based tendon with the real
COUPLING (inter-finger whiffletree + intra-finger wrap-and-tuck + compliant
joints), on the static harness (`--strategy yale`) and the dynamic catch
(`tests/cage_dynamic_catch.py`, via the additive `Drone.external_gripper` hook).
- **Self-distribution VERIFIED** (off-center -> per-finger flexions differ:
  3.5 cm toward a finger gives spread ~3.4 rad, near finger stalls).
- **Static harness**: yale LOSES to fixed (gravity-off anti-tuck bias).
- **Dynamic catch**: yale MATCHES fixed at nominal (both caught+held) but needs a
  FIRMER tendon tension (0.7 vs 0.5) to retain, and is marginally worse across the
  velocity grid (fixed 2/5, yale 1/5). It does NOT beat the rigid close in sim —
  the Yale benefit is for real-hardware uncertainty this sim doesn't model.
- Additive + opt-in; regression gates re-checked (self-validation PASS, elbow
  caught+held, arm_catch_solo 12/12).

## Status: COMPLETE — but read the CORRECTION first.

> **CORRECTION (iteration_findings §26).** The original off-center findings ("gap
> is the failure mode," strategy rankings, "compliance doesn't help") were a
> **timestep + rigid-contact numerical artifact**. The self-validation passed
> because it only covered the stable extremes (centered cage / far-outside
> escape), NOT the ill-conditioned off-center band. Fixed by **compliant contact
> pads + a 1/960 substep** (now the harness default; `--substep` to inspect),
> which CONVERGE (substep 4 == 8). Corrected, trustworthy result: the current
> 4-finger fixed close **robustly cages off-center balls to ~3.5 cm in ALL
> directions and with ALL strategies**; the real capture limit is ~4.5 cm (gap
> ~1 cm weaker than finger); no strategy extends it. The trustworthy LESSON:
> determinism is not convergence — vary the timestep/contact model as a
> convergence check on any contact-rich result.

### What was built (all additive; existing Drone/throw/catch unchanged)
| File | Role |
|---|---|
| `tests/cage_harness.py` | Phase-0/1 deterministic FIXED-BASE harness. Real form-closure metric = 26-direction, 2.5 g disturbance battery via `saveState`. Modes: `--self-test`, `--grid`, `--cell`, `--render`, `--video [--slowmo]`. |
| `assets/make_gripper_variants.py` + `quadrotor_gripper_n{4,6,8}.urdf` | N-finger URDF variants (NEW files; canonical urdf untouched). |
| `tests/cage_drone_close.py` | Phase-2 on-drone finger-close body-reaction test (pitch during close; `--ff`, `--tv`, `--table`). |
| `tests/cage_drone_catch.py` | Phase-2 full catch on the TV drone, winning close + seating-bias offset. |
| `src/drone.py`, `src/thrust_vectoring_drone.py` | `finger_reaction_ff` (additive, default OFF) + `_finger_reaction_ff_body_torque()`. |
| `docs/iteration_findings.md` §25, `docs/concepts/13` addendum | findings + concept writeup. |
| `docs/cage_frames/`, `docs/cage_videos/` | rendered stills + clips (fast ~5.5 s overview; `*_slowmo.mp4` = grasp-only, first 1.5 s sim -> 9 s video). |

### Verification gates
1. Harness self-validation — **PASS**: determinism `[1,1,1]`; positive control
   (centered, current close) 26/26; negative control (8 cm outside) 0/26.
2. A config beats the current close off-center — **NOT MET (honest negative)**.
   The current 4-finger splayed fixed close is the best (mean 0.48 at
   offset>=2.5 cm); nothing tested beats it. Table in §25.
3. On the TV drone: winning (fixed) close holds body pitch **2.0 deg < 5 deg**
   during close — **PASS**. Full retained catch on TV — **NOT achieved**, blocked
   by a pre-existing TV arm-tracking station-keeping instability (body climbs to
   the ceiling under rapid per-tick IK arm slews; repo TV catch is WIP, §20). Not
   a close-strategy problem.
4. Regression — **PASS**: `elbow_catch_solo` caught+held; `arm_catch_solo --grid`
   12/12 (unchanged; FF is default-off).

### Key findings (trustworthy; several overturn the noisy priors)
- The current rigid fixed-pose close is already near the geometric ceiling for a
  4-finger ring. Its only weakness is off-center **toward a finger GAP** (the
  ball slips between fingers) — a **coverage** problem, not a compliance one.
- **Compliance does not help; `soft` (Fin-Ray spring) scores 0 even centered**
  (too soft to resist 2.5 g — the conform-vs-hold tradeoff).
- Constant-torque "tendon" close is **numerically ill-conditioned** on the light
  (~3-4 g/segment) 3-link finger chain (Coulomb-like joint threshold, sign-flips,
  frozen distal joints); excluded from the ranking. Force-limited position
  control is the robust yield-on-contact stand-in.
- **Finger-reaction FF is a clean negative**: in the arm-down pose the symmetric
  ring's motor torques sum to ~0 (FF predicts ~0), while the real disturbance is
  the asymmetric finger-link inertial/contact reaction the model can't see. The
  winning rigid close needs no FF anyway.
- Hand types covered: finger count {4,6,8}; close strategy {fixed, compliant,
  soft, (tendon excluded)}; ready pose {splayed, partly-curled}. Splayed beats
  curled uniformly. Geometry (3-segment long-proximal hand) held fixed.

### Reproduce
```
conda run -n robots python tests/cage_harness.py --self-test
conda run -n robots python tests/cage_harness.py --grid
conda run -n robots python tests/cage_harness.py --video --strategy fixed --offset 0.035 --dir gap
conda run -n robots python tests/cage_harness.py --video --slowmo --strategy fixed --dir finger   # 9s grasp-only
conda run -n robots python tests/cage_drone_close.py --table
conda run -n robots python tests/elbow_catch_solo.py --headless     # regression
conda run -n robots python tests/arm_catch_solo.py --grid           # regression 12/12
```

### Commits (this worktree)
- `1ab2609` harness + study + finger-reaction FF + sync of current working tree.
- `7947ab5` video render mode + supporting clips.
- `60e8cf8` slow-mo grasp video mode (--slowmo) + tightened overviews.

### Open / next steps (the harness now makes these tractable)
- Close-pose RE-OPTIMISATION per finger count to close the gap-direction weakness
  (the one lever not yet swept; denser ring needs a re-tuned close pose).
- Fix the TV arm-tracking station-keeping (rapid IK slews launch the body) to get
  a retained TV catch under offsets (§20 WIP).
- Vary hand GEOMETRY (segment lengths, mount-ring radius), not just finger count.

### Notes / gotchas for the next agent
- The worktree branch only tracked the v1 core; the current gripper/TV/test stack
  was untracked in the main checkout and was synced into the branch in `1ab2609`
  so the study is reproducible. The worktree's `CLAUDE.md` is the STALE v1 — use
  the main checkout's current CLAUDE.md as the source of truth.
- `run_cell` close (force/gains/steps) is the validated/self-tested path — do NOT
  change it or the scores/self-validation drift. The slow-mo grasp uses a
  separate video-only ramped servo.
