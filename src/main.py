"""Demo: two drones play catch, then one picks up a cube."""
import argparse
import json
import os
import time
from pathlib import Path
import numpy as np
import pybullet as p

from world import setup
from drone import Drone
from ball import spawn_ball, predict_landing, state


HOVER_Z = 1.5
DT = 1.0 / 240.0


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


def _drone_state(d):
    _, ang = p.getBaseVelocity(d.body_id)
    _, orn = p.getBasePositionAndOrientation(d.body_id)
    return {
        "pos": d.position().tolist(),
        "vel": d.velocity().tolist(),
        "ang_vel": list(ang),
        "ang_speed": float(np.linalg.norm(ang)),
        "orn_quat": list(orn),
        "target": d.target.tolist(),
        "holding": d.held_constraint is not None,
    }


def snapshot(t, phase, thrower, catcher, ball, cube, predicted_xy):
    bp, bv = state(ball)
    cube_pos, _ = p.getBasePositionAndOrientation(cube)
    return {
        "t": round(t, 5),
        "phase": phase,
        "thrower": _drone_state(thrower),
        "catcher": _drone_state(catcher),
        "ball": {"pos": bp.tolist(), "vel": bv.tolist()},
        "cube": {"pos": list(cube_pos)},
        "predicted_landing_xy": (
            list(predicted_xy) if predicted_xy is not None else None
        ),
    }


class Marker:
    """Visual-only sphere that we move around to show a target/aim point.
    Has no collision shape so it doesn't interact with anything."""
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


class VideoRecorder:
    """Captures offscreen frames via getCameraImage and writes MP4."""

    def __init__(self, path: str | None, every: int, width=640, height=480, fps=30):
        self.path = path
        self.every = max(1, every)
        self.width, self.height = width, height
        self.writer = None
        self.step = 0
        if path is not None:
            import imageio.v2 as imageio
            self.writer = imageio.get_writer(path, fps=fps, codec="libx264",
                                             quality=7, macro_block_size=1)
            self.view = p.computeViewMatrix(
                cameraEyePosition=[3.0, -3.0, 2.5],
                cameraTargetPosition=[0.0, 0.0, 1.2],
                cameraUpVector=[0, 0, 1])
            self.proj = p.computeProjectionMatrixFOV(
                fov=60, aspect=width / height, nearVal=0.1, farVal=20.0)

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


def rotate_videos(runs_dir: Path, keep: int = 5):
    vids = sorted(runs_dir.glob("run_*.mp4"), key=lambda p: p.stat().st_mtime)
    for old in vids[:-keep]:
        old.unlink()
        # also drop the matching jsonl/png if present
        for ext in (".jsonl", ".png"):
            sib = old.with_suffix(ext)
            if sib.exists():
                sib.unlink()


def run(gui: bool = True, duration_s: float = 20.0,
        log_path: str | None = None, log_decimate: int = 10,
        video_path: str | None = None, video_every: int = 8):
    setup(gui=gui)
    logger = Logger(log_path, decimate=log_decimate)
    # 240Hz / 8 = 30fps capture
    video = VideoRecorder(video_path, every=video_every)
    sim_step = [0]  # mutable counter for closures

    # Each drone owns a soft-bound play area centered on its home_pos.
    # Areas overlap a little in the middle so the catcher can step toward the
    # thrower's side to make a tough catch.
    thrower = Drone(start_pos=(-1.5, 0.0, HOVER_Z),
                    home_pos=(-1.5, 0.0, HOVER_Z),
                    play_area_half_extents=(2.0, 1.5, 1.5))
    catcher = Drone(start_pos=(1.5, 0.0, HOVER_Z),
                    home_pos=(1.5, 0.0, HOVER_Z),
                    play_area_half_extents=(2.0, 1.5, 1.5))
    cube = p.loadURDF("cube_small.urdf", [0.5, -1.0, 0.05])
    p.changeVisualShape(cube, -1, rgbaColor=[0.2, 0.8, 0.2, 1])  # green cube

    # Markers (visual-only, no collision):
    #   red    = thrower position target
    #   blue   = catcher position target
    #   yellow = ball-intended-landing point (where the throw is aimed)
    m_thrower = Marker([1.0, 0.2, 0.2, 0.7])
    m_catcher = Marker([0.2, 0.4, 1.0, 0.7])
    m_ball_target = Marker([1.0, 0.85, 0.0, 0.8], radius=0.08)

    # Spawn ball early so logger can reference it during warm-up.
    ball = spawn_ball(thrower.position() - np.array([0, 0, 0.08]))
    p.changeVisualShape(ball, -1, rgbaColor=[1.0, 0.3, 0.3, 1])  # red ball
    p.resetBaseVelocity(ball, linearVelocity=[0, 0, 0])

    def tick(phase, predicted_xy=None):
        thrower.step()
        catcher.step()
        p.stepSimulation()
        m_thrower.set(thrower.target)
        m_catcher.set(catcher.target)
        logger.record(snapshot(sim_step[0] * DT, phase, thrower,
                               catcher, ball, cube, predicted_xy))
        video.capture()
        sim_step[0] += 1
        if gui:
            time.sleep(DT)

    # Warm up: let drones settle at hover (ball rests on thrower hand spawn point)
    thrower.grasp(ball, max_distance=0.5)
    # Aim: yaw thrower so body-x points at the catcher.
    # Catcher's yaw is left at 0 — pre-yawing it to face the thrower puts the
    # geometric attitude controller at its 180° singularity.
    aim = catcher.position() - thrower.position()
    yaw_to_catcher = float(np.arctan2(aim[1], aim[0]))
    thrower.set_yaw_target(yaw_to_catcher)

    for _ in range(int(1.0 / DT)):
        tick("warmup")
    for _ in range(120):
        tick("settle")

    # --- Throw: solve back from "ball lands at catcher_pos at z=HOVER_Z" to
    # get a release_pos + release_vel pair, then ask the controller to track
    # that state. Release when the drone passes through release_pos. ---
    horiz_dir = np.array([np.cos(yaw_to_catcher), np.sin(yaw_to_catcher), 0.0])
    release_pos = thrower.position() + horiz_dir * 1.0 + np.array([0, 0, 1.0])
    catcher_xy = catcher.position()[:2]
    flight_time = 0.8  # tunable; longer = higher arc, also higher vz needed
    horiz_xy = (catcher_xy - release_pos[:2]) / flight_time
    vz_release = (HOVER_Z - release_pos[2] + 0.5 * 9.81 * flight_time ** 2) / flight_time
    release_vel = np.array([horiz_xy[0], horiz_xy[1], vz_release])

    # Set a lookahead target: aim 0.4s past release_pos along release_vel so the
    # controller doesn't try to brake as the drone approaches release_pos.
    lookahead_pos = release_pos + release_vel * 0.4
    thrower.set_target(lookahead_pos, vel=release_vel)
    # Show where the ball is aimed (catcher's hover point)
    m_ball_target.set([catcher_xy[0], catcher_xy[1], HOVER_Z])

    # Trigger: release the moment the drone crosses the plane through
    # release_pos perpendicular to the throw direction.
    throw_dir = release_vel / np.linalg.norm(release_vel)
    max_steps = int(1.5 / DT)
    for _ in range(max_steps):
        tick("throw_windup")
        if np.dot(thrower.position() - release_pos, throw_dir) >= 0:
            break

    grip_v = thrower.gripper_world_velocity()
    thrower.release()
    print(f"[t={sim_step[0]*DT:.2f}s] threw ball  "
          f"release_pos={release_pos.round(2).tolist()}  "
          f"target_vel={release_vel.round(2).tolist()}  "
          f"actual_grip_v={grip_v.round(2).tolist()}")

    # Evade + return home (cascade will pitch up to brake and climb)
    thrower.go_home()
    thrower.set_yaw_target(0.0)

    phase = "tracking"
    steps = int(duration_s / DT)
    for i in range(steps):
        predicted_xy = None
        if phase == "tracking":
            bp, bv = state(ball)
            # Don't yaw-track the ball: when the ball is directly behind the
            # catcher (yaw error ≈ π) the geometric attitude controller hits
            # its singularity AND, with thrust_vec in the same plane as x_c,
            # R_des becomes symmetric → e_R == 0 → the cascade can't tilt the
            # drone to translate. Yaw is cosmetic for our gripper anyway.
            predicted_xy, _ = predict_landing(bp, bv, target_z=HOVER_Z)
            if predicted_xy is not None:
                catcher.set_target([predicted_xy[0], predicted_xy[1], HOVER_Z])
                m_ball_target.set([predicted_xy[0], predicted_xy[1], HOVER_Z])
            else:
                m_ball_target.hide()
            if np.linalg.norm(catcher.position() - bp) < 0.25:
                if catcher.grasp(ball, max_distance=0.3):
                    phase = "carry_to_cube"
                    print(f"[t={i*DT:.2f}s] caught ball")

        elif phase == "carry_to_cube":
            # Translate at hover altitude — descending while translating forces
            # an extreme tilt that kills vertical thrust authority.
            cube_pos, _ = p.getBasePositionAndOrientation(cube)
            above = np.array([cube_pos[0], cube_pos[1], HOVER_Z])
            catcher.set_target(above)
            if np.linalg.norm(catcher.position()[:2] - above[:2]) < 0.15:
                catcher.release()
                phase = "descend_to_cube"

        elif phase == "descend_to_cube":
            cube_pos, _ = p.getBasePositionAndOrientation(cube)
            catcher.set_target(np.array(cube_pos) + np.array([0, 0, 0.12]))
            if catcher.grasp(cube, max_distance=0.18):
                phase = "lift"
                print(f"[t={i*DT:.2f}s] picked up cube")

        elif phase == "lift":
            catcher.set_target(catcher.home_pos + np.array([0, 0, 0.5]))
            m_ball_target.hide()

        thrower.set_target([-1.5, 0.0, HOVER_Z])
        tick(phase, predicted_xy)

    print(f"[final] phase={phase} catcher_pos={catcher.position()}")
    logger.close()
    video.close()
    p.disconnect()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--duration", type=float, default=20.0)
    ap.add_argument("--log", type=str, default=None,
                    help="Path to JSONL log file")
    ap.add_argument("--log-decimate", type=int, default=10,
                    help="Write every Nth sim step (default 10 = ~24 Hz)")
    ap.add_argument("--video", type=str, default=None,
                    help="Path to MP4 video file")
    ap.add_argument("--video-every", type=int, default=16,
                    help="Capture every Nth step (default 16 = 15fps)")
    ap.add_argument("--runs-dir", type=str, default=None,
                    help="If set, auto-name log+video as run_<timestamp>.* in this dir "
                         "and keep only the last 5 runs")
    args = ap.parse_args()

    log_path = args.log
    video_path = args.video
    if args.runs_dir:
        runs = Path(args.runs_dir); runs.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        log_path = log_path or str(runs / f"run_{stamp}.jsonl")
        video_path = video_path or str(runs / f"run_{stamp}.mp4")

    run(gui=not args.headless, duration_s=args.duration,
        log_path=log_path, log_decimate=args.log_decimate,
        video_path=video_path, video_every=args.video_every)

    if args.runs_dir:
        rotate_videos(Path(args.runs_dir), keep=5)


if __name__ == "__main__":
    main()
