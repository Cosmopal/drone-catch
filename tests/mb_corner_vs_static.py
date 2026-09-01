"""Lead's escalated question: does the breaking corner (substep=8, contact
x0.33, seed=2) also break the §28/§29 Goal-1 static-study convergence
claims, or is the damage confined to M-B's marginal cells? Runs that
single corner config against:
  1. prb, n4, 2.5cm, finger (the §29 cell re-verified this run)
  2. prb, n4, 3.5cm, gap (a §29 null-direction cell)
  3. paired M-B null cells: prb_pulse vs prb and prb_active vs prb at
     n4-2.5cm-finger
No fixes, no retuning -- pure measurement."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cage_harness as ch

BASE_SS = ch.SUBSTEP
BASE_K = ch.CONTACT_STIFFNESS
BASE_C = ch.CONTACT_DAMPING

def set_corner():
    ch.SUBSTEP, ch.SIM_DT = 8, ch.DT / 8
    ch.CONTACT_STIFFNESS = BASE_K * 0.33
    ch.CONTACT_DAMPING = BASE_C * 0.33

def reset():
    ch.SUBSTEP, ch.SIM_DT = BASE_SS, ch.DT / BASE_SS
    ch.CONTACT_STIFFNESS, ch.CONTACT_DAMPING = BASE_K, BASE_C

rows = []

# 1+2: single-strategy static cells
for n, direction, offset, tag in [(4, "finger", 0.025, "S29_n4_finger_2.5cm"),
                                  (4, "gap", 0.035, "S29_n4_gap_3.5cm")]:
    set_corner()
    r = ch.run_cell("prb", n, offset, direction, quality=True, seed=2)
    reset()
    row = {"tag": tag, "strategy": "prb", "EM_g": r["escape_margin_g"],
          "PI_cm": r["pull_in"] * 100, "CF": r["n_contact_fingers"],
          "SY": r["symmetry"], "score": r["score"]}
    rows.append(row)
    print(f"{tag}: EM={row['EM_g']:.2f}g PI={row['PI_cm']:+.2f}cm "
         f"CF={row['CF']} SY={row['SY']:.2f} score={row['score']:.2f}")

# 3: paired M-B null cell
for strat in ["prb_pulse", "prb_active"]:
    set_corner()
    a = ch.run_cell(strat, 4, 0.025, "finger", quality=True, seed=2)["pull_in"] * 100
    b = ch.run_cell("prb", 4, 0.025, "finger", quality=True, seed=2)["pull_in"] * 100
    reset()
    row = {"tag": "MB_n4_finger_2.5cm_paired", "strategy": strat,
          "a_PI": a, "b_PI": b, "delta": a - b}
    rows.append(row)
    print(f"MB null n4-finger-2.5cm {strat}: a={a:+.2f} b={b:+.2f} delta={a-b:+.2f}")

out = "docs/cage_frames/iter2/logs/mb_corner_vs_static.jsonl"
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    for row in rows:
        f.write(json.dumps(row) + "\n")
print("WROTE", out)
