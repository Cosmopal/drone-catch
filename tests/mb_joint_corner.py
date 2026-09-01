"""M-B task 4: joint (combined, not one-at-a-time) worst-case perturbation
corners at the two headline cells, to check the OAT convergence battery
isn't hiding a joint-failure mode. Combines substep + contact + seed
simultaneously (drawing from the OAT-weakest values already observed per
axis at each cell) via run_cell directly."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cage_harness as ch

strat = sys.argv[1]
n = int(sys.argv[2])
offset = float(sys.argv[3])
direction = sys.argv[4]
tag = sys.argv[5]
substep = int(sys.argv[6])
contact_scale = float(sys.argv[7])
seed = int(sys.argv[8])
corner_label = sys.argv[9]

ch._BASE_SS = ch.SUBSTEP
ch._BASE_K = ch.CONTACT_STIFFNESS
ch._BASE_C = ch.CONTACT_DAMPING

ledger = f"docs/cage_frames/iter2/logs/mb_corner_{tag}_{strat}.jsonl"
os.makedirs(os.path.dirname(ledger), exist_ok=True)

ch.SUBSTEP, ch.SIM_DT = substep, ch.DT / substep
ch.CONTACT_STIFFNESS = ch._BASE_K * contact_scale
ch.CONTACT_DAMPING = ch._BASE_C * contact_scale

t0 = time.time()
a = ch.run_cell(strat, n, offset, direction, quality=True, seed=seed)["pull_in"] * 100
b = ch.run_cell("prb", n, offset, direction, quality=True, seed=seed)["pull_in"] * 100

ch.SUBSTEP, ch.SIM_DT = ch._BASE_SS, ch.DT / ch._BASE_SS
ch.CONTACT_STIFFNESS, ch.CONTACT_DAMPING = ch._BASE_K, ch._BASE_C

row = {"corner": corner_label, "substep": substep, "contact_scale": contact_scale,
      "seed": seed, "a_pull_in": a, "b_pull_in": b, "delta": a - b,
      "elapsed_s": time.time() - t0}
with open(ledger, "a") as f:
    f.write(json.dumps(row) + "\n")
    f.flush()
    os.fsync(f.fileno())
print(f"{corner_label}: a={a:+.2f} b={b:+.2f} delta={a-b:+.2f} ({row['elapsed_s']:.1f}s)")
