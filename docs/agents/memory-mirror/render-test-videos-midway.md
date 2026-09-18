---
name: render-test-videos-midway
description: "User wants intermediate test/experiment videos sent proactively, not just final results"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f1ce1eef-1e9e-4588-8d6f-776aa6e3fbf7
---

When iterating on experiments or catch/control tests that produce visible
behavior, render a short video of the intermediate result and send it with
SendUserFile *as I go* — don't wait until the full response is done.

**Why:** the user wants to guide the direction midway ("so that I can guide you
midway instead of waiting for your full response") rather than discover a wrong
turn at the end. They are highly engaged and have repeatedly improved the design
from watching the videos (spotted the arm↔body coupling, the fingers pushing the
ball out, the ceiling launch).

**How to apply:** after each test that has visual behavior, render it (the tests
take a `--runs-dir`; or a custom close-up like the finger-cam) and send it before
moving on. Prefer short, targeted views (finger-cam, before/after) over one long
clip. Relates to [[learning-objective-concept-docs]].
