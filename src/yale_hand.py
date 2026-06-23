"""Faithful Yale-OpenHand-style UNDERACTUATED hand model (position-based tendon).

The point of an adaptive underactuated hand is the COUPLING — one actuator, many
joints, the hand self-distributes around the object wherever it is. The prior
`under` stand-in (cage_harness) drove each joint INDEPENDENTLY toward a deep
target, which is NOT a Yale hand: with equal independent targets there is no
differential, so for an off-center ball every finger closes the same amount.

This module models the two couplings that define the mechanism, using a
POSITION-based tendon (numerically stable — it sidesteps the constant-torque
ill-conditioning of a real tendon-tension model):

  (b) INTER-finger whiffletree: ONE actuator displacement `d_act` is the MEAN of
      the per-finger tendon displacements (a balance bar). A finger that contacts
      early stalls (caps its travel); to keep the mean at `d_act` the freed travel
      is fed to the fingers still free, so they close MORE. => self-distribution:
      near fingers close LESS, far fingers close MORE.

  (a) INTRA-finger tendon over pulleys: within a finger the tendon's flexion
      budget is shared across the 3 joints (distal-biased weights = the validated
      cage shape, so the distal tucks under). When the PROXIMAL contacts and
      stalls, its share is redistributed to the middle+distal — automatic
      wrap-and-tuck.

  (c) COMPLIANT joints: a soft position servo (low force cap + gentle gain) so a
      contacting joint YIELDS rather than crushing — the "return spring +
      flexure" behaviour, and the source of the conform-on-contact compliance.

Works on any body that exposes finger joints as lists of segment-joint indices
(`FixedGripper` in the static harness, `Drone` in the dynamic catch). Contact is
read from the live sim (`getContactPoints` vs the ball), so the differential is
driven by the ACTUAL object position, not an assumption.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np
import pybullet as p


@dataclass
class YaleConfig:
    # per-segment open (splayed) angles and max-flexion caps (absolute angle).
    open_pose: tuple = (-0.4, -0.2, 0.0)
    joint_caps: tuple = (1.5, 1.9, 1.9)       # how far each joint may curl
    # intra-finger tendon share weights (proximal, middle, distal) — distal-biased
    # so the tip tucks under (ratios of the validated cage flexion 0.9/1.2/1.3).
    weights: tuple = (0.9, 1.2, 1.3)
    # soft (compliant) position servo
    soft_force: float = 0.08                  # N.m yield-on-contact cap
    soft_kp: float = 0.6
    soft_kd: float = 0.8
    d_max: float = 3.6                         # actuator travel at full close
    contact_margin: float = 0.0


def open_hand(body_id, finger_joints, cfg: YaleConfig):
    """Reset every finger to the splayed open pose (tendon slack)."""
    for segs in finger_joints:
        for k, j in enumerate(segs):
            p.resetJointState(body_id, j, cfg.open_pose[k])


def _seg_in_contact(body_id, j, ball_id) -> bool:
    return len(p.getContactPoints(bodyA=body_id, bodyB=ball_id, linkIndexA=j)) > 0


def _finger_in_contact(body_id, segs, ball_id) -> bool:
    pts = p.getContactPoints(bodyA=body_id, bodyB=ball_id)
    links = {c[3] for c in pts}
    return any(j in links for j in segs)


def finger_flexions(body_id, finger_joints, cfg: YaleConfig):
    """Per-finger total flexion above the open pose — the self-distribution
    proof (off-center => these come out UNEQUAL)."""
    out = []
    open_sum = sum(cfg.open_pose)
    for segs in finger_joints:
        ang = [p.getJointState(body_id, j)[0] for j in segs]
        out.append(sum(ang) - open_sum)
    return out


def _command_finger(body_id, segs, angles, tgt_flex, ball_id, cfg: YaleConfig):
    """Distribute a finger's flexion budget `tgt_flex` (above open) across its 3
    joints: contacting joints HOLD (stall) and feed their share to the free
    joints, which split the remainder by the distal-biased weights."""
    flex_now = [angles[k] - cfg.open_pose[k] for k in range(len(segs))]
    jc = [_seg_in_contact(body_id, j, ball_id) for j in segs]
    fixed = sum(max(0.0, flex_now[k]) for k in range(len(segs)) if jc[k])
    free_k = [k for k in range(len(segs)) if not jc[k]]
    Wf = sum(cfg.weights[k] for k in free_k) or 1.0
    rem = max(0.0, tgt_flex - fixed)
    for k, j in enumerate(segs):
        if jc[k]:
            # contacting joint: maintain tendon TENSION — keep pulling toward the
            # cap so the soft servo presses with ~soft_force (stalled by contact).
            # This is what holds the ball (a position-hold would let it work
            # loose); the differential is preserved because the FREE joints/
            # fingers below still receive the redistributed travel.
            target = cfg.joint_caps[k]
        else:
            cap = cfg.joint_caps[k] - cfg.open_pose[k]
            give = min(cap, rem * cfg.weights[k] / Wf)
            target = cfg.open_pose[k] + give
        p.setJointMotorControl2(body_id, j, p.POSITION_CONTROL,
                                targetPosition=target, force=cfg.soft_force,
                                positionGain=cfg.soft_kp, velocityGain=cfg.soft_kd)


def actuate(body_id, finger_joints, ball_id, d_act, cfg: YaleConfig):
    """One control step of the underactuated close at actuator displacement
    `d_act` (ramp 0 -> cfg.d_max). Reads live contacts; applies the inter-finger
    whiffletree + intra-finger tendon couplings; commands the soft joint servos.
    """
    N = len(finger_joints)
    open_sum = sum(cfg.open_pose)
    angles = [[p.getJointState(body_id, j)[0] for j in segs] for segs in finger_joints]
    phi = [sum(a) - open_sum for a in angles]                  # flexion above open
    contact = [_finger_in_contact(body_id, segs, ball_id) for segs in finger_joints]

    # INTER-finger whiffletree: mean(per-finger travel) == d_act. Contacting
    # fingers cap their travel; the freed budget is split among the free fingers
    # (they close MORE) -> self-distribution around the object.
    budget = N * d_act
    used = sum(max(0.0, phi[i]) for i in range(N) if contact[i])
    free = [i for i in range(N) if not contact[i]]
    per_free = max(0.0, budget - used) / len(free) if free else 0.0

    for i, segs in enumerate(finger_joints):
        tgt = phi[i] if contact[i] else max(phi[i], per_free)
        _command_finger(body_id, segs, angles[i], tgt, ball_id, cfg)
