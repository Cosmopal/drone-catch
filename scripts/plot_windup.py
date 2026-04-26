"""Plot planned vs actual drone trajectory during throw windup."""
import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=None)
    args = ap.parse_args()

    rows = [json.loads(l) for l in args.log.read_text().splitlines() if l.strip()]
    backup = [r for r in rows if r['phase'] == 'backup']
    windup = [r for r in rows if r['phase'] == 'throw_windup']
    if not windup:
        sys.exit("no throw_windup samples found")

    # actual trajectory (use backup tail + windup so we see the handoff)
    pre = backup[-3:] if len(backup) >= 3 else []
    seq = pre + windup
    t_actual = np.array([r['t'] for r in seq])
    pos = np.array([r['thrower']['pos'] for r in seq])
    vel = np.array([r['thrower']['vel'] for r in seq])

    # planned trajectory: vel ramps linearly from 0 to release_vel over ramp_duration
    # The throw planner uses release_vel = (5.28, 0, 4.65) — same as in main.py:
    release_vel = np.array([5.28, 0.0, 4.65])
    ramp_duration = 1.0
    backup_pos = np.array([-5.0, 0.0, 0.5])  # nominal backup target

    # Plan starts at first windup sample
    t0 = windup[0]['t']
    t_plan = np.linspace(0, ramp_duration, 100)
    # vel(t) = release_vel * t/ramp
    vel_plan = release_vel[None, :] * (t_plan / ramp_duration)[:, None]
    # pos(t) = backup_pos + 0.5 * release_vel * t^2 / ramp
    pos_plan = backup_pos[None, :] + 0.5 * release_vel[None, :] * (t_plan ** 2)[:, None] / ramp_duration

    fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)

    # Position x and z, actual vs planned
    ax = axes[0, 0]
    ax.plot(t_actual - t0, pos[:, 0], 'C0o-', label='actual x', ms=3)
    ax.plot(t_plan, pos_plan[:, 0] + (windup[0]['thrower']['pos'][0] - backup_pos[0]),
            'C0--', alpha=0.6, label='planned x (offset to actual start)')
    ax.set_xlabel('t since windup start (s)'); ax.set_ylabel('x (m)')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    ax.axhline(-2.0, color='C0', linestyle=':', alpha=0.4, label='release_x')
    ax.set_title('position x')

    ax = axes[0, 1]
    ax.plot(t_actual - t0, pos[:, 2], 'C1o-', label='actual z', ms=3)
    ax.plot(t_plan, pos_plan[:, 2] + (windup[0]['thrower']['pos'][2] - backup_pos[2]),
            'C1--', alpha=0.6, label='planned z (offset to actual start)')
    ax.axhline(1.5, color='gray', linestyle=':', label='release_z')
    ax.axhline(3.0, color='red', linestyle=':', label='ceiling')
    ax.set_xlabel('t since windup start (s)'); ax.set_ylabel('z (m)')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    ax.set_title('position z')

    # Velocity x and z, actual vs planned
    ax = axes[1, 0]
    ax.plot(t_actual - t0, vel[:, 0], 'C0o-', label='actual vx', ms=3)
    ax.plot(t_plan, vel_plan[:, 0], 'C0--', alpha=0.6, label='planned vx')
    ax.axhline(release_vel[0], color='gray', linestyle=':', label=f'target {release_vel[0]:.2f}')
    ax.set_xlabel('t since windup start (s)'); ax.set_ylabel('vx (m/s)')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    ax.set_title('velocity x')

    ax = axes[1, 1]
    ax.plot(t_actual - t0, vel[:, 2], 'C1o-', label='actual vz', ms=3)
    ax.plot(t_plan, vel_plan[:, 2], 'C1--', alpha=0.6, label='planned vz')
    ax.axhline(release_vel[2], color='gray', linestyle=':', label=f'target {release_vel[2]:.2f}')
    ax.set_xlabel('t since windup start (s)'); ax.set_ylabel('vz (m/s)')
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    ax.set_title('velocity z')

    out = args.output or args.log.with_suffix('.windup.png')
    fig.savefig(out, dpi=120)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
