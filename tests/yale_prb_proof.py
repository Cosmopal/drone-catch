"""PROOF that the PRB Yale hand (`src/yale_prb.py`) is a real MECHANISM, not a
contact-reading stand-in (spec §2A, reviewer detector D9). Three deliverables:

  (1) FLEXURE CONFORMANCE — the multi-segment finger chain curls CONTINUOUSLY
      around the sphere (proximal at the equator, middle+distal tuck UNDER), so it
      contacts the ball on MULTIPLE segments — a wrap a single rigid segment (or a
      straight non-curling chain) cannot make. Quantified by #segments-in-contact
      per finger; shown from side + under.

  (2) EMERGENT SELF-DISTRIBUTION — with the ball off-center, the per-finger
      flexions come out UNEQUAL (near finger stalls low, far fingers wrap more)
      PURELY from the physics: the close law (`yale_prb.actuate`) contains ZERO
      `getContactPoints` calls (grep-checkable). Centered → equal; off-center →
      unequal. This is measured, never commanded.

  (3) Honest ceiling stated in the module docstring + here.

Run:  python tests/yale_prb_proof.py            # prints proof + renders frames
      python tests/yale_prb_proof.py --headless # numbers only
Ball PINNED during the close (isolates the coupling from the gravity-off cup drop,
per §27) so the wrap/self-distribution is legible.
"""
from __future__ import annotations
import argparse
import math
import os
import sys

import numpy as np
import pybullet as p

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
import cage_harness as ch          # noqa: E402  (harness scaffolding + numerics)
import yale_prb as prb             # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "cage_frames",
                   "iter2", "prb")


def _segments_touching(g, ball):
    """Per-finger list of how many SEGMENTS (proximal/mid/distal) touch the ball —
    the conformance measure (a rigid single contact would be 1; a conforming wrap
    is 2-3)."""
    pts = p.getContactPoints(bodyA=g.body, bodyB=ball)
    links = [c[3] for c in pts]
    out = []
    for segs in g.finger_joints:
        out.append(sum(1 for j in segs if j in links))
    return out


def close_on_ball(offset_m, direction, cfg, render=False, tag=""):
    """Close the PRB hand on a PINNED ball at (offset, direction); return
    (per_finger_flex, n_fingers_touch, per_finger_seg_contacts). Optionally save
    3-angle HUD frames of the seated wrap."""
    p.connect(p.DIRECT)
    try:
        ch.setup_physics()
        g = ch.FixedGripper(ch.variants.ensure_variant(4))
        prb.set_open(g.body, g.finger_joints, cfg)
        g.set_finger_dynamics()
        prb.regularize_inertia(g.body, g.finger_links, cfg.inertia_scale)
        prb.prep(g.body, g.finger_joints)
        az = (math.pi / 2 if direction == "finger"
              else math.pi / 2 + math.pi / 4)
        off = offset_m * np.array([math.cos(az), math.sin(az), 0.0])
        cup = g.cup_world()
        ball = ch.setup_ball(cup + off)
        ball0 = np.array(p.getBasePositionAndOrientation(ball)[0])
        n_close = (ch.CLOSE_STEPS + ch.SETTLE_STEPS) * ch.SUBSTEP
        for s in range(n_close):
            p.resetBasePositionAndOrientation(ball, ball0.tolist(), [0, 0, 0, 1])
            p.resetBaseVelocity(ball, [0, 0, 0], [0, 0, 0])
            g.hold_arm_rigid()
            pull = min(1.0, s / (0.7 * n_close)) * cfg.pull_max
            prb.actuate(g.body, g.finger_joints, pull, cfg)   # NO contact read
            p.stepSimulation()
        flex = prb.finger_flexions(g.body, g.finger_joints, cfg)
        seg = _segments_touching(g, ball)
        nf = sum(1 for s in seg if s > 0)
        if render:
            _render(g, ball, flex, seg, offset_m, direction, tag)
        return flex, nf, seg
    finally:
        p.disconnect()


def _render(g, ball, flex, seg, offset_m, direction, tag):
    import imageio.v2 as imageio
    os.makedirs(OUT, exist_ok=True)
    ee = g.ee_world()
    proj = p.computeProjectionMatrixFOV(46, 1.0, 0.02, 4.0)
    cams = {
        "side": p.computeViewMatrix((0.45, 0.0, ee[2] - 0.02),
                                    (0, 0, ee[2] - 0.05), [0, 0, 1]),
        "under": p.computeViewMatrix((0.13, -0.13, ee[2] - 0.40),
                                     (0, 0, ee[2] - 0.05), [0, 0, 1]),
        "diag": p.computeViewMatrix((0.34, -0.34, ee[2] + 0.10),
                                    (0, 0, ee[2] - 0.04), [0, 0, 1]),
    }
    lines = [
        f"PRB Yale (physical tendon, NO contact-reading)  off={offset_m*100:.1f}cm {direction}",
        f"per-finger flexion: " + " ".join(f"{x:+.2f}" for x in flex),
        f"self-distrib spread: {max(flex)-min(flex):.2f} rad "
        + ("(EQUAL=centered)" if max(flex)-min(flex) < 0.3 else "(UNEQUAL=self-distributed)"),
        f"segments touching/finger: {seg}  (>1 = conforming wrap)",
    ]
    for name, view in cams.items():
        _, _, rgba, _, _ = p.getCameraImage(560, 560, viewMatrix=view,
                                            projectionMatrix=proj,
                                            renderer=p.ER_TINY_RENDERER)
        fr = np.array(rgba, np.uint8).reshape(560, 560, 4)[:, :, :3]
        fr = ch._draw_hud(fr, lines, color=(120, 255, 120))
        path = os.path.join(OUT, f"prb_{tag}_{name}.png")
        imageio.imwrite(path, fr)
        print("  frame:", os.path.abspath(path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true")
    args = ap.parse_args()
    cfg = prb.PRBConfig()
    render = not args.headless

    print("=== PRB Yale hand — mechanism-fidelity proof (D9) ===")
    print(f"config: k={cfg.k_spring} c={cfg.c_damp} pull_max={cfg.pull_max} "
          f"inertia_scale={cfg.inertia_scale}")
    print("close law src/yale_prb.actuate: contains getContactPoints? "
          + ("YES (BUG)" if "getContactPoints" in open(
              os.path.join(os.path.dirname(__file__), "..", "src", "yale_prb.py")
          ).read().split("def actuate")[1] else "NO — self-distribution is physical"))

    print("\n(1)+(2) centered vs off-center (pinned ball):")
    fc, nfc, segc = close_on_ball(0.0, "finger", cfg, render, "centered")
    print(f"  CENTERED     flex={['%+.2f'%x for x in fc]} spread={max(fc)-min(fc):.2f} "
          f"nf={nfc} seg={segc}")
    fo, nfo, sego = close_on_ball(0.035, "finger", cfg, render, "offcenter_finger")
    print(f"  OFF-CENTER   flex={['%+.2f'%x for x in fo]} spread={max(fo)-min(fo):.2f} "
          f"nf={nfo} seg={sego}")

    equal_c = (max(fc) - min(fc)) < 0.3
    unequal_o = (max(fo) - min(fo)) > 0.6
    conform = max(max(segc), max(sego)) >= 2
    print("\nVERDICT:")
    print(f"  centered symmetric (spread<0.3): {'PASS' if equal_c else 'FAIL'}")
    print(f"  off-center self-distributes (spread>0.6): {'PASS' if unequal_o else 'FAIL'}")
    print(f"  flexure conforms (a finger wraps >=2 segments): {'PASS' if conform else 'FAIL'}")
    print(f"  => emergent self-distribution + conformance from the MECHANISM: "
          f"{'PROVEN' if (equal_c and unequal_o and conform) else 'NOT proven'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
