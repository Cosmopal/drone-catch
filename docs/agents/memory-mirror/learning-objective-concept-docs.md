---
name: learning-objective-concept-docs
description: "User's key project goal — accrue robotics/control/estimation learning; maintain docs/concepts/ collection as we go"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f1ce1eef-1e9e-4588-8d6f-776aa6e3fbf7
---

An important objective of the drone-catch project is for the user to accrue transferable learning (robotics, estimation, control theory) for larger future projects — not just to make the demo work.

**Why:** The user said so explicitly (2026-06-13): "an important objective of this project is for us to accrue learning for larger projects... help me learn the concepts of robotics, estimation and control that we are experimenting with along the way."

**How to apply:**
- Maintain `docs/concepts/` — one short markdown per concept (what it is / where we use it / what we learned / notes for larger projects). Add a file whenever a new concept enters the work (e.g., Kalman filter, quaternion attitude control, IK, MPC).
- When introducing a technique in conversation, briefly explain the concept, not just the code change.
- Prefer experiments that teach (e.g., parameter sweeps showing *why* something matters) when cheap.
- Engineering narrative lives in `docs/iteration_findings.md`; conceptual reference lives in `docs/concepts/`.
