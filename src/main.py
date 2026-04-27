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
from config import GameConfig, DEFAULT as DEFAULT_GAME


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
    state = {
        "pos": d.position().tolist(),
        "vel": d.velocity().tolist(),
        "ang_vel": list(ang),
        "ang_speed": float(np.linalg.norm(ang)),
        "orn_quat": list(orn),
        "target": d.target.tolist(),
        "holding": d.held_constraint is not None,
    }
    # Arm joint state + EE world pose (per-drone, present on both since both
    # have arms in the URDF).
    if hasattr(d, "shoulder_joint"):
        s_pos, s_vel, e_pos, e_vel = d.joint_states()
        ee_pos, _, ee_vel, _ = d.ee_state()
        state.update({
            "shoulder_pos": float(s_pos), "shoulder_vel": float(s_vel),
            "elbow_pos": float(e_pos),    "elbow_vel": float(e_vel),
            "ee_pos": ee_pos.tolist(),    "ee_vel": ee_vel.tolist(),
        })
    return state


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
        video_path: str | None = None, video_every: int = 8,
        cfg: GameConfig = DEFAULT_GAME):
    """Run the full play-catch demo. All scene geometry comes from `cfg`."""
    setup(gui=gui, room_size=cfg.room_size, wall_height=cfg.wall_height)
    logger = Logger(log_path, decimate=log_decimate)
    video = VideoRecorder(video_path, every=video_every)
    sim_step = [0]  # mutable counter for closures
    HOVER_Z = cfg.hover_z

    thrower = Drone(start_pos=cfg.thrower_start, home_pos=cfg.thrower_home,
                    play_area_min_offset=cfg.thrower_play_min_offset,
                    play_area_max_offset=cfg.thrower_play_max_offset)
    catcher = Drone(start_pos=cfg.catcher_start, home_pos=cfg.catcher_home,
                    play_area_min_offset=cfg.catcher_play_min_offset,
                    play_area_max_offset=cfg.catcher_play_max_offset)
    cube = p.loadURDF("cube_small.urdf", list(cfg.cube_pos))
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
    # Orange = where the ball was ACTUALLY released (drops at release time
    # and stays there). Lets you see how much the drone trails the released
    # ball vs cleanly separating from it. Bigger + high-contrast so it's
    # visible against the floor/sky.
    m_release_actual = Marker([1.0, 0.5, 0.0, 1.0], radius=0.12)
    # Play-area outlines (asymmetric → use lo/hi corners)
    for d, color in ((thrower, [0.9, 0.3, 0.3]), (catcher, [0.3, 0.5, 1.0])):
        lo = d.home_pos + d.play_area_min_offset
        hi = d.home_pos + d.play_area_max_offset
        center = (lo + hi) / 2
        half = (hi - lo) / 2
        draw_box_outline(center, half, color)

    # Spawn ball at the end-effector's current world position (arm starts
    # folded — EE sits near body center). Drone grasps it immediately;
    # ball follows the EE through arm motion thereafter.
    ee_initial = thrower.gripper_world_position()
    ball = spawn_ball(ee_initial)
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

    # Warm up: let drones settle at hover with arm folded + ball gripped at EE.
    thrower.grasp(ball, max_distance=0.10)
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
        hover_z=cfg.hover_z,
        ceiling_z=cfg.ceiling_z,
        ceiling_margin=cfg.ceiling_margin,
        backup_x_min=float(play_lo[0]),
        play_x_max=float(play_hi[0]),
        floor_margin=cfg.floor_margin,
        release_x_range=(float(play_lo[0] + 0.5), float(play_hi[0])),
        m_drone=0.625, m_ball=0.065,
        max_thrust=20.0, max_tilt_deg=35.0,
        brake_decel=cfg.brake_decel,
    )
    # "max_flight" maximizes ball flight time → catcher has more time to
    # react, throws look more like high arcs. Other options: "max_throw"
    # (fast flat fastball), "min_ke" (gentle), "pareto" (random from frontier).
    throw = plan_throw(inputs, prefer="max_flight")
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

    # --- v1: STATIONARY THROW. Drone hovers at release_pos with arm extended
    # straight down. Arm spin delivers ALL the throw velocity (no drone
    # translation contribution). This avoids the coupling between drone
    # translation/brake and arm dynamics that was producing inconsistent
    # throws. Real bowling-style (drone runup + arm sweep) is the v2 goal.
    release_pos = np.array(throw.release_pos)
    release_vel = np.array(throw.release_vel)
    throw_dir = release_vel / np.linalg.norm(release_vel)
    target_speed = float(np.linalg.norm(release_vel))
    catcher_xy = catcher.position()[:2]
    m_ball_target.set([catcher_xy[0], catcher_xy[1], HOVER_Z])

    # Park drone over release_pos (skip backup; drone is already at home).
    thrower.set_target(release_pos)
    for _ in range(int(2.5 / DT)):
        tick("approach_to_release_pos")
        if (np.linalg.norm(thrower.position() - release_pos) < 0.15
                and np.linalg.norm(thrower.velocity()) < 0.3):
            break

    # SPIN: arm starts wound-up (folded_shoulder=-π/2 in config, set during
    # Drone.__post_init__). Command full ω forward — arm sweeps from -π/2
    # → 0 → +π/2 → ... reaching full ω before the optimal release angle.
    # Tip world velocity passes through "purely forward" at shoulder=0 and
    # "forward-up at 47°" at shoulder≈+0.83. Trigger fires when v_ee
    # aligns with planner's release_vel.
    L_arm = cfg.arm.upper_arm_len + cfg.arm.forearm_len
    omega_required = target_speed / L_arm
    omega_cmd = min(omega_required, 18.0)
    RAMP_DURATION = 0.20  # ramp arm vel target 0 → omega_cmd over this
    spin_started_at = sim_step[0] * DT

    # Multi-condition release trigger (see plan §F).
    v_proj_max = -np.inf
    released = False
    actual_release_pos = None
    grip_v_at_release = None
    trig_reason = None
    max_steps = int(cfg.arm.spin_window_s / DT)

    for i in range(max_steps):
        # Ramp shoulder velocity command linearly to spread arm-reaction
        # angular momentum over time — step-commanding full ω hits drone
        # with ~2 N·m impulsive torque, drone tilts past 80° within 50 ms
        # and falls. With a 200 ms ramp, α_arm ≈ 80 rad/s² → reaction
        # ≈ 1.1 N·m, well within cascade's 3 N·m torque budget.
        t_since_spin = sim_step[0] * DT - spin_started_at
        ramp_progress = min(1.0, t_since_spin / RAMP_DURATION)
        thrower.spin_arm(shoulder_vel=omega_cmd * ramp_progress, elbow_vel=0.0)
        tick("throw_windup_arm")
        v_ee = thrower.gripper_world_velocity()
        v_proj = float(np.dot(v_ee, throw_dir))
        v_ee_mag = float(np.linalg.norm(v_ee))
        cos_align = float(np.dot(v_ee, release_vel) /
                          (v_ee_mag * target_speed + 1e-9))
        t_since_spin = sim_step[0] * DT - spin_started_at
        gates_ok = (t_since_spin > cfg.arm.min_spin_time
                    and cos_align > cfg.arm.release_align_cos_min)
        mag_met = v_proj >= cfg.arm.release_mag_frac * target_speed
        past_peak = v_proj < v_proj_max - cfg.arm.release_decline_threshold
        timeout = t_since_spin > cfg.arm.spin_window_s
        if (gates_ok and (mag_met or past_peak)) or timeout:
            actual_release_pos = thrower.gripper_world_position()
            grip_v_at_release = thrower.gripper_world_velocity()
            thrower.release()
            m_release_actual.set(actual_release_pos)
            trig_reason = ("mag_met" if mag_met else
                           "past_peak" if past_peak else "timeout")
            released = True
            break
        v_proj_max = max(v_proj_max, v_proj)

    # Forced release if loop exits without trigger (shouldn't happen but safe)
    if not released:
        actual_release_pos = thrower.gripper_world_position()
        grip_v_at_release = thrower.gripper_world_velocity()
        thrower.release()
        m_release_actual.set(actual_release_pos)
        trig_reason = "loop_end"

    print(f"[t={sim_step[0]*DT:.2f}s] threw ball  "
          f"release_pos={release_pos.round(2).tolist()}  "
          f"target_vel={release_vel.round(2).tolist()}  "
          f"actual_grip_v={grip_v_at_release.round(2).tolist()}  "
          f"actual_release_pos={actual_release_pos.round(2).tolist()}  "
          f"trigger={trig_reason}")

    # Post-release: re-extend arm to neutral hanging position, restore
    # normal tilt cap (we never moved the body during the throw — no need
    # for evade flip-brake), go home.
    m_release_target.hide()
    thrower.extend_arm()
    thrower.controller.max_tilt_deg = 35.0
    thrower.go_home()
    thrower.set_yaw_target(0.0)

    phase = "tracking"
    steps = int(duration_s / DT)
    for i in range(steps):
        predicted_xy = None
        if phase == "tracking":
            bp, bv = state(ball)
            # Two-mode catcher logic:
            #   Far: chase the predicted z=HOVER_Z landing point (good for big
            #        positioning moves while ball is high in the air).
            #   Close: chase the ball's CURRENT 3D position (handles the case
            #        where ball passes through HOVER_Z briefly OR drops below
            #        it before catcher arrives at the ground-zero prediction).
            predicted_xy, _ = predict_landing(bp, bv, target_z=HOVER_Z)
            cat_to_ball = float(np.linalg.norm(catcher.position() - bp))
            if cat_to_ball < 1.0:
                # Direct 3D pursuit — converge on actual ball position.
                catcher.set_target(bp)
                m_ball_target.set(bp)
            elif predicted_xy is not None:
                catcher.set_target([predicted_xy[0], predicted_xy[1], HOVER_Z])
                m_ball_target.set([predicted_xy[0], predicted_xy[1], HOVER_Z])
            else:
                # Ball below HOVER_Z and no prediction — pursue directly.
                catcher.set_target(bp)
                m_ball_target.set(bp)
            if cat_to_ball < 0.5:
                if catcher.grasp(ball, max_distance=0.5):
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
