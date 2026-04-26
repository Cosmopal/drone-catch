"""Plot a JSONL run log produced by `python src/main.py --log path.jsonl`.

Usage:
    python scripts/plot_run.py runs/last.jsonl              # writes runs/last.png
    python scripts/plot_run.py runs/last.jsonl --show       # also opens window
    python scripts/plot_run.py runs/last.jsonl -o foo.png   # custom output
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


PHASE_COLORS = {
    "warmup": "#eeeeee",
    "settle": "#dddddd",
    "tracking": "#ffe0b3",
    "carry_to_cube": "#cce5ff",
    "descend_to_cube": "#d4edda",
    "lift": "#f8d7da",
}


def load(path: Path):
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    if not rows:
        sys.exit(f"empty log: {path}")
    return rows


def shade_phases(ax, t, phases):
    start = 0
    for i in range(1, len(phases) + 1):
        if i == len(phases) or phases[i] != phases[start]:
            ax.axvspan(t[start], t[i - 1], color=PHASE_COLORS.get(phases[start], "#ffffff"),
                       alpha=0.4, lw=0)
            start = i


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=None)
    ap.add_argument("--show", action="store_true")
    args = ap.parse_args()

    rows = load(args.log)
    t = np.array([r["t"] for r in rows])
    phases = [r["phase"] for r in rows]
    catcher = np.array([r["catcher"]["pos"] for r in rows])
    catcher_tgt = np.array([r["catcher"]["target"] for r in rows])
    ball = np.array([r["ball"]["pos"] for r in rows])
    cube = np.array([r["cube"]["pos"] for r in rows])
    err = np.linalg.norm(catcher - catcher_tgt, axis=1)

    fig, axes = plt.subplots(3, 1, figsize=(10, 9), constrained_layout=True)

    # 1) z vs time
    ax = axes[0]
    shade_phases(ax, t, phases)
    ax.plot(t, catcher[:, 2], label="catcher z", color="C0")
    ax.plot(t, catcher_tgt[:, 2], label="catcher target z", color="C0", ls=":", alpha=0.6)
    ax.plot(t, ball[:, 2], label="ball z", color="C3")
    ax.set_ylabel("z (m)"); ax.set_xlabel("t (s)")
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title(f"{args.log.name}  ({len(rows)} samples)")

    # 2) tracking error
    ax = axes[1]
    shade_phases(ax, t, phases)
    ax.plot(t, err, color="C2")
    ax.set_ylabel("|catcher - target| (m)"); ax.set_xlabel("t (s)")

    # 3) top-down XY
    ax = axes[2]
    ax.plot(catcher[:, 0], catcher[:, 1], label="catcher", color="C0")
    ax.plot(ball[:, 0], ball[:, 1], label="ball", color="C3", alpha=0.6)
    ax.scatter(cube[-1, 0], cube[-1, 1], marker="s", color="C2", label="cube (final)", s=60)
    ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    ax.set_aspect("equal"); ax.legend(fontsize=8); ax.grid(alpha=0.3)

    out = args.output or args.log.with_suffix(".png")
    fig.savefig(out, dpi=120)
    print(f"wrote {out}")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
