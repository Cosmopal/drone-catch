# Pre-registration — M-B adaptive re-centering (Goal 2, iteration 2)

> Written BEFORE any M-B code or run (loop-spec §0.3). Predictions are anchored in
> the Yale OpenHand / underactuated-grasping literature and in our own §29 passive
> baseline (PRB pull-in +1.3..+3.1 cm, finger direction, n4–n6). NOTE: written
> while the regression gates were still UNCONFIRMED (environment blocker — no
> `robots` env on this machine); no M-B run existed when this was committed.

**Candidate strategies** (both additive, opt-in flags in `cage_harness.py`):
- `prb_pulse` — mechanism-honest ACTIVE use of the faithful PRB hand: a tendon
  tension *schedule* (close → partial release → re-close, ≥2 cycles), zero contact
  reading. The constant-tension tendon redistributes on each re-close.
- `prb_active` — SENSOR-BASED: reads per-finger contact booleans + joint angles
  (stands in for commodity finger contact switches + joint encoders), estimates
  the ball bearing from the flexion deficit, and biases per-finger tendon tension
  toward the blocked finger(s). Labeled sensor-based, never passive-mechanical.

## Predictions

**P1 — Finger direction, n4–n6, offsets 1.5–3.5 cm: active adds ≈ nothing.**
The passive PRB close already seats to 0.15–0.38 cm residual (§29) — there is
almost no re-centering left to win. Literature (Dollar & Howe SDM; Yale OpenHand)
attributes re-centering to the passive differential itself; active re-grasping
(regrasp/wiggle literature) helps when the first grasp jams, which our frames do
not show here. Predict paired delta (active − prb) OVERLAPS 0 in these cells.
*Falsifier:* `--paired` delta convergent-positive > 0.3 cm in any such cell.
*Confidence: 0.75.*

**P2 — Gap direction: neither variant re-centers.** The §29 null is geometric —
no finger sits behind the ball, so no tension schedule or tension bias can
generate a centering force component; squeezing the two straddling fingers gives
normals ≈ through the ball center (no net lateral push). Predict pull-in sign NOT
stable and paired delta vs `prb` OVERLAPS 0 for both variants.
*Falsifier:* convergent-positive gap-direction pull-in (or delta vs prb) at any
offset ≥2.5 cm. A P2 violation would be the interesting anomaly → investigate the
wedge/friction mechanism in frames before reporting.
*Confidence: 0.6 (the wedge effect of `prb_active` is the genuine unknown).*

**P3 — Large finger-direction offsets (5 cm): the one place active should help.**
At 5 cm the passive close leaves 3.04 cm residual with an asymmetric stalled
wrap (§29 boundary frame) — a friction-locked partial grasp, exactly the case the
regrasp literature says a release-re-close fixes. Predict `prb_pulse` (and/or
`prb_active`) convergently improves pull-in vs `prb` at n4-finger-5.0 cm.
Mind the caveat: gravity is OFF in this harness, so a released ball has no
restoring force — the gain must come from the fingers themselves, which caps it.
*Falsifier:* paired delta vs prb OVERLAPS 0 (or negative) at n4-finger-5.0 cm.
*Confidence: 0.5 (the gravity-off regime may suppress the regrasp benefit).*

**P4 — n8: no active re-centering.** Per-finger travel budget is too small for
any differential, active or not (§29 n8 null). Predict same null for both
variants (still cages, score 26/26). *Falsifier:* convergent-positive pull-in at
n8. *Confidence: 0.8.*

**P5 — No robustness regression.** Both variants keep the PRB hand's binary
caging (score 26/26, EM ≥10 g, finger direction) wherever passive prb cages; the
pulse's release phase does not lose the ball (gravity-off: nothing pulls it out).
*Falsifier:* any caged→escaped flip vs prb in the §29-caged envelope.
*Confidence: 0.7.*

Verdicts come from the standard gates only: `--converge` tables + `--paired`
deltas + frames. These priors direct attention; they decide nothing.
