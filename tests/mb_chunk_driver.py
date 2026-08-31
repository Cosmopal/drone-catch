"""M-B: chunkable paired-delta runner. Replicates cage_harness.paired_converge's
EXACT perturbation set (same 13 variations: substep 2/4/8, contact x0.33/x3,
seed 1/2/3, solver_iters 50/100/150/200/300 baseline-omitted-since-default-is-
run-separately) via run_cell directly (the unmodified public API -- does not
touch/retool cage_harness.py's own paired_converge), so a cell's 26 runs can
be split into safe sub-600s chunks without losing rigor. Appends+fsyncs one
JSON line per completed PAIR to a resumable ledger; a final aggregation step
reads the ledger and prints the same verdict format as paired_converge."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import cage_harness as ch

PERTURBATIONS = (
    [("substep", ss) for ss in (2, 4, 8)]
    + [("contact", sc) for sc in (0.33, 3.0)]
    + [("seed", sd) for sd in (1, 2, 3)]
    + [("solver_iters", it) for it in (50, 100, 150, 200, 300)]
)  # 13 total, matches paired_converge exactly


def apply_perturbation(kind, val):
    if kind == "substep":
        ch.SUBSTEP, ch.SIM_DT = val, ch.DT / val
        return {}
    if kind == "contact":
        ch.CONTACT_STIFFNESS, ch.CONTACT_DAMPING = ch._BASE_K * val, ch._BASE_C * val
        return {}
    if kind == "seed":
        return {"seed": val}
    if kind == "solver_iters":
        ch.SOLVER_ITERS = val
        return {}
    raise ValueError(kind)


def reset_defaults():
    ch.SUBSTEP, ch.SIM_DT = ch._BASE_SS, ch.DT / ch._BASE_SS
    ch.CONTACT_STIFFNESS, ch.CONTACT_DAMPING = ch._BASE_K, ch._BASE_C
    ch.SOLVER_ITERS = ch._BASE_ITERS


# stash bases once (module import time) so repeated invocations across
# process runs always reset to the SAME baseline values.
ch._BASE_SS = ch.SUBSTEP
ch._BASE_K = ch.CONTACT_STIFFNESS
ch._BASE_C = ch.CONTACT_DAMPING
ch._BASE_ITERS = ch.SOLVER_ITERS


def main():
    strat_a = sys.argv[1]
    n = int(sys.argv[2])
    offset = float(sys.argv[3])
    direction = sys.argv[4]
    tag = sys.argv[5]
    start_idx = int(sys.argv[6])
    end_idx = int(sys.argv[7])   # exclusive

    ledger = f"docs/cage_frames/iter2/logs/mb_ledger_{tag}_{strat_a}.jsonl"
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    done_idx = set()
    if os.path.exists(ledger):
        with open(ledger) as f:
            for line in f:
                done_idx.add(json.loads(line)["idx"])

    for idx in range(start_idx, end_idx):
        if idx in done_idx:
            print(f"idx {idx}: SKIP (already done)")
            continue
        kind, val = PERTURBATIONS[idx]
        reset_defaults()
        kw = apply_perturbation(kind, val)
        t0 = time.time()
        a = ch.run_cell(strat_a, n, offset, direction, quality=True, **kw)["pull_in"] * 100
        b = ch.run_cell("prb", n, offset, direction, quality=True, **kw)["pull_in"] * 100
        reset_defaults()
        row = {"idx": idx, "kind": kind, "val": val, "a_pull_in": a, "b_pull_in": b,
              "delta": a - b, "elapsed_s": time.time() - t0}
        with open(ledger, "a") as f:
            f.write(json.dumps(row) + "\n")
            f.flush()
            os.fsync(f.fileno())
        print(f"idx {idx} ({kind}={val}): a={a:+.2f} b={b:+.2f} delta={a-b:+.2f} "
             f"({row['elapsed_s']:.1f}s)")

    print(f"CHUNK DONE [{start_idx}:{end_idx}]")


if __name__ == "__main__":
    main()
