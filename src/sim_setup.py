"""Shared scaffolding for sim entry-points: world setup, drone construction,
markers, video recording, jsonl logging, and the per-step tick wrapper.

Both the main demo (`main.py`) and isolated subsystem tests (`tests/*.py`)
build on this module so the test files stay small and focused on what's
unique to each test.
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable
import numpy as np
import pybullet as p

from world import setup as world_setup
from drone import Drone
from ball import spawn_ball
from config import GameConfig, DEFAULT as DEFAULT_GAME

DT = 1.0 / 240.0


# ---------------- Logging ----------------
class Logger:
    def __init__(self, path: str | None, decimate: int = 1):
        self.fh = open(path, "w") if path else None
        self.decimate = max(1, decimate)
        self.step = 0

    def record(self, payload: dict):
        if self.fh is not None and self.step % self.decimate == 0:
            self.fh.write(json.dumps(payload) + "\n")
        self.step += 1

    def close(self):
        if self.fh is not None:
            self.fh.close()


# ---------------- Markers ----------------
class Marker:
    """Visual-only sphere movable in space. No collision shape."""
    def __init__(self, rgba, radius=0.06):
        vis = p.createVisualShape(p.GEOM_SPHERE, radius=radius, rgbaColor=rgba)
        self.body = p.createMultiBody(baseMass=0, baseVisualShapeIndex=vis,
                                      basePosition=[0, 0, -10])
        self._visible = False

    def set(self, pos):
        p.resetBasePositionAndOrientation(self.body, list(pos), [0, 0, 0, 1])
        self._visible = True

    def hide(self):
        if self._visible:
            p.resetBasePositionAndOrientation(self.body, [0, 0, -10], [0, 0, 0, 1])
            self._visible = False


@dataclass
class MarkerSet:
    """Standard 3-marker palette for intent-vs-result visualization.
      target  (red)     — what the controller is currently asked to track
      intent  (magenta) — what the test/plan wants the drone to be doing
      actual  (orange)  — where the drone actually is, sampled each tick
    """
    target: Marker = field(default_factory=lambda: Marker([1.0, 0.2, 0.2, 0.8]))
    intent: Marker = field(default_factory=lambda: Marker([1.0, 0.2, 0.8, 0.7], radius=0.07))
    actual: Marker = field(default_factory=lambda: Marker([1.0, 0.5, 0.0, 1.0], radius=0.05))


# ---------------- Video ----------------
class VideoRecorder:
    """Captures offscreen frames via getCameraImage and writes MP4."""

    def __init__(self, path: str | None, every: int = 8, width=640, height=480,
                 sim_hz=240, playback_speed=0.5,
                 eye=(0.0, -3.5, 1.8), target=(0.0, 0.0, 1.5), fov=75):
        self.path = path
        self.every = max(1, every)
        self.width, self.height = width, height
        self.writer = None
        self.step = 0
        if path is not None:
            import imageio.v2 as imageio
            capture_fps = sim_hz / self.every
            playback_fps = capture_fps * playback_speed
            self.writer = imageio.get_writer(path, fps=playback_fps, codec="libx264",
                                             quality=7, macro_block_size=1)
            self.view = p.computeViewMatrix(
                cameraEyePosition=list(eye),
                cameraTargetPosition=list(target),
                cameraUpVector=[0, 0, 1])
            self.proj = p.computeProjectionMatrixFOV(
                fov=fov, aspect=width / height, nearVal=0.1, farVal=20.0)

    def capture(self):
        if self.writer is None:
            self.step += 1
            return
        if self.step % self.every == 0:
            _, _, rgba, _, _ = p.getCameraImage(
                self.width, self.height, viewMatrix=self.view,
                projectionMatrix=self.proj, renderer=p.ER_TINY_RENDERER)
            frame = np.array(rgba, dtype=np.uint8).reshape(self.height, self.width, 4)
            self.writer.append_data(frame[:, :, :3])
        self.step += 1

    def close(self):
        if self.writer is not None:
            self.writer.close()


# ---------------- Setup helpers ----------------
def make_world(cfg: GameConfig = DEFAULT_GAME, gui: bool = True):
    return world_setup(gui=gui, room_size=cfg.room_size, wall_height=cfg.wall_height)


def make_solo_drone(home_pos=(0.0, 0.0, 1.5),
                    play_extent=(5.0, 5.0, 1.2), urdf_path=None):
    """Single drone, centered, with a wide play area (default ±5 m horiz,
    ±1.2 m vert). Tests that traverse meaningful distance should pass an
    explicit play_extent or set home_pos near the middle of their workspace
    so set_target doesn't clip targets at the boundary.

    `urdf_path` selects the body model (default: plain quadrotor; pass the
    gripper URDF for the caging-finger catcher).
    """
    px, py, pz = play_extent
    return Drone(start_pos=home_pos, home_pos=home_pos, urdf_path=urdf_path,
                 play_area_min_offset=(-px, -py, -pz),
                 play_area_max_offset=(+px, +py, +pz))


def spawn_ball_at_ee(drone: Drone, max_grasp_distance: float = 0.10) -> int:
    """Spawn a ball at the drone's end-effector position and grasp it.
    Caller is responsible for releasing/cleanup later if needed."""
    ee_pos = drone.gripper_world_position()
    ball = spawn_ball(ee_pos)
    p.changeVisualShape(ball, -1, rgbaColor=[1.0, 0.3, 0.3, 1])
    p.resetBaseVelocity(ball, linearVelocity=[0, 0, 0])
    if not drone.grasp(ball, max_distance=max_grasp_distance):
        raise RuntimeError(f"failed to grasp ball at EE (ball {ee_pos} too far)")
    return ball


def auto_run_paths(runs_dir: str | None) -> tuple[Optional[str], Optional[str]]:
    """If runs_dir given, return (log_path, video_path) auto-named with timestamp."""
    if runs_dir is None:
        return None, None
    runs = Path(runs_dir); runs.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    return str(runs / f"run_{stamp}.jsonl"), str(runs / f"run_{stamp}.mp4")


# ---------------- Tick ----------------
class Sim:
    """Holds the per-tick context for a test/demo: drones, markers, logger,
    video, sim_step counter. Provides `tick()` that advances physics one step
    and runs the bookkeeping."""

    def __init__(self, drones: list[Drone], markers: MarkerSet,
                 logger: Logger, video: VideoRecorder, gui: bool = True):
        self.drones = drones
        self.markers = markers
        self.logger = logger
        self.video = video
        self.gui = gui
        self.sim_step = 0

    @property
    def t(self) -> float:
        return self.sim_step * DT

    def tick(self, phase: str, extra_payload: Optional[dict] = None):
        for d in self.drones:
            d.step()
        p.stepSimulation()
        # Update markers from drones (target = first drone's target by default;
        # actual = first drone's position). Tests can override by setting
        # markers manually before calling tick().
        if self.drones:
            d0 = self.drones[0]
            self.markers.target.set(d0.target)
            self.markers.actual.set(d0.position())
        # Record snapshot
        if self.logger.fh is not None:
            payload = {"t": round(self.t, 5), "phase": phase}
            for i, d in enumerate(self.drones):
                payload[f"drone{i}"] = drone_state(d)
            if extra_payload:
                payload.update(extra_payload)
            self.logger.record(payload)
        else:
            self.logger.step += 1
        self.video.capture()
        self.sim_step += 1
        if self.gui:
            time.sleep(DT)


def drone_state(d: Drone) -> dict:
    """Compact snapshot of a drone's state (position, velocity, attitude,
    angular velocity, arm joints + EE if present)."""
    pos, orn = p.getBasePositionAndOrientation(d.body_id)
    lin, ang = p.getBaseVelocity(d.body_id)
    rpy = p.getEulerFromQuaternion(orn)
    state = {
        "pos": list(pos),
        "vel": list(lin),
        "ang_vel": list(ang),
        "rpy": list(rpy),     # roll, pitch, yaw (radians)
        "target": d.target.tolist(),
    }
    if hasattr(d, "shoulder_joint"):
        s_pos, s_vel, e_pos, e_vel = d.joint_states()
        ee_pos, _, ee_vel, _ = d.ee_state()
        state.update({
            "shoulder_pos": float(s_pos), "shoulder_vel": float(s_vel),
            "elbow_pos": float(e_pos),    "elbow_vel": float(e_vel),
            "ee_pos": ee_pos.tolist(),    "ee_vel": ee_vel.tolist(),
        })
    return state


def rotate_runs(runs_dir: Path, keep: int = 5):
    vids = sorted(runs_dir.glob("run_*.mp4"), key=lambda p: p.stat().st_mtime)
    for old in vids[:-keep]:
        old.unlink()
        for ext in (".jsonl", ".png"):
            sib = old.with_suffix(ext)
            if sib.exists():
                sib.unlink()
