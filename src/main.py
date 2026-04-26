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
from planner import PlannerInputs, plan as plan_throw


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


def draw_box_outline(center, half_extents, color, thickness=0.01):
    """Draw the 12 edges of an axis-aligned box as visual-only thin boxes.
    Real visual bodies (not debug lines) so getCameraImage / video picks them up.
    """
    cx, cy, cz = center
    hx, hy, hz = half_extents
    rgba = list(color) + ([0.9] if len(color) == 3 else [])
    edges = []
    for sy in (-1, 1):
        for sz in (-1, 1):
            edges.append(((cx, cy + sy*hy, cz + sz*hz),
                          (hx, thickness, thickness)))
    for sx in (-1, 1):
        for sz in (-1, 1):
            edges.append(((cx + sx*hx, cy, cz + sz*hz),
                          (thickness, hy, thickness)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            edges.append(((cx + sx*hx, cy + sy*hy, cz),
                          (thickness, thickness, hz)))
    for pos, half in edges:
        vis = p.createVisualShape(p.GEOM_BOX, halfExtents=half, rgbaColor=rgba)
        p.createMultiBody(baseMass=0, baseVisualShapeIndex=vis, basePosition=list(pos))


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

    def __init__(self, path: str | None, every: int, width=640, height=480,
                 sim_hz=240, playback_speed=0.5):
        # Default playback_speed=0.5 → 0.5× slow-mo so motion is easier to read.
        # Set =1.0 for real-time, =0.25 for very slow.
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
            # Side-spectator view from inside the arena (walls are now
            # collision-only, so an outside camera would still see floor/sky
            # but we get a more natural framing from inside). Slightly raised
            # above hover height with a small downward tilt.
            self.view = p.computeViewMatrix(
                cameraEyePosition=[0.0, -5.5, 2.5],
                cameraTargetPosition=[0.0, 0.0, 1.5],
                cameraUpVector=[0, 0, 1])
            self.proj = p.computeProjectionMatrixFOV(
                fov=90, aspect=width / height, nearVal=0.1, farVal=30.0)

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

    # Each drone has an asymmetric play area: lots of room BEHIND home for
    # backup runway (like a tennis player's baseline), less room forward — they
    # can reach a bit into the opponent's near-court for a tough catch but
    # can't camp in opponent territory. Z capped at CEILING−margin (=2.6 m
    # with ceiling 3 m) so the soft bound keeps targets off the ceiling.
    Z_LO = -1.3   # 0.2 m floor clearance
    Z_HI = 1.1    # ceiling − 0.4 m margin
    # No overlap: each drone owns its half of the room (centerline at x=0).
    # Sport-like — thrower can't poach into catcher's area.
    thrower = Drone(start_pos=(-3.0, 0.0, HOVER_Z),
                    home_pos=(-3.0, 0.0, HOVER_Z),
                    play_area_min_offset=(-2.5, -1.5, Z_LO),  # 2.5 m behind home
                    play_area_max_offset=(+3.0, +1.5, Z_HI))  # to centerline
    catcher = Drone(start_pos=(3.0, 0.0, HOVER_Z),
                    home_pos=(3.0, 0.0, HOVER_Z),
                    play_area_min_offset=(-3.0, -1.5, Z_LO),  # to centerline
                    play_area_max_offset=(+2.5, +1.5, Z_HI))
    cube = p.loadURDF("cube_small.urdf", [2.0, -1.0, 0.05])
    p.changeVisualShape(cube, -1, rgbaColor=[0.2, 0.8, 0.2, 1])  # green cube

    # Markers (visual-only, no collision):
    #   red    = thrower position target
    #   blue   = catcher position target
    #   yellow = ball-intended-landing point (where the throw is aimed)
    m_thrower = Marker([1.0, 0.2, 0.2, 0.7])
    m_catcher = Marker([0.2, 0.4, 1.0, 0.7])
    m_ball_target = Marker([1.0, 0.85, 0.0, 0.8], radius=0.08)
    # Magenta = planned final release point (static during throw — stays where
    # the planner committed to release, regardless of where the trajectory
    # carrot is moving).
    m_release_target = Marker([1.0, 0.2, 0.8, 0.7], radius=0.07)
    # Play-area outlines (asymmetric → use lo/hi corners)
    for d, color in ((thrower, [0.9, 0.3, 0.3]), (catcher, [0.3, 0.5, 1.0])):
        lo = d.home_pos + d.play_area_min_offset
        hi = d.home_pos + d.play_area_max_offset
        center = (lo + hi) / 2
        half = (hi - lo) / 2
        draw_box_outline(center, half, color)

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

    horiz_dir = np.array([np.cos(yaw_to_catcher), np.sin(yaw_to_catcher), 0.0])

    # --- Plan the throw: grid+Pareto over (release_x, vz), pick from frontier.
    # The planner returns release_pos, release_vel, backup_pos, t_ramp — all
    # consistent under a matched-t single ramp.
    play_lo = thrower.home_pos + thrower.play_area_min_offset
    play_hi = thrower.home_pos + thrower.play_area_max_offset
    inputs = PlannerInputs(
        catcher_xy=tuple(catcher.home_pos[:2]),
        hover_z=HOVER_Z,
        ceiling_z=3.0, ceiling_margin=0.4,
        backup_x_min=float(play_lo[0]),
        play_x_max=float(play_hi[0]),  # forward boundary — drone must brake within
        floor_margin=float(play_lo[2]),
        release_x_range=(float(play_lo[0] + 0.5), float(play_hi[0])),
        m_drone=0.55, m_ball=0.065,
        max_thrust=12.0, max_tilt_deg=35.0,
    )
    # prefer="max_throw" picks the flattest, fastest plan (real throw, not
    # a drop). "pareto" balances KE vs margin; "min_ke" minimizes ball arrival
    # speed (gentlest catch).
    throw = plan_throw(inputs, prefer="max_throw")
    if throw is None:
        from planner import diagnose_infeasibility
        print(f"[planner] no feasible throw: {diagnose_infeasibility(inputs)}")
        logger.close(); video.close(); p.disconnect(); return
    print(f"[planner] release_pos={tuple(round(x,2) for x in throw.release_pos)}  "
          f"release_vel={tuple(round(x,2) for x in throw.release_vel)}  "
          f"backup={tuple(round(x,2) for x in throw.backup_pos)}  "
          f"t_ramp={throw.t_ramp:.2f}s  apex={throw.apex:.2f}m  "
          f"thrust={throw.thrust_required:.1f}N  tilt={throw.tilt_deg:.1f}°  "
          f"KE={throw.arrival_ke:.2f}J")
    # Park the static release-target marker where the planner committed to
    # release. The moving trajectory carrot is the red m_thrower marker.
    m_release_target.set(throw.release_pos)

    # --- Backup: fly to the planner's backup_pos.
    backup_pos = np.array(throw.backup_pos)
    thrower.set_target(backup_pos)
    for _ in range(int(2.5 / DT)):
        tick("backup")
        if (np.linalg.norm(thrower.position() - backup_pos) < 0.25
                and np.linalg.norm(thrower.velocity()) < 0.4):
            break

    # --- Throw windup: matched-t single ramp from backup → release.
    # pos_target evolves as the integral of vel_target so they stay consistent
    # at every step. At t = t_ramp, drone should be at release_pos with
    # release_vel by construction.
    release_pos = np.array(throw.release_pos)
    release_vel = np.array(throw.release_vel)
    t_ramp = throw.t_ramp
    throw_dir = release_vel / np.linalg.norm(release_vel)
    catcher_xy = catcher.position()[:2]
    m_ball_target.set([catcher_xy[0], catcher_xy[1], HOVER_Z])

    max_steps = int(1.5 * t_ramp / DT)
    for i in range(max_steps):
        t = i * DT
        progress = min(1.0, t / t_ramp)
        # vel_target ramps linearly; pos_target is its integral
        cur_vel = release_vel * progress
        cur_pos = backup_pos + 0.5 * release_vel * (t ** 2) / t_ramp \
                  if t < t_ramp \
                  else release_pos + release_vel * (t - t_ramp)
        thrower.set_target(cur_pos, vel=cur_vel)
        tick("throw_windup")
        if np.dot(thrower.position() - release_pos, throw_dir) >= 0:
            break

    grip_v = thrower.gripper_world_velocity()
    thrower.release()
    print(f"[t={sim_step[0]*DT:.2f}s] threw ball  "
          f"release_pos={release_pos.round(2).tolist()}  "
          f"target_vel={release_vel.round(2).tolist()}  "
          f"actual_grip_v={grip_v.round(2).tolist()}")

    # Evade + return home. Temporarily bump max_tilt to 90° so the cascade
    # can flip-brake (drone tilts ~90° backward, full thrust horizontal in -x).
    # This matches the planner's `brake_decel = max_thrust/m_drone` assumption.
    # Drone briefly free-falls during the flip; OK with our hover_z headroom.
    m_release_target.hide()
    normal_max_tilt = thrower.controller.max_tilt_deg
    thrower.controller.max_tilt_deg = 90.0
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
