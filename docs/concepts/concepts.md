---
tags:
  - concept
---

# Concepts

A learning companion to the drone-catch project. Each note covers one
robotics / control / estimation concept we actually used: what it is, where
it shows up in this codebase, what our experiments taught us about it, and
what transfers to larger projects.

This is deliberately separate from [[iteration_findings|docs/iteration_findings.md]] (the
engineering narrative — what we tried, what broke, in what order). These
notes are the reference: read findings to see concepts colliding with
reality, read these to understand the concepts themselves.

Reading order roughly follows the control stack, bottom-up:

1. [[01-pd-control|PD control, natural frequency, damping]]
2. [[02-cascade-control|Cascade control & timescale separation]]
3. [[03-feedforward-and-gain-scheduling|Feedforward & gain scheduling]]
4. [[04-state-estimation-alpha-beta|State estimation: the alpha-beta filter]]
5. [[05-latency-compensation|Sensor latency & compensation]]
6. [[06-compliance-impedance|Compliance, impedance, and impulse]]
7. [[07-ballistic-prediction-interception|Ballistic prediction & interception]]
8. [[08-disturbance-modeling|Disturbance modeling (OU gusts)]]
9. [[09-grasping-caging-and-actuator-disturbance|Grasping, caging & actuator-induced disturbance]]
10. [[10-forward-inverse-kinematics-tracking|Forward/inverse kinematics & tracking vs sweeping]]
11. [[11-integral-control-and-windup|Integral control & windup]]
12. [[12-overactuation-thrust-vectoring-allocation|Over-actuation, thrust vectoring & control allocation]] *(design study)*
13. [[13-adaptive-underactuated-grasping|Adaptive & underactuated grasping]]

Conventions: equations are for unit mass unless stated; our sim runs at
240 Hz (`DT = 1/240 s`); the drone weighs 0.625 kg, the ball 0.065 kg,
the arm is 0.4 m.
