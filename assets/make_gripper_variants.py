#!/usr/bin/env python3
"""Generate caging-gripper URDF variants with N fingers to NEW files
(quadrotor_gripper_n{N}.urdf) WITHOUT touching the canonical
quadrotor_gripper.urdf.

Reuses the EXACT base / arm / finger geometry from make_gripper_urdf.py (imports
its building blocks), only varying the finger COUNT. The finger mount ring,
segment lengths, and per-segment joint limits are unchanged, so a variant is the
same hand with more fingers spread evenly around the palm ring.

Used by tests/cage_harness.py for the finger-count sweep (4 / 6 / 8). Run:
    python assets/make_gripper_variants.py
"""
import math
import os

import make_gripper_urdf as g

ASSETS = os.path.dirname(__file__)


def build(n_fingers: int, path: str):
    parts = [g.HEADER, g.PROPS, g.ARM]
    for i in range(n_fingers):
        parts.append(g.finger_block(i, 2 * math.pi * i / n_fingers + math.pi / 2))
    parts.append("</robot>\n")
    with open(path, "w") as f:
        f.write("".join(parts))
    return path


def variant_path(n_fingers: int) -> str:
    return os.path.join(ASSETS, f"quadrotor_gripper_n{n_fingers}.urdf")


def ensure_variant(n_fingers: int) -> str:
    """Generate the N-finger variant if missing; return its path."""
    path = variant_path(n_fingers)
    if not os.path.exists(path):
        build(n_fingers, path)
    return path


def main():
    for n in (4, 6, 8):
        path = build(n, variant_path(n))
        print(f"wrote {path}  ({n} fingers x {len(g.SEG_LENS)} segments, "
              f"reach ~{sum(g.SEG_LENS):.3f} m)")


if __name__ == "__main__":
    main()
