# Caging-study video evidence map

Each clip is rendered by `tests/cage_harness.py --video [--slowmo]` from TWO
angles side-by-side: a 3/4 **diagonal** view (left) and an **under/below** view
(right) that shows whether the distal segments tuck UNDER the ball (the
form-closure signal). Two kinds of clip:

- **fast** (`*.mp4`, ~5.5 s): the close, then the **2.5 g disturbance battery**
  in 8 directions. The ball staying in the basket = HELD; flung away = ESCAPED.
  This is the proof of the "caged" claim (a real form-closure test, not
  distance + touching).
- **slowmo** (`*_slowmo.mp4`, ~3.9 s, 6x): true slow-motion of the SAME close
  (identical physics, just every step at 40 fps) — for analysing the grasp
  mechanics. Grasp only, no battery.

`seated_fingers` is measured at the same instant (right after the close) in both,
so fast and slow agree.

## Claim -> evidence

### Claim 1 — the current 4-finger fixed-pose close cages a centered ball
- `cagevid_fixed_n4_finger_0mm.mp4` -> **HELD 8/8** (ball moves 0.1 cm under 2.5 g
  from every direction, including inversion).
- `cagevid_fixed_n4_finger_0mm_slowmo.mp4` -> watch the proximal reach the equator
  and the distal tuck under (under view).

### Claim 2 — the cage is robust OFF-CENTER toward a finger (to 3.5 cm)
- `cagevid_fixed_n4_finger_35mm.mp4` -> **HELD 7/8** at 3.5 cm toward a finger.

### Claim 3 — the failure mode is off-center toward a GAP (direction, not magnitude)
The controlled comparison: same hand, same close, same offset *magnitude* — only
the *direction* changes.
- `cagevid_fixed_n4_finger_35mm.mp4` (toward a finger) -> **HELD 7/8**, vs
  `cagevid_fixed_n4_gap_35mm.mp4` (toward a gap, same 3.5 cm) -> **ESCAPED 0/8**.
- `cagevid_fixed_n4_gap_15mm.mp4` -> **ESCAPED 0/8** — the gap direction fails at
  even 1.5 cm.
- `cagevid_fixed_n4_gap_35mm_slowmo.mp4` -> the *mechanism*: the closing fingers
  paddle the gap-offset ball OUT (it ends up expelled below the cage), because
  there is no finger in the gap to trap it. => it is a finger-COVERAGE problem.

### Claim 4 — compliance does not WIN, but it is not a flat negative (re-examined)
The first-pass `soft`/`compliant` strategies servo to the FIXED cage pose, so they
can't adapt the finger SHAPE — they under-test underactuation:
- `cagevid_soft_n4_finger_0mm.mp4` -> **ESCAPED 0/8 even CENTERED**: too compliant
  to resist 2.5 g (conform-vs-hold tradeoff).
- `cagevid_compliant_n4_finger_35mm.mp4` -> **ESCAPED 0/8** where the rigid close
  HELD 7/8 — a low-force close to the fixed pose is *worse* off-center.

A PROPER **underactuated/differential** close (`under`: low force toward a DEEP
curl, each joint stalling on contact while the rest curl further) DOES help the
failure mode:
- `cagevid_under_n4_gap_25mm.mp4` -> **HELD 3/8** shown (full 26-battery 0.50) vs
  `cagevid_fixed_n4_gap_25mm.mp4` -> **0/8** at the same gap-offset 2.5 cm. The
  under view shows the fingers wrapping deeper around the off-center ball
  (frames `docs/cage_frames/cage_under_n4_gap_25mm_{diag,under}.png`).
- It still LOSES overall: aggressive enough to help the gap, it *ejects* centered/
  finger balls (the under-tuck squeezes the ball out the top in the gravity-OFF
  isolation). The fair test is the DYNAMIC catch (ball entering with downward
  momentum to seat it), not this static fixed-base metric — so the compliance
  question is *not won* on the static metric but is plausibly under-credited by it.

## Claims that still need video evidence (next clips)
These are supported by the scored `--grid` table (iteration_findings §25) but do
not yet have a dedicated clip:
- "more fingers trade gap-coverage for finger-direction robustness" — n6/n8 at
  matched offsets (the data is non-monotonic/fragile, so a clip should show the
  fragility honestly, not oversell n8).
- "splayed ready beats partly-curled" — a curled-ready clip failing to seat.
- "constant-torque tendon is numerically ill-conditioned" — a `--strategy tendon`
  clip showing the fingers curling to a non-caging shape / chattering.
- finger-reaction FF on the drone — belongs to `tests/cage_drone_close.py`
  (floating base), not this fixed-base harness.

## Regenerate
```
python tests/cage_harness.py --video          --strategy fixed --offset 0.035 --dir gap     # fast + battery
python tests/cage_harness.py --video --slowmo --strategy fixed --offset 0.0   --dir finger  # ~9 s slow grasp
python tests/cage_harness.py --video          --strategy under --offset 0.025 --dir gap     # underactuated vs gap
```
