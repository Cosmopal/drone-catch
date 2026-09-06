"""Decisive experiment: is the passive-close 'jam' at 4.5/5.0cm a real
physical effect, or an artifact of under-resolved numerics at the
harness's validated operating point (substep=4, contact x1)? Sweeps prb
ALONE (no pairing, no adaptive strategies) across substep {2,4,8,16} x
contact scale {0.33,1.0,3.0} at offsets {0.045, 0.050}. No rendering --
the numbers are the point. No tuning, no harness-default changes.
Resumable/chunkable: pass a start:end slice index into the 24-cell grid."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cage_harness as ch

CELLS = [(offset, ss, scale)
        for offset in [0.050, 0.045]
        for ss in [2, 4, 8, 16]
        for scale in [0.33, 1.0, 3.0]]

BASE_SS = ch.SUBSTEP
BASE_K = ch.CONTACT_STIFFNESS
BASE_C = ch.CONTACT_DAMPING

start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
end = int(sys.argv[2]) if len(sys.argv) > 2 else len(CELLS)

out = "docs/cage_frames/iter2/logs/mb_convergence_check.jsonl"
os.makedirs(os.path.dirname(out), exist_ok=True)

done_keys = set()
if os.path.exists(out):
    with open(out) as f:
        for line in f:
            r = json.loads(line)
            done_keys.add((r["offset_cm"], r["substep"], r["contact_scale"]))

for i in range(start, end):
    offset, ss, scale = CELLS[i]
    key = (offset * 100, ss, scale)
    if key in done_keys:
        print(f"idx {i}: SKIP (already done)")
        continue
    ch.SUBSTEP, ch.SIM_DT = ss, ch.DT / ss
    ch.CONTACT_STIFFNESS = BASE_K * scale
    ch.CONTACT_DAMPING = BASE_C * scale
    r = ch.run_cell("prb", 4, offset, "finger", quality=True)
    ch.SUBSTEP, ch.SIM_DT = BASE_SS, ch.DT / BASE_SS
    ch.CONTACT_STIFFNESS, ch.CONTACT_DAMPING = BASE_K, BASE_C
    row = {"idx": i, "offset_cm": offset * 100, "substep": ss, "contact_scale": scale,
          "pull_in_cm": r["pull_in"] * 100, "seat_off_cm": r["seat_off"] * 100,
          "symmetry": r["symmetry"], "escape_margin_g": r["escape_margin_g"],
          "flex": r["flexions"], "n_contact_fingers": r["n_contact_fingers"]}
    with open(out, "a") as f:
        f.write(json.dumps(row) + "\n")
        f.flush()
        os.fsync(f.fileno())
    print(f"idx {i} off={row['offset_cm']:.1f}cm ss={ss:2d} contact={scale:.2f} | "
         f"PI={row['pull_in_cm']:+.2f}cm SY={row['symmetry']:.2f} "
         f"EM={row['escape_margin_g']:.2f}g flex={['%.2f'%x for x in row['flex']]}")

print(f"CHUNK DONE [{start}:{end}]")
