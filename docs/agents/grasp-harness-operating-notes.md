---
tags: [agent-loop]
---

# Grasp-harness operating notes

A successor's reference for `tests/cage_harness.py` and the M-B adaptive-
re-centering tooling built around it. **Acceptance test for this doc**: a
fresh agent with no context reads this + the code and runs a cell
correctly the first time — right invocation, right perturbation handling,
without re-discovering a defect already known. Everything here earned its
place against that test. History and results live in
[[iteration_findings#^26|§26]], [[iteration_findings#^28|§28]],
[[iteration_findings#^29|§29]], [[13-adaptive-underactuated-grasping|§13]],
and the run log — this doc only covers what you need to operate the
harness correctly.

## Environment and invocation

- Always `conda run -n robots --no-capture-output python -u <script>`.
  Without `--no-capture-output` + `-u`, output to a redirected/logged file
  stays empty until the process exits — if you're tailing a log to check
  progress, you'll see nothing and wrongly conclude the process is stuck.
- `conda run ... python -c "<multi-line string>"` fails outright:
  `NotImplementedError: Support for scripts where arguments contain
  newlines not implemented`. Write the script to a file and run that.
- **This machine kills background processes unpredictably** — including a
  trivial no-op `sleep` loop with nothing else running, so it isn't your
  script's fault. Long sweeps need to survive that:
  - Split into chunks that finish well under ~400s each.
  - Each chunk appends one JSON line per completed unit to a ledger file,
    with `f.flush(); os.fsync(f.fileno())` after every write — so a kill
    mid-chunk loses at most the in-flight unit, not the whole sweep.
  - On start, read the ledger and skip units already present, so re-
    invoking the same chunk command is always safe.
  - See `tests/mb_chunk_driver.py` for the reference implementation (used
    for every paired-delta sweep in M-B).

## Harness internals a newcomer will misread

- **Applying a perturbation.** `converge_cell`/`paired_converge` perturb
  by mutating module globals directly: `SUBSTEP`/`SIM_DT` (timestep),
  `CONTACT_STIFFNESS`/`CONTACT_DAMPING` (contact model), and a `seed`
  argument threaded into `run_cell` (ball-placement jitter). To reproduce
  or extend a perturbation, **mirror this exact mutation** — set the same
  globals, call `run_cell`/`render_quality`, restore the globals after.
  Do NOT reimplement the close/IK/control loop yourself to get a custom
  perturbation in: an earlier attempt at this (a from-scratch copy of
  `elbow_catch_solo.run()`'s loop for a custom camera) silently diverged
  from the real IK/control details and produced a false negative — neither
  strategy captured, in a run that should have. It was caught by cross-
  checking against the real function's numbers before anything shipped,
  not by inspection. Prefer monkeypatching/wrapping the real function
  (see `tests/mb_corner_render.py`'s use of `render_quality`'s own
  `seed=`/`tag_suffix=` params) over rewriting its internals.
- **`SUBSTEP`/`SIM_DT`**: `SIM_DT = DT / SUBSTEP` where `DT = 1/240`.
  Setting one without the other desyncs the sim resolution from what the
  code thinks it is — always set both together, e.g.
  `ch.SUBSTEP, ch.SIM_DT = 8, ch.DT / 8`.
- **Contact-scale semantics**: `CONTACT_STIFFNESS`/`CONTACT_DAMPING` in
  the OAT battery are a base value times a scale factor (0.33 / 1.0 /
  3.0), not an absolute stiffness — `ch.CONTACT_STIFFNESS = BASE_K *
  scale`.
- **`A_MAX_ESCAPE = 10.0 * G`** (`cage_harness.py:467`) is a **search
  cap** on the escape-margin bisection, not a physical ceiling. When a
  direction holds all the way to the cap, the HUD and printouts show
  `>=10.0g` — that number is **censored, not measured**; the true margin
  could be 10g or 40g. Never report "escape-margin 10.00g" as a real
  value — say "at-or-above the 10g search ceiling."
- **`flex` in the HUD/quality metrics is a per-finger SUM of all three
  segment joint angles, plus a rest-pose offset** (`yale_prb.
  finger_flexions`: `sum(joint_angles) - sum(rest_pose)`, rest_pose sums
  to −0.6) — it is NOT a single joint's angle. A flex value of +3.40 looks
  extreme and reads like a joint-limit saturation, but checking the actual
  per-joint angles (`p.getJointState`) against the URDF's real limits
  (`assets/make_gripper_urdf.py`: finger segments are `lower="-0.8"
  upper="2.0"`) showed the three joints at [0.501, 1.000, 1.300] rad —
  comfortably inside the limits. +3.40 was just the normal fully-closed
  pose, reached by all four fingers because none of them were touching
  anything. Always read per-joint angles directly if a flex number looks
  like it might mean a limit; don't infer it from the aggregate.
- **`_fingers_touching()`** (`cage_harness.py:446`) uses real
  `p.getContactPoints`, not a distance threshold — "N fingers touching" in
  any HUD/printout means an actual PyBullet contact was found, not
  proximity.
- **`rotate_runs(keep=5)`** (used by `elbow_catch_solo.py`'s default
  `--runs-dir` path, and similar spots) silently deletes all but the last
  5 runs in a directory. It is not durable storage for a sweep — anything
  you need to keep must go to a directory outside that rotation (this
  study uses `docs/cage_frames/iter2/mb_*_frames/`, which is never
  rotated).

## Known defects — don't rediscover these

- **Finger-direction ball placement starts already interpenetrating a
  finger, at every offset tested (1.5–5.5cm), depth growing monotonically
  with offset**: −1.98mm (1.5cm) → −11.19mm (2.5cm) → −20.40mm (3.5cm) →
  −29.61mm (4.5cm) → −34.21mm (5.0cm) → −35.18mm (5.5cm). Measured with
  `p.performCollisionDetection()` immediately after `setup_ball()`,
  before any `stepSimulation()` — see `tests/mb_t0_penetration_check.py`
  and its committed log. This means "pull-in" above roughly 3.5cm partly
  measures the solver resolving a placement overlap, not the hand
  re-centering a free ball. Gap-direction has smaller/inconsistent
  overlap (present at 2.5/3.5/4.5cm, absent at 1.5/5.5cm). Not yet
  determined whether this generalizes to n=6/n=8 or other strategies (the
  placement code itself is strategy-independent, so it likely does, but
  this hasn't been checked).
- **A stiff-contact × fine-substep × large-offset blow-up region**: at
  offset 5.0cm finger, contact-scale ×3.0, substep ∈ {8, 16}, the sim
  produces a real (not metric-artifact) catastrophic ejection — ball ends
  up 29–45cm from the cup, escape-margin reads ~0.16g. Traced visually to
  a sideways squeeze-out past one displaced finger, not a joint-limit
  saturation and not a broken margin computation. Does NOT occur at the
  identical settings at 4.5cm. See `tests/mb_convergence_check.py` +
  `mb_blowup_diag.py`/`mb_blowup_render.py` and
  `docs/cage_frames/iter2/mb_blowup_frames/`.
- **The OAT convergence battery (`converge_cell`/`paired_converge`) is
  one-axis-at-a-time from a single baseline — 12 rays from one point, not
  a coverage of the space.** A config that is simultaneously
  coarse-timestep AND soft-contact AND a specific seed is never sampled.
  Two such joint corners were tested by hand at the M-B headline cells:
  one left both findings unchanged, the other flipped one delta's sign
  and collapsed the other to ~0 — i.e. **"convergent across all 12
  perturbations" does not mean convergent everywhere nearby.** See
  `tests/mb_joint_corner.py` and `docs/cage_frames/iter2/logs/
  mb_corner_*.jsonl`.
- **Validity guard**: before trusting any cell's `pull_in`/`escape_margin`
  number, check `n_contact_fingers > 0` and `score > 0`. A fully-ejected
  cell (see the blow-up above) still returns numeric `pull_in`/
  `escape_margin` values — they're just describing an empty cage, and read
  as nonsense if taken at face value (`pull_in` of −24 to −40cm).

## Evidence discipline (with the episode that produced each rule)

- **Decode every video before citing it, not just check it exists.** A
  render once produced a 48-byte `.mp4` (`ffmpeg`/imageio failed
  silently) that was described as usable evidence without being opened —
  caught by a reviewer, not by the author. Since then: `imageio.
  get_reader(path); r.count_frames()` on every video before citing any of
  it, and check the WHOLE batch a render produced, not just the one file
  that was flagged — a sibling file in the same batch can be corrupt too.
- **Use non-rotating output directories for anything you need to keep.**
  See `rotate_runs` above — this is the same rule from the harness-
  internals angle; the episode is the same one.
- **Bake perturbation parameters into every filename, unambiguously**
  (e.g. `..._CORNER_ss8_ctc033_seed2_...` vs `..._NOMINAL_...`). A figure
  once traveled between two different runs and got reported as one
  consistent trace (a hold/lift transition figure from one run
  misattributed to another) — a "cross-run chimera." Corner and nominal
  renders must never be filename-indistinguishable from each other.
- **A number must trace to committed, parameterized CODE — not merely a
  committed log.** A milestone's headline number once existed only as
  prose in a lead's own run log (transcribed from a scratchpad run,
  never committed); it had to be regenerated from a committed generator
  script before anyone could trust it. The fix pattern: any one-off
  measurement script that produces a reportable number gets committed
  alongside its output, with the exact reproducing command in the commit
  message (see `tests/mb_chunk_driver.py`, `tests/mb_corner_render.py`,
  `tests/mb_blowup_diag.py` for the pattern).

## Pointers, not restated here

- Mechanism history, PRB hand design, Goal-1 results: [[iteration_findings#^26|§26]],
  [[iteration_findings#^28|§28]], [[iteration_findings#^29|§29]],
  [[13-adaptive-underactuated-grasping|§13]].
- M-B pre-registration (predictions P1–P5, falsifiers): `docs/agents/goal2-prereg-MB.md`.
- Iteration-1 caging study + the original stand-in-hand history:
  [[cage-robustness-study]].
