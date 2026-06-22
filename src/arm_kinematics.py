"""Planar forward/inverse kinematics for the 2-link arm.

Both joints rotate about body ±y, so the whole arm lives in the body
xz-plane (the sagittal plane). Angles are measured from straight-down:

  - shoulder θ1: upper-arm direction = (sin θ1, -cos θ1)   [x, z]
  - elbow θ2:    forearm direction   = (sin(θ1-θ2), -cos(θ1-θ2))
    (elbow axis is +y, opposite the shoulder's -y, so the forearm's
    absolute angle is θ1 - θ2; θ2=0 extended, θ2=π folded back/up.)

FK gives the end-effector position relative to the shoulder pivot. With
1-DOF (θ2=0) this reduces to the single-rod model the rest of the code uses:
EE = (L·sin θ1, -L·cos θ1) with L = L1+L2.

Verified against PyBullet in tests (see verify_kinematics()).
"""
from __future__ import annotations
import math
from typing import Optional

L1 = 0.20   # upper_arm length (matches URDF)
L2 = 0.20   # forearm length
REACH = L1 + L2

# Shoulder pivot in body frame (x, z): top-of-base mount. Calibrated against
# PyBullet (j_shoulder_mount at +0.030, shoulder_joint origin -0.010).
SHOULDER_X = 0.0
SHOULDER_Z = 0.020


def fk(theta1: float, theta2: float) -> tuple[float, float]:
    """End-effector (x, z) relative to the SHOULDER pivot, body frame."""
    a1 = theta1            # upper-arm absolute angle from -z
    a2 = theta1 - theta2   # forearm absolute angle from -z
    x = L1 * math.sin(a1) + L2 * math.sin(a2)
    z = -L1 * math.cos(a1) - L2 * math.cos(a2)
    return x, z


def fk_body(theta1: float, theta2: float) -> tuple[float, float]:
    """End-effector (x, z) relative to the BODY origin."""
    x, z = fk(theta1, theta2)
    return SHOULDER_X + x, SHOULDER_Z + z


def ik(x: float, z: float, elbow_max: float = 1.7) -> Optional[tuple[float, float]]:
    """Inverse kinematics: (θ1, θ2) placing the EE at (x, z) relative to the
    SHOULDER pivot. Returns None if unreachable.

    Equal-length links → r = 2L·cos(θ2/2). We take the θ2 ≥ 0 branch (elbow
    bends forward/down, within the URDF limit [0, π]) and cap it at
    `elbow_max` to stay clear of the inverted-pendulum trap (folded arm above
    the shoulder, which joint-motor PD can't stabilize).
    """
    r = math.hypot(x, z)
    if r > REACH or r < 1e-6:
        return None
    h = math.acos(min(1.0, r / REACH))   # = θ2 / 2
    theta2 = 2.0 * h
    if theta2 > elbow_max:
        return None                      # would fold too far
    m = math.atan2(x, -z)                # bisector angle of the two links
    theta1 = m + h
    return theta1, theta2


def ik_body(x: float, z: float, **kw) -> Optional[tuple[float, float]]:
    """IK for an EE target given relative to the BODY origin."""
    return ik(x - SHOULDER_X, z - SHOULDER_Z, **kw)


def jacobian(theta1: float, theta2: float, le: float = L2):
    """2×2 Jacobian J of the arm TIP position (x, z) w.r.t. (θ1, θ2), body
    sagittal plane. `le` is the effective second-link length to the controlled
    point: L2 for the EE, or L2+cup_depth to control the cup center.

    tip = (L1·sinθ1 + le·sin(θ1−θ2),  −L1·cosθ1 − le·cos(θ1−θ2))
    Returns [[∂x/∂θ1, ∂x/∂θ2], [∂z/∂θ1, ∂z/∂θ2]].
    """
    a2 = theta1 - theta2
    c1, s1 = math.cos(theta1), math.sin(theta1)
    c2, s2 = math.cos(a2), math.sin(a2)
    return [[L1 * c1 + le * c2, -le * c2],
            [L1 * s1 + le * s2, -le * s2]]


def ik_velocity(theta1, theta2, vx, vz, le=L2, damp=1e-3):
    """Joint velocities (θ̇1, θ̇2) that move the arm tip at velocity (vx, vz)
    in the body sagittal plane, at pose (θ1, θ2). Damped-least-squares inverse
    of the Jacobian so it stays finite near singularities (full extension).
    """
    J = jacobian(theta1, theta2, le)
    a, b, c, d = J[0][0], J[0][1], J[1][0], J[1][1]
    # (Jᵀ J + λI)⁻¹ Jᵀ v  — damped least squares
    m11 = a * a + c * c + damp
    m12 = a * b + c * d
    m22 = b * b + d * d + damp
    det = m11 * m22 - m12 * m12
    if abs(det) < 1e-12:
        return 0.0, 0.0
    # Jᵀ v
    jtv1 = a * vx + c * vz
    jtv2 = b * vx + d * vz
    # inv(M) @ Jᵀv
    th1d = (m22 * jtv1 - m12 * jtv2) / det
    th2d = (-m12 * jtv1 + m11 * jtv2) / det
    return th1d, th2d
