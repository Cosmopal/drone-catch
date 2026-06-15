# Concepts

A learning companion to the drone-catch project. Each note covers one
robotics / control / estimation concept we actually used: what it is, where
it shows up in this codebase, what our experiments taught us about it, and
what transfers to larger projects.

This is deliberately separate from `docs/iteration_findings.md` (the
engineering narrative — what we tried, what broke, in what order). These
notes are the reference: read findings to see concepts colliding with
reality, read these to understand the concepts themselves.

Reading order roughly follows the control stack, bottom-up:

1. [PD control, natural frequency, damping](01-pd-control.md)
2. [Cascade control & timescale separation](02-cascade-control.md)
3. [Feedforward & gain scheduling](03-feedforward-and-gain-scheduling.md)
4. [State estimation: the alpha-beta filter](04-state-estimation-alpha-beta.md)
5. [Sensor latency & compensation](05-latency-compensation.md)
6. [Compliance, impedance, and impulse](06-compliance-impedance.md)
7. [Ballistic prediction & interception](07-ballistic-prediction-interception.md)
8. [Disturbance modeling (OU gusts)](08-disturbance-modeling.md)
9. [Grasping, caging & actuator-induced disturbance](09-grasping-caging-and-actuator-disturbance.md)

Conventions: equations are for unit mass unless stated; our sim runs at
240 Hz (`DT = 1/240 s`); the drone weighs 0.625 kg, the ball 0.065 kg,
the arm is 0.4 m.
