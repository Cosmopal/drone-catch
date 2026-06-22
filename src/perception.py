"""Ball perception models: distance-scaled measurement noise + sensor
latency (`BallPerception`), and a latency-compensating ballistic estimator
(`BallEstimator`).

Split out of main.py so isolation tests can run the same sensing model as
the full demo.
"""
from __future__ import annotations
import numpy as np

from ball import state as ball_state

GRAV = np.array([0.0, 0.0, -9.81])


class BallPerception:
    """Simulated stereo-camera perception of the ball.

    Realistic-ish characteristics (modeled after Intel RealSense D435 /
    StereoLabs ZED 2 class):
      - Latency: 50 ms (12 sim steps at 240 Hz).
      - Position noise σ scales with distance from observer:
        σ_pos ≈ 0.005 + 0.005 * dist (m). At 1 m distance: ~1 cm; at 4 m: ~2.5 cm.
      - Velocity noise σ similarly distance-scaled, +floor.
    Closer = more accurate, mirroring real stereo (depth uncertainty grows
    with distance²).

    Catcher reads `observe(viewer_pos)` — the viewer is the catcher, so
    "distance" = distance from catcher to ball.
    """
    def __init__(self, ball_id, latency_steps=12,
                 pos_sigma_floor=0.005, pos_sigma_per_m=0.005,
                 vel_sigma_floor=0.05, vel_sigma_per_m=0.06,
                 seed=0):
        self.ball_id = ball_id
        self.latency_steps = latency_steps
        self.pos_sigma_floor = pos_sigma_floor
        self.pos_sigma_per_m = pos_sigma_per_m
        self.vel_sigma_floor = vel_sigma_floor
        self.vel_sigma_per_m = vel_sigma_per_m
        self._buf = []
        self._rng = np.random.default_rng(seed)

    def step_record(self):
        bp, bv = ball_state(self.ball_id)
        self._buf.append((bp.copy(), bv.copy()))
        if len(self._buf) > self.latency_steps + 1:
            self._buf.pop(0)

    def observe(self, viewer_pos=None):
        """Return latency-delayed noisy (pos, vel) of the ball.
        If viewer_pos is given, noise scales with distance from viewer
        (closer = lower noise — matches real stereo perception)."""
        if not self._buf:
            return ball_state(self.ball_id)
        idx = max(0, len(self._buf) - 1 - self.latency_steps)
        bp_true, bv_true = self._buf[idx]
        if viewer_pos is not None:
            dist = float(np.linalg.norm(np.asarray(viewer_pos) - bp_true))
            ps = self.pos_sigma_floor + self.pos_sigma_per_m * dist
            vs = self.vel_sigma_floor + self.vel_sigma_per_m * dist
        else:
            ps, vs = 0.015, 0.25
        bp_noisy = bp_true + self._rng.normal(0, ps, 3)
        bv_noisy = bv_true + self._rng.normal(0, vs, 3)
        return bp_noisy, bv_noisy


class BallEstimator:
    """Alpha-beta filter over latency-delayed ballistic measurements, with
    latency compensation.

    The measurement stream is `latency_s` old. Acting on it raw costs
    rel_speed · latency of position error (~23 cm at 4.6 m/s, 50 ms) —
    bigger than the whole catch radius. The filter tracks the *delayed*
    state with the known ballistic dynamics, and `estimate()` extrapolates
    it forward by the latency under gravity (exact for drag-free flight).

    Alpha/beta low because measurements arrive at 240 Hz: the dynamics
    model carries the state; measurements only trim drift.
    """
    def __init__(self, latency_s: float, dt: float, alpha=0.2, beta=0.2):
        self.latency_s = latency_s
        self.dt = dt
        self.alpha = alpha
        self.beta = beta
        self.p = None
        self.v = None

    def update(self, meas_pos, meas_vel):
        if self.p is None:
            self.p = np.array(meas_pos, dtype=float)
            self.v = np.array(meas_vel, dtype=float)
            return
        # Predict: advance the internal delayed-state one tick. Semi-implicit
        # Euler (v first, then p with new v) to match PyBullet's integrator.
        self.v = self.v + GRAV * self.dt
        self.p = self.p + self.v * self.dt
        # Correct
        self.p = self.p + self.alpha * (np.asarray(meas_pos) - self.p)
        self.v = self.v + self.beta * (np.asarray(meas_vel) - self.v)

    def estimate(self):
        """Best-guess CURRENT (pos, vel): filtered delayed state extrapolated
        forward by the sensor latency."""
        tau = self.latency_s
        pos = self.p + self.v * tau + 0.5 * GRAV * tau * tau
        vel = self.v + GRAV * tau
        return pos, vel
