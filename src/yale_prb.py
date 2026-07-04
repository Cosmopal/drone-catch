"""Faithful PSEUDO-RIGID-BODY (PRB) Yale-style underactuated hand (spec §2A).

This is the MECHANISM model that replaces the contact-reading stand-in in
`yale_hand.py`. The defining property of a Yale/SDM adaptive hand is that
self-distribution around the object EMERGES FROM PHYSICS — one actuator, a
constant-tension tendon, compliant (flexure) joints — with NO software reading
of where the object is. This module contains ZERO `getContactPoints` calls in
its close law: a finger stalls because the ball is physically in its way, and the
remaining fingers keep closing under the same tendon tension. That is the test of
faithfulness (§3 D9).

The two physical ingredients (the accepted PRB way to sim a flexure hand):

  1. FLEXURE JOINTS as torsional return springs. Each revolute joint is a
     pseudo-rigid-body approximation of a continuous flexure: a restoring torque
     τ_spring = −k·(θ − θ_rest) − c·θ̇ pulls the segment back toward its molded
     (open) shape and damps it. This regularizes the near-massless-finger dynamics
     that make a bare constant-torque tendon ill-conditioned (§25): the joint now
     has a defined, damped equilibrium instead of unbounded τ/I acceleration.

  2. CONSTANT-TENSION TENDON (the whiffletree, done right). ONE actuator variable
     `pull` (ramped 0→pull_max) adds the SAME closing torque to every finger
     (equal tension per branch — a floating balance bar equalizes force, NOT a
     rigid gear ratio; JOINT_GEAR would force equal MOTION, the opposite of a
     differential). Within a finger the tendon routes over pulleys, so the pull is
     distal-biased (`weights`) → the distal segment tucks under. Net joint torque:
         τ = −k·(θ − θ_rest) − c·θ̇ + w·pull
     A finger blocked by the ball reaches force balance early (low flex); a free
     finger reaches θ_eq = θ_rest + w·pull/k (high flex). => near fingers close
     LESS, far fingers close MORE, purely from force equalization. Optionally a
     physical floating balance-bar link (`use_balance_bar`) conserves total travel
     (a stronger, true-whiffletree coupling) — see `attach_balance_bar`.

STATED CEILING (be honest, §2A): this is a DISCRETIZED approximation on a sphere,
fixed-base ONLY (flexure joints are unstable on the floating drone, §15). It does
NOT model continuous flexure deformation, true tendon friction/creep, or SHAPE
adaptation (PyBullet has no continuous compliance/native tendons — that is a
MuJoCo project). We test the sphere only and make no shape-adaptation claim.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pybullet as p


@dataclass
class PRBConfig:
    # rest (molded/open) pose per segment — the flexure's zero-energy shape.
    rest_pose: tuple = (-0.4, -0.2, 0.0)
    # torsional return-spring stiffness k (N·m/rad) and damping c (N·m·s/rad),
    # per segment. Chosen k = pull so a FREE finger's force-balance equilibrium
    # rest + w·pull/k lands exactly at the validated cage pose (whose per-joint
    # flexion ≈ the weights 0.9/1.2/1.3) — verified: a free finger settles at
    # [0.5,1.0,1.3]. c ≈ mild overdamping at the ×50-regularized inertia.
    k_spring: tuple = (0.25, 0.25, 0.25)
    c_damp: tuple = (0.003, 0.003, 0.003)
    # intra-finger tendon pulley weights (distal-biased → tip tucks under).
    weights: tuple = (0.9, 1.2, 1.3)
    pull_max: float = 0.25          # actuator tendon tension at full close (N·m)
    inertia_scale: float = 50.0     # PRB numerical regularization (see regularize_inertia)
    joint_effort_cap: float = 0.6   # URDF effort limit (clamp the applied torque)


def finger_flexions(body_id, finger_joints, cfg: PRBConfig):
    """Per-finger total flexion above the rest pose (rad). Off-center → these come
    out UNEQUAL (the self-distribution signature), and it must be measured, never
    commanded."""
    rest_sum = sum(cfg.rest_pose)
    out = []
    for segs in finger_joints:
        ang = [p.getJointState(body_id, j)[0] for j in segs]
        out.append(sum(ang) - rest_sum)
    return out


def regularize_inertia(body_id, finger_links, scale: float = 50.0):
    """PRB NUMERICAL REGULARIZATION (a stated discretization choice, part of the
    model's ceiling). The bare finger links have inertia ~3e-6 kg·m²; under pure
    TORQUE_CONTROL that makes τ/I ~2e4 rad/s², so a joint blows past the velocity
    cap in one 1/960 step and vibrates without net motion (the §25 wall at the
    JOINT level). Scaling the rotational inertia ×`scale` fixes the stiff-ODE
    instability — the finger then closes smoothly to its force-balance equilibrium
    (verified: a free finger settles EXACTLY at the cage pose). This is physically
    defensible (a real molded flexure has more rotational inertia than an idealized
    thin box) and is the standard way to condition near-massless links in a rigid-
    body sim; mass is unchanged. WITHOUT it the faithful tendon is not viable in
    PyBullet on these fingers — which is itself the honest ceiling if one refuses
    the regularization."""
    for link in finger_links:
        dyn = p.getDynamicsInfo(body_id, link)
        I = dyn[2]
        p.changeDynamics(body_id, link,
                         localInertiaDiagonal=[I[0] * scale, I[1] * scale,
                                               I[2] * scale])


def set_open(body_id, finger_joints, cfg: PRBConfig):
    """Reset every finger to the molded rest pose (tendon slack)."""
    for segs in finger_joints:
        for k, j in enumerate(segs):
            p.resetJointState(body_id, j, cfg.rest_pose[k])


def prep(body_id, finger_joints):
    """Free the default position motors so pure TORQUE_CONTROL governs the joints
    (the spring + tendon torques are applied every step)."""
    for segs in finger_joints:
        for j in segs:
            p.setJointMotorControl2(body_id, j, p.VELOCITY_CONTROL, force=0.0)


def actuate(body_id, finger_joints, pull, cfg: PRBConfig):
    """One control step of the PHYSICAL close at tendon tension `pull` (ramp
    0→cfg.pull_max). Applies, per joint, the flexure return spring + the equal
    (distal-weighted) tendon tension as a TORQUE. NO contact is read — the ball
    stalls the fingers mechanically. This is the whole point.
    """
    cap = cfg.joint_effort_cap
    for segs in finger_joints:
        for k, j in enumerate(segs):
            th, thd = p.getJointState(body_id, j)[:2]
            tau = (-cfg.k_spring[k] * (th - cfg.rest_pose[k])
                   - cfg.c_damp[k] * thd
                   + cfg.weights[k] * pull)
            tau = float(np.clip(tau, -cap, cap))
            p.setJointMotorControl2(body_id, j, p.TORQUE_CONTROL, force=tau)
