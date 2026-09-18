# Memory index

- [Learning objective & concept docs](learning-objective-concept-docs.md) — project exists to accrue robotics/control learning; maintain docs/concepts/, explain concepts as we use them
- [Render test videos midway](render-test-videos-midway.md) — send intermediate test videos proactively so the user can steer before the full response
- [Examine frames, not just metrics](examine-frames-not-just-metrics.md) — for physics-sim/contact/geometry, look at frames; scalar success metrics hide failure modes
- [General detectors, not failure maps](autonomy-general-detectors-not-failure-maps.md) — for blue-sky autonomy, install domain-general failure detectors + a ratchet; don't pre-enumerate specific failures
- [Engineering, not science](framing-engineering-not-science.md) — project is plug+tune known robotics principles & characterize practical limits, not novel-algorithm research
- [Mechanism fidelity, not behavioral stand-in](mechanism-fidelity-not-behavioral-standin.md) — evaluating a mechanism needs a faithful physical model, not a software abstraction on unrelated geometry; prove it's real before scoring
- [conda run log buffering](conda-run-log-buffering.md) — committed background-run logs stay empty until exit unless you use `conda run --no-capture-output` + `python -u`
- [Grasp iteration-2 state](grasp-iter2-state.md) — `grasp-iter2` branch has the study; `main` is current (tvp ff'd in + core-code/docs delta ported); Goal 2 next
