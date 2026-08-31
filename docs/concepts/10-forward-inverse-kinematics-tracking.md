---
tags:
  - concept
---

# Forward/inverse kinematics & tracking vs. sweeping

## What it is

**Forward kinematics (FK)**: joint angles → end-effector (EE) pose. A
deterministic geometry calculation — chain the link transforms.

**Inverse kinematics (IK)**: desired EE pose → joint angles. The inverse
problem, and the interesting one: it can have zero solutions (target out of
reach), one (at full stretch), two (elbow-up vs elbow-down), or infinitely
many (redundant arms with more DOF than the task needs).

Our arm is a **planar 2R manipulator**: two revolute joints, both about
body ±y, two equal 0.2 m links, operating in the body xz-plane. For equal
links the IK is closed-form:

```
r = |target - shoulder|              # must be ≤ L1+L2 to be reachable
θ2 = 2·acos(r / (L1+L2))             # elbow bend; ± gives the two branches
θ1 = atan2(x, -z) + θ2/2             # shoulder
```

We take the elbow-forward branch (θ2 ≥ 0) and cap θ2 below the fold that
would put the forearm above the shoulder (the inverted-pendulum trap a
joint-PD can't hold).

**DOF vs. task dimension** is the load-bearing idea. 1 joint traces the EE
along a 1-D *curve* (an arc). 2 joints fill a 2-D *region* (a disk). To put
the EE at an arbitrary point in a plane you need ≥2 DOF; with exactly 2 you
get isolated solutions, with 3+ you get a null-space to exploit (obstacle
avoidance, posture). Our catch lives in a plane → 2 DOF is the minimum that
turns "sweep through one point" into "reach any point."

## Where we use it

`src/arm_kinematics.py` (`fk`, `fk_body`, `ik`, `ik_body`),
`tests/elbow_catch_solo.py` (M7 — IK-tracking catch). Earlier work locked the
elbow at 0 and used the shoulder as a single rod (`arm_catch_solo`,
`finger_catch_solo`); the EE was confined to an arc.

## What we learned here

- **Verify FK/IK against the physics engine, not your algebra.** Setting
  joints and comparing `getLinkState` to our `fk` gave 0.0 mm error and — more
  usefully — caught the elbow *sign* (the forearm's absolute angle is
  θ1 − θ2, because the elbow axis opposes the shoulder's). Sign bugs in
  kinematics are silent and pervasive; a round-trip test kills them.
- **The DOF count was the whole game for catching.** With 1 DOF the cup
  swept an arc *through* the ball at one instant — a knife-edge that left a
  7–10 cm miss. With 2 DOF the cup *servos onto* the ball and tracks it; the
  miss dropped to ~1 cm at the design point. Same arm, same ball — one more
  joint changed a tangency problem into a tracking problem.
- **Tracking a moving target needs velocity, not just position.** Getting the
  EE *to* where the ball *is* isn't enough if the ball blows through; the EE
  must move *with* the ball (match velocity) for the gripper to have time to
  close. Position-only IK tracking caught the easy cases and missed the fast
  ones. (This is the same lesson as latency compensation, [[05-latency-compensation|§05]], one layer up:
  aim where the target *will be*.)
- **Redundancy resolution / branch choice matters.** We always pick the
  elbow-forward branch and cap the fold; the other branch is reachable but
  unstable for our PD. Real arms choose branches for joint limits, obstacles,
  and continuity (don't flip branches mid-trajectory — the arm would slam
  across).

## For larger projects

- Closed-form IK exists for many low-DOF arms and is worth deriving (fast,
  exact, no solver). For 6+ DOF or awkward geometries, numeric IK
  (Jacobian/optimization) is standard — but the same reachability, branch,
  and redundancy questions apply.
- For interception/manipulation of *moving* things, plan in **task space**
  with velocity (servo the EE to a moving target with feedforward), and let
  IK (or the Jacobian transpose/pseudo-inverse) map it to joints — don't hand-
  choreograph joint trajectories.
- Always know your **DOF-vs-task-dimension** budget: it tells you up front
  whether a motion is even possible, and whether you have redundancy to spend
  on secondary goals.
