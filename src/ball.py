"""Ball spawning and parabolic intercept prediction for catching."""
import numpy as np
import pybullet as p

G = 9.81


def spawn_ball(position, radius_urdf: str = "sphere_small.urdf", mass: float = 0.05):
    body = p.loadURDF(radius_urdf, basePosition=list(position), globalScaling=1.0)
    p.changeDynamics(body, -1, mass=mass, restitution=0.4,
                     linearDamping=0.05, angularDamping=0.05)
    return body


def predict_landing(pos, vel, target_z: float):
    """Solve z(t) = pz + vz*t - 0.5*g*t^2 = target_z for the later root.

    Returns (xy_at_target_z, time) or (None, None) if it never reaches it.
    """
    pz, vz = pos[2], vel[2]
    a, b, c = -0.5 * G, vz, pz - target_z
    disc = b * b - 4 * a * c
    if disc < 0:
        return None, None
    sq = np.sqrt(disc)
    t1 = (-b + sq) / (2 * a)
    t2 = (-b - sq) / (2 * a)
    candidates = [t for t in (t1, t2) if t > 1e-3]
    if not candidates:
        return None, None
    t = max(candidates)  # later (descending) root
    xy = np.array(pos[:2]) + np.array(vel[:2]) * t
    return xy, t


def state(body_id):
    pos, _ = p.getBasePositionAndOrientation(body_id)
    vel, _ = p.getBaseVelocity(body_id)
    return np.array(pos), np.array(vel)
