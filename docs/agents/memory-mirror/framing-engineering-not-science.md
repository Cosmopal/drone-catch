---
name: framing-engineering-not-science
description: "The drone-catch project is engineering empiricism (plug+tune known robotics principles, characterize practical limits), not novel-algorithm science"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d155edbe-7048-4315-a7e7-ea544c31734d
---

The user's framing of what this project is, and is not (stated 2026-06-30). The
robotics principles are well-established and textbook (Lee SO(3) attitude control,
planar 2R IK, compliant/underactuated grasping, ballistic prediction). The work is
**correct selection + tuning of the right known methods + building expertise of their
practical limitations** — NOT inventing new algorithms, and not a scientific study.

**Why:** it sets the right altitude for how to work and what to record. Don't frame
tasks as "discovering" things or reach for novel-algorithm research; frame them as
engineering characterization. The user pushed back when I over-reached with a
"scientific method / discover algorithms" framing.

**How to apply:** the scientific-method machinery (hypothesis → falsification →
convergence check) is in service of *engineering characterization* — "does this known
method hold in my regime, where is its breaking point?" Record **characterizations**,
not discoveries: the practical envelope of each method here (where it works/breaks,
tuned constants, and the validity conditions of the MEASUREMENT used to certify it).
`iteration_findings.md` is already this logbook; the missing first-class dimension is
measurement validity. The hard, valuable part is the practical-limitations expertise,
which is exactly the accreting failure map in [[autonomy-general-detectors-not-failure-maps]].
