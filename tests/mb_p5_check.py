"""M-B P5 check: score (26/26 caging) preserved for both adaptive strategies
at the same cells tested for paired-delta, at the default (shared, 150)
solver setting."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cage_harness as ch

CELLS = [
    (4, "finger", 0.015, "P1_1.5cm"),
    (4, "finger", 0.025, "P1_2.5cm"),
    (4, "gap",    0.035, "P2_gap_3.5cm"),
    (4, "finger", 0.050, "P3_5.0cm"),
    (8, "finger", 0.025, "P4_n8_2.5cm"),
]
STRATS = ["prb", "prb_pulse", "prb_active"]

print(f"{'cell':>16} {'strategy':>12} | {'score':>6} {'EM(g)':>7} {'CF':>3}")
for n, direction, offset, tag in CELLS:
    for strat in STRATS:
        r = ch.run_cell(strat, n, offset, direction, quality=True)
        print(f"{tag:>16} {strat:>12} | {r['score']:>6.2f} "
             f"{r['escape_margin_g']:>7.2f} {r['n_contact_fingers']:>3d}")
