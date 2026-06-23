# Caging-study video evidence map (corrected — see iteration_findings §26)

> The earlier version of this map presented a "gap is the failure mode" + a
> compliance comparison. Those were a **timestep + rigid-contact numerical
> artifact** (§26). These clips use the **corrected, converged numerics**
> (compliant contact pads + 1/960 substep, the harness default now), and the
> negative control still escapes — so they are trustworthy.

Each clip is rendered by `tests/cage_harness.py --video [--slowmo]` from TWO
angles side-by-side: a 3/4 **diagonal** view (left) and an **under/below** view
(right, shows the distal segments tucking UNDER the ball = form closure).

- **fast** (`*.mp4`, ~5.5 s): the close, then the **2.5 g disturbance battery** in
  8 directions. Ball stays in the basket = HELD; flung away = ESCAPED.
- **slowmo** (`*_slowmo.mp4`, ~9 s @ 34 fps): true slow-motion of the SAME close
  (finer-dt gives 4x more frames, so it is smooth), grasp only, no battery.

## Claim -> evidence (corrected)

### Claim 1 — the current 4-finger fixed close cages a centered ball
- `cagevid_fixed_n4_finger_0mm.mp4` -> **HELD 8/8** (ball moves <0.3 cm under
  2.5 g from every direction, including inversion).
- `cagevid_fixed_n4_finger_0mm_slowmo.mp4` -> the proximal reaches the equator and
  the distal tucks under (under view).

### Claim 2 — it ALSO cages off-center to 3.5 cm in BOTH directions (no gap weakness)
- `cagevid_fixed_n4_finger_35mm.mp4` -> **HELD 8/8** (3.5 cm toward a finger).
- `cagevid_fixed_n4_gap_35mm.mp4` -> **HELD 8/8** (3.5 cm toward a GAP). At the
  corrected numerics the gap-offset ball is caged, not paddled out — the slow-mo
  (`..._gap_35mm_slowmo.mp4`, under view) shows the fingers wrapping it.
  *(This is exactly the case the artifact showed "escaping"; it does not.)*

### Claim 3 — the REAL capture limit is ~4.5 cm, and no strategy extends it
- `cagevid_fixed_n4_finger_55mm.mp4` -> **ESCAPED 0/8** (seated_fingers=0): at
  5.5 cm the ball is outside the basket. The limit is ~5 cm toward a finger,
  ~4 cm toward a gap (a small real ~1 cm directional difference). Beyond it,
  fixed / compliant / soft / under ALL fail — compliance does not extend the
  capture radius at this offset scale.

## What changed vs the artifact version
- "gap fails at 1.5 cm" -> gap cages to ~3.5-4 cm (the limit was off by ~3 cm).
- "soft fails / grab-then-release limit cycle", "compliance worse/under-credited",
  the strategy rankings, splayed-vs-curled -> all rigid-contact artifacts; at
  converged numerics every strategy cages to 3.5 cm and the distinctions vanish.

## Regenerate / inspect the artifact
```
python tests/cage_harness.py --video          --strategy fixed --offset 0.035 --dir gap     # HELD now
python tests/cage_harness.py --video --slowmo --strategy fixed --offset 0.035 --dir gap     # ~9 s slow grasp
python tests/cage_harness.py --cell --substep 1 --strategy fixed --offset 0.035 --dir gap   # the artifact: 0.00
python tests/cage_harness.py --cell             --strategy fixed --offset 0.035 --dir gap   # converged: 1.00
```

## Yale underactuated hand (§27) + on-screen metrics (HUD)

All `--video` clips now overlay a **HUD** with the live metrics (fingers touching,
ball displacement, HELD/ESCAPED; for `yale` the per-finger flexions = the
self-distribution). New flag `--pin` holds the ball fixed during the close (a
gravity-off free off-center ball ejects under an aggressive adaptive close, so
pin to SEE the wrap).

- `cagevid_yale_n4_finger_35mm_pin_slowmo.mp4` — **the self-distribution, visible**:
  off-center ball, HUD shows `finger flex: -0.4 +3.1 +3.3 +3.2` / `spread 3.71 rad`
  — the near finger STALLS on the ball, the far three wrap. The whiffletree
  differential made literal.
- `cagevid_yale_n4_finger_35mm_pin.mp4` — same wrap, then the disturbance battery
  on the released ball: **ESCAPED 0/8** (the asymmetric soft wrap captures but is
  not a robust cage) vs `cagevid_fixed_n4_*` HELD 8/8.
- `dynamic_catch_fixed.mp4` vs `dynamic_catch_yale.mp4` — the validated scoop catch
  with each close (captioned with the result). Fixed: caught+held (robust). Yale:
  caught+held WITHOUT video but the rendering overhead flips it to a drop WITH
  video — i.e. the Yale catch is MARGINAL where the rigid catch is robust.

Reproduce:
```
python tests/cage_harness.py --video --slowmo --pin --strategy yale --offset 0.035 --dir finger
python tests/cage_dynamic_catch.py --headless --close yale --runs-dir runs/yale
```
