"""Print post-run diagnostics: peak positions, intrusion into opponent area,
release vs actual velocity, evade brake distance.

Usage:
    python scripts/check_run.py                   # most recent runs/*.jsonl
    python scripts/check_run.py runs/foo.jsonl    # specific log
"""
import argparse
import glob
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log", nargs="?", type=Path, default=None)
    args = ap.parse_args()
    path = args.log or Path(sorted(glob.glob('runs/run_*.jsonl'))[-1])
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    print(f"file: {path}  ({len(rows)} samples)")

    # Phase summary
    from itertools import groupby
    print("\nphases:")
    for k, g in groupby(rows, key=lambda r: r['phase']):
        grp = list(g)
        print(f"  {k:18s} {grp[0]['t']:6.2f}->{grp[-1]['t']:6.2f}s ({len(grp)} samples)")

    # Throw moment: last throw_windup sample is just before release
    windup = [r for r in rows if r['phase'] == 'throw_windup']
    if windup:
        last = windup[-1]
        thr = last['thrower']
        print(f"\nat release (t={last['t']:.2f}):  thrower pos={[round(x,2) for x in thr['pos']]} "
              f"vel={[round(x,2) for x in thr['vel']]}")

    # Post-release thrower trajectory: did it overshoot into catcher's territory?
    post = [r for r in rows if r['t'] > windup[-1]['t']] if windup else rows
    if post:
        peak_x = max(post, key=lambda r: r['thrower']['pos'][0])
        peak_z = max(post, key=lambda r: r['thrower']['pos'][2])
        rel_x = windup[-1]['thrower']['pos'][0] if windup else 0
        brake_dist = peak_x['thrower']['pos'][0] - rel_x
        print(f"\nthrower POST-RELEASE peaks:")
        print(f"  peak x = {peak_x['thrower']['pos'][0]:+.2f} m  at t={peak_x['t']:.2f}  "
              f"(centerline=0; positive = poached into opponent area)")
        print(f"  peak z = {peak_z['thrower']['pos'][2]:.2f} m  at t={peak_z['t']:.2f}  "
              f"(ceiling=3.0)")
        print(f"  brake distance = {brake_dist:.2f} m from release_x={rel_x:.2f}")

    # Catcher: did it catch?
    caught = next((r for r in rows if r['phase'] == 'carry_to_cube'), None)
    cube = next((r for r in rows if r['phase'] == 'lift'), None)
    print(f"\noutcome:")
    print(f"  caught ball: {'YES at t=' + format(caught['t'], '.2f') if caught else 'NO'}")
    print(f"  picked cube: {'YES at t=' + format(cube['t'], '.2f') if cube else 'NO'}")
    print(f"  final phase: {rows[-1]['phase']}")


if __name__ == "__main__":
    main()
