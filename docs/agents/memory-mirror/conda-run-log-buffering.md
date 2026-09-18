---
name: conda-run-log-buffering
description: Committed background-run logs stay empty until process exit unless you use conda run --no-capture-output
metadata: 
  node_type: memory
  type: project
  originSessionId: 2809acdf-6cf1-469a-90e6-84f65a23096b
---

When running long PyBullet grids/sweeps in the background and teeing to a COMMITTED
log (for shutdown-safety / incremental commits), `conda run -n robots python ... > log.txt`
BUFFERS the child's stdout — the log stays empty until the process exits, so a
hibernation/shutdown mid-run loses everything (this bit us in iteration-2, and again
in the task-7 faithful-Yale re-score).

**Fix:** `conda run --no-capture-output -n robots python -u ...` (both flags: `-u`
unbuffers Python, `--no-capture-output` stops conda from capturing/buffering). Then
committed logs fill line-by-line and you can commit each stage as it lands.

Also: killing a background `bash driver.sh` loop needs killing the driver script
PID, not just the current `conda run` child — the loop otherwise spawns the next cell.

**Why:** the cage-study workflow (docs/cage_frames/iter2/logs/) demands every grid
number live in a committed log (provenance ratchet). Buffered logs defeat that and
defeat shutdown-safety. See docs/iteration_findings.md §28 note ("trust the *.out
stdout, not the tee'd *.txt") — this is the actual fix for that symptom.

**How to apply:** for any `run_in_background` PyBullet grid whose output must be a
committed artifact, use `--no-capture-output` + `python -u`, tee to the committed
path, and commit incrementally per stage. Related: [[examine-frames-not-just-metrics]].
