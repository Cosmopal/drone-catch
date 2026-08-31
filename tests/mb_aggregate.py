import json, glob, os

for path in sorted(glob.glob("docs/cage_frames/iter2/logs/mb_ledger_*.jsonl")):
    rows = [json.loads(l) for l in open(path)]
    if len(rows) < 13:
        print(f"{os.path.basename(path)}: INCOMPLETE ({len(rows)}/13)")
        continue
    deltas = [r["delta"] for r in rows]
    dmin, dmax = min(deltas), max(deltas)
    if dmin > 0.3:
        verdict = "CONVERGENT POSITIVE"
    elif dmax < -0.3:
        verdict = "CONVERGENT NEGATIVE"
    else:
        verdict = "OVERLAPS 0 -> not distinguishable"
    print(f"{os.path.basename(path):50s} delta {dmin:+.2f}..{dmax:+.2f} cm -> {verdict}")
