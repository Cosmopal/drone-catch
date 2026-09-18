---
name: examine-frames-not-just-metrics
description: "For physics-sim / geometric / contact behavior, extract and visually examine frames; don't trust scalar success metrics alone"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d155edbe-7048-4315-a7e7-ea544c31734d
---

When debugging physics-sim behavior (catches, contacts, grasps, collisions,
geometry), scalar metrics (`held=True`, `min_dist`, contact-count) compress away
the failure MODE. In the drone-catch M9 work the user caught the load-bearing
bugs by visually examining video frames — the cup pointing the wrong way so the
ball hit a finger, and the cage pinching an off-center ball and squeezing it
out — both of which the metrics reported as "success" or a generic "miss."

**Why:** in a physics sim the geometry and contact dynamics decide the outcome,
and a binary "success" can be one perturbation from failure. Rendering a video
as an *output for the user* is not the same as examining it as an *input for my
own analysis*.

**How to apply:** proactively extract frames (imageio/ffmpeg → PNG) and Read
them when debugging geometric/contact behavior — I have image input, use it.
Distrust binary success metrics on a physical interaction: verify *how* it
succeeded, not just *if*. And note the limit honestly — even with frame access,
the user's at-a-glance motion perception still caught modes I missed, so keep a
human (or a deliberate frame-by-frame pass) in the loop for physical-sim
verification. Recorded as a project finding in `docs/iteration_findings.md` §23.
Relates to [[render-test-videos-midway]].
