---
name: mechanism-fidelity-not-behavioral-standin
description: "Evaluating a mechanism requires a faithful physical model, not a behavioral abstraction on unrelated geometry"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2809acdf-6cf1-469a-90e6-84f65a23096b
---

When a study claims to evaluate a physical **mechanism** (an underactuated hand, a
tendon/whiffletree, a compliant flexure, a controller principle), a **behavioral/
software abstraction bolted onto unrelated geometry does NOT count as testing that
mechanism** — even if it reproduces the mechanism's *behavior*. The verdict from such
a stand-in is unreliable (it may reflect a bad model, not the mechanism).

The user reopened a **fully reviewer-approved Goal 1** over exactly this: the scored
"Yale hand" (`src/yale_hand.py`) was a contact-reading position-budget redistributor
(reads `getContactPoints`, mean-splits a software "flexion budget") on the rigid
caging gripper, and its docstring falsely said "Faithful." The "Yale ties fixed"
finding was therefore invalid.

**Why:** the whole point of an engineering characterization is to test the *real*
principle. A stand-in that happens to behave similarly can confidently reject (or
accept) the wrong answer — the falsifiability trap ([[examine-frames-not-just-metrics]]
is the sibling for metrics; this is the same failure for *mechanisms*).

**How to apply:**
- Build the faithful model the accepted way (e.g. pseudo-rigid-body: multi-segment
  revolute flexure chains + per-joint torsional return springs; a **physical** tendon
  coupling via `createConstraint(JOINT_GEAR)` + a floating whiffletree — NOT a
  contact-reading algorithm; compliant pads via `changeDynamics`).
- **Prove the model is real before scoring it**, with frames: continuous conformance,
  and self-distribution emerging from the *physical coupling* (not from reading
  contacts).
- State the model's **ceiling** honestly (a discretized approximation) and what the
  tool cannot capture (PyBullet has no continuous compliance / native tendons →
  shape-adaptation is a MuJoCo project, out of scope).
- Made this a **standing reviewer detector (D9 mechanism-fidelity)** in the grasp
  iteration-2 spec; it's a ratchet, applies to any mechanism claim from here on.
- Fits [[framing-engineering-not-science]]: characterize the real principle's limits,
  don't accept a convenient proxy for it.
