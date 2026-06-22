"""Demo: two drones play catch, then one picks up a cube."""
import argparse
import json
import math
import os
import time
from dataclasses import replace
from pathlib import Path
import numpy as np
import pybullet as p

from world import setup
from drone import Drone
from ball import spawn_ball, predict_landing, state
from planner import PlannerInputs, plan as plan_throw
from config import GameConfig, DEFAULT as DEFAULT_GAME
from throw import decompose_throw, cruise_speed_for_release
from perception import BallPerception


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
    """Captures 4 viewpoints per frame and writes them as a 2x2 grid MP4.
    Top-left: side-view (current scene cam). Top-right: thrower POV.
    Bottom-left: catcher POV. Bottom-right: ball-follow.
    Each cell is `cell_w x cell_h`; total frame is 2*cell_w x 2*cell_h.
    The camera providers are functions that return (eye, target, up) per
    capture call so they can track moving subjects (drones, ball).
    """

    def __init__(self, path: str | None, every: int,
                 cell_w=640, cell_h=480, sim_hz=240, playback_speed=0.5,
                 thrower=None, catcher=None, ball_id=None):
        self.path = path
        self.every = max(1, every)
        self.cell_w, self.cell_h = cell_w, cell_h
        self.thrower = thrower
        self.catcher = catcher
        self.ball_id = ball_id
        self.writer = None
        self.step = 0
        if path is not None:
            import imageio.v2 as imageio
            capture_fps = sim_hz / self.every
            playback_fps = capture_fps * playback_speed
            self.writer = imageio.get_writer(path, fps=playback_fps, codec="libx264",
                                             quality=7, macro_block_size=1)
            self.proj = p.computeProjectionMatrixFOV(
                fov=70, aspect=cell_w / cell_h, nearVal=0.1, farVal=25.0)
            # Tighter FOV for POV cams (looks like a real on-board camera)
            self.proj_pov = p.computeProjectionMatrixFOV(
                fov=85, aspect=cell_w / cell_h, nearVal=0.05, farVal=20.0)

    def _view_side(self):
        # Static spectator side-view (top-left): same as v1
        return p.computeViewMatrix([0.5, -5.0, 1.8], [0.5, 0.0, 1.0], [0, 0, 1])

    def _view_thrower_pov(self):
        # Camera mounted on thrower body, looking forward (drone's body +x).
        # Drone yaws toward catcher → POV looks toward the throw direction.
        if self.thrower is None:
            return self._view_side()
        pos = self.thrower.position()
        R = np.array(p.getMatrixFromQuaternion(
            self.thrower.orientation())).reshape(3, 3)
        body_x = R @ np.array([1.0, 0.0, 0.0])
        eye = pos + body_x * 0.05 + np.array([0, 0, 0.05])
        target = pos + body_x * 5.0
        return p.computeViewMatrix(eye.tolist(), target.tolist(), [0, 0, 1])

    def _view_catcher_pov(self):
        # Catcher faces world +x by default but the ball comes from world -x.
        # Mount camera on catcher body looking toward -x (the incoming ball).
        if self.catcher is None:
            return self._view_side()
        pos = self.catcher.position()
        R = np.array(p.getMatrixFromQuaternion(
            self.catcher.orientation())).reshape(3, 3)
        body_neg_x = R @ np.array([-1.0, 0.0, 0.0])
        eye = pos + body_neg_x * 0.05 + np.array([0, 0, 0.05])
        target = pos + body_neg_x * 5.0
        return p.computeViewMatrix(eye.tolist(), target.tolist(), [0, 0, 1])

    def _view_ball_follow(self):
        # Camera trails the ball at a fixed offset, looking at the ball.
        # Pre-throw: ball is at thrower's EE → camera looks at thrower.
        # Mid-flight: camera moves with ball.
        if self.ball_id is None:
            return self._view_side()
        bp = np.array(p.getBasePositionAndOrientation(self.ball_id)[0])
        # Trail behind ball in -y direction so we always see the side profile
        eye = bp + np.array([0.0, -2.5, 1.0])
        return p.computeViewMatrix(eye.tolist(), bp.tolist(), [0, 0, 1])

    def _render(self, view, proj):
        _, _, rgba, _, _ = p.getCameraImage(
            self.cell_w, self.cell_h, viewMatrix=view,
            projectionMatrix=proj, renderer=p.ER_TINY_RENDERER)
        return np.array(rgba, dtype=np.uint8).reshape(
            self.cell_h, self.cell_w, 4)[:, :, :3]

    def capture(self):
        if self.writer is None:
            self.step += 1
            return
        if self.step % self.every == 0:
            tl = self._render(self._view_side(),         self.proj)
            tr = self._render(self._view_thrower_pov(),  self.proj_pov)
            bl = self._render(self._view_catcher_pov(),  self.proj_pov)
            br = self._render(self._view_ball_follow(),  self.proj)
            top = np.hstack([tl, tr])
            bot = np.hstack([bl, br])
            grid = np.vstack([top, bot])
            self.writer.append_data(grid)
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
    # The throw releases at drone_release_x ≈ 0.6 (well past the default
    # thrower_play_max_offset_x = 2.0 → play_x_max = 0). Widen the
    # thrower's forward play area so set_target doesn't clip the release
    # target. Also widen the room so ball doesn't bounce off +x wall.
    # Tighter, non-overlapping play areas.
    # Thrower x ∈ [-3.0, -0.5] (2.5 m wide, enough for runway + release).
    # Catcher x ∈ [+1.0, +3.0] (2.0 m wide, covers cube + ball intercept).
    # Ball flies through the 1.5 m gap [-0.5, +1.0].
    # Catcher z down to 0.4 so its extended arm tip reaches the cube.
    cfg = replace(cfg,
                  room_size=10.0,
                  thrower_play_min_offset=(-1.0, -1.0, -0.7),
                  thrower_play_max_offset=(+1.5, +1.0, +1.1),
                  catcher_play_min_offset=(-1.0, -1.0, -1.1),
                  catcher_play_max_offset=(+1.0, +1.0, +1.1))
    setup(gui=gui, room_size=cfg.room_size, wall_height=cfg.wall_height)
    logger = Logger(log_path, decimate=log_decimate)
    sim_step = [0]
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

    # Now we can build the multi-cam video recorder (needs drones + ball IDs)
    video = VideoRecorder(video_path, every=video_every,
                          thrower=thrower, catcher=catcher, ball_id=ball)
    # Catcher's noisy perception of the ball — used in the tracking phase
    # instead of direct god-mode `state(ball)` reads.
    perception = BallPerception(ball_id=ball)

    def tick(phase, predicted_xy=None):
        thrower.step()
        catcher.step()
        p.stepSimulation()
        perception.step_record()       # capture true ball state for noisy readback
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
    aim = catcher.position() - thrower.position()
    yaw_to_catcher = float(np.arctan2(aim[1], aim[0]))
    thrower.set_yaw_target(yaw_to_catcher)

    # Enable controller layers we built across M1–M3 on the thrower:
    #   arm-reaction torque feedforward (pitch stable through arm transients),
    #   attitude gain scheduling (cascade stays critically damped through
    #     arm-pose inertia changes),
    #   body-z translational FF (drone holds altitude through sweep dive),
    #   PI integrator on attitude (default in cfg, eats steady-state biases).
    thrower.arm_reaction_ff = True
    thrower.attitude_gain_schedule = True
    thrower.arm_translational_ff_z = True
    # Catcher only needs gain scheduling — no arm spin disturbance here.
    catcher.attitude_gain_schedule = True

    for _ in range(int(1.0 / DT)):
        tick("warmup")

    # --- Plan the throw: ballistic to where the catcher's EE will be.
    # Catcher keeps its arm in the natural wound-up pose (shoulder=-π/2,
    # pointing backward in body frame). With catcher facing world +x
    # (yaw=0), the arm points in -x direction = toward the incoming ball.
    # EE is at catcher_x − L_arm at catcher_z. So ball needs to land at
    # z = HOVER_Z (same as catcher body z) and the catcher hovers L_arm
    # past the intercept point so EE sits on the predicted ball xy.
    L_arm = cfg.arm.upper_arm_len + cfg.arm.forearm_len  # 0.4 m
    target_landing = np.array([catcher.home_pos[0], catcher.home_pos[1],
                               cfg.hover_z])
    RELEASE_ALPHA = math.radians(70.0)
    AIM_OFFSET = 0.30           # ~empirical, see throw_solo.py notes
    EXPECTED_PITCH_RAD = math.radians(7.0)
    VEL_RAMP_S = 0.5
    RUNWAY_MARGIN = 0.4
    RAMP_DURATION = 0.20
    SWEEP_TIMEOUT_S = 4.0

    G = 9.81
    max_apex = cfg.ceiling_z - cfg.ceiling_margin
    apex_target = (cfg.hover_z + max_apex) / 2
    # Release drone body 30 cm inside the thrower's forward play boundary
    # (instead of fitting drone_release_x to a fraction of the throw range).
    # This keeps the drone honestly inside its own play zone at release;
    # vx of the throw is then back-solved to land at target.
    INSIDE_MARGIN = 0.30
    play_x_max = thrower.home_pos[0] + thrower.play_area_max_offset[0]
    drone_release_x = play_x_max - INSIDE_MARGIN
    ee_dx = L_arm * math.sin(RELEASE_ALPHA)
    ee_dz = -L_arm * math.cos(RELEASE_ALPHA)
    release_pos = np.array([drone_release_x + ee_dx, 0.0,
                            cfg.hover_z + ee_dz])
    release_z = release_pos[2]
    vz = math.sqrt(2 * G * max(0.1, apex_target - release_z))
    t_up = vz / G
    apex_z = release_z + vz * vz / (2 * G)
    t_down = math.sqrt(2 * max(0, apex_z - target_landing[2]) / G)
    t_flight = t_up + t_down
    vx = (target_landing[0] + AIM_OFFSET - release_pos[0]) / t_flight
    release_vel = np.array([vx, 0.0, vz])

    decomp = decompose_throw(release_vel, L_arm=L_arm,
                             release_alpha=RELEASE_ALPHA,
                             expected_pitch_rad=EXPECTED_PITCH_RAD)
    cruise_vx = cruise_speed_for_release(decomp)
    sweep_angle = decomp.release_alpha + math.pi / 2
    sweep_time = sweep_angle / decomp.omega + RAMP_DURATION * 0.5
    drone_dx_during_sweep = cruise_vx * sweep_time
    spin_trigger_x = drone_release_x - drone_dx_during_sweep
    vel_ramp_distance = 0.5 * cruise_vx * VEL_RAMP_S
    auto_start_x = spin_trigger_x - vel_ramp_distance - RUNWAY_MARGIN

    print(f"[plan] release_x_drone={drone_release_x:.2f}  "
          f"release_pos={tuple(round(x, 2) for x in release_pos)}  "
          f"release_vel={tuple(round(x, 2) for x in release_vel)}  "
          f"target_land={target_landing.tolist()}")
    print(f"[decomp] α={math.degrees(decomp.release_alpha):.0f}°  "
          f"ω={decomp.omega:.1f}  v_drone={decomp.v_drone_horiz:.2f}  "
          f"cruise={cruise_vx:.2f}")
    print(f"[choreo] auto start x={auto_start_x:.2f}  "
          f"spin trigger x={spin_trigger_x:.2f}  "
          f"runway={spin_trigger_x - auto_start_x:.2f}m")

    m_release_target.set(release_pos)
    m_ball_target.set([target_landing[0], target_landing[1], cfg.hover_z])

    # --- Move thrower to auto_start_x AND pre-position catcher at the
    # predicted intercept point so it's already in place when the ball
    # arrives. Catcher body sits L_arm forward of intercept xy so its
    # backward-pointing EE lands on intercept.
    catcher_intercept_target = np.array([target_landing[0] + L_arm,
                                          target_landing[1], cfg.hover_z])
    catcher.set_target(catcher_intercept_target, vel=(0.0, 0.0, 0.0))
    thrower.set_target([auto_start_x, 0.0, cfg.hover_z], vel=(0.0, 0.0, 0.0))
    for _ in range(int(2.0 / DT)):
        tick("preparing")
        if (np.linalg.norm(thrower.position()
                           - np.array([auto_start_x, 0.0, cfg.hover_z])) < 0.10
                and np.linalg.norm(thrower.velocity()) < 0.2):
            break

    # --- Throw choreography: closed-loop cruise + adaptive trigger + release ---
    cruise_start_t = sim_step[0] * DT
    spin_started = False
    spin_start_t = None
    released = False
    actual_release_pos = None
    grip_v_at_release = None
    trig_reason = None

    while (sim_step[0] * DT - cruise_start_t) < SWEEP_TIMEOUT_S:
        sim_t = sim_step[0] * DT
        elapsed = sim_t - cruise_start_t

        if not released:
            # Closed-loop carrot: pos target = drone's current x, vel
            # target = ramped cruise_vx. Cascade tracks vel feedforward,
            # no overshoot from open-loop position carrot.
            cur_vx = cruise_vx * min(1.0, elapsed / VEL_RAMP_S)
            cur_x = thrower.position()[0]
            thrower.set_target((cur_x, 0.0, cfg.hover_z),
                               vel=(cur_vx, 0.0, 0.0))
        else:
            thrower.set_target(thrower.home_pos, vel=(0.0, 0.0, 0.0))

        # Adaptive spin trigger: predict drone-x at release using current
        # measured vx, fire when it would arrive at drone_release_x.
        cur_vx_meas = thrower.velocity()[0]
        predicted_x_at_release = (thrower.position()[0]
                                  + cur_vx_meas * sweep_time)
        if not spin_started and predicted_x_at_release >= drone_release_x:
            spin_started = True
            spin_start_t = sim_t

        if spin_started and not released:
            t_since_spin = sim_t - spin_start_t
            ramp = min(1.0, t_since_spin / RAMP_DURATION)
            thrower.spin_arm(shoulder_vel=decomp.omega * ramp, elbow_vel=0.0)
            s_pos, _, _, _ = thrower.joint_states()
            if s_pos >= RELEASE_ALPHA:
                actual_release_pos = thrower.gripper_world_position()
                grip_v_at_release = thrower.gripper_world_velocity()
                thrower.release()
                thrower.spin_arm(shoulder_vel=0.0, elbow_vel=0.0)
                m_release_actual.set(actual_release_pos)
                trig_reason = "alpha_reached"
                released = True

        phase_label = ("post_release" if released
                       else "spin" if spin_started else "cruise")
        tick(phase_label)

        # Exit ~0.4 s after release so the catcher loop can take over
        if released and (sim_step[0] * DT - spin_start_t) > 0.4:
            break

    if not released:
        actual_release_pos = thrower.gripper_world_position()
        grip_v_at_release = thrower.gripper_world_velocity()
        thrower.release()
        thrower.spin_arm(0.0, 0.0)
        m_release_actual.set(actual_release_pos)
        trig_reason = "timeout"

    print(f"[t={sim_step[0]*DT:.2f}s] threw ball  "
          f"actual_grip_v={grip_v_at_release.round(2).tolist()}  "
          f"actual_release_pos={actual_release_pos.round(2).tolist()}  "
          f"trigger={trig_reason}")

    # Post-release: hide planning marker, set thrower target home,
    # arm in vel-mode hold (avoids the position-mode jerk we identified).
    m_release_target.hide()
    thrower.spin_arm(0.0, 0.0)
    thrower.go_home()

    # Catcher arm stays in the default wound-up pose (shoulder=-π/2,
    # backward in body frame). With catcher yaw=0 → arm points in world
    # -x direction toward the incoming ball. EE is at catcher_x - L_arm,
    # at catcher_z. Catcher body hovers L_arm forward of the intercept
    # point so the EE lands on the predicted ball xy.
    EE_INTERCEPT_Z = HOVER_Z              # ball arrives at this z
    BODY_HOVER_Z = HOVER_Z                # catcher body z (no climb)
    EE_BACK_OFFSET = L_arm                # how far behind body the EE sits

    # Bump catcher's tilt cap during catch so it can match a fast ball's
    # horizontal velocity. A 4 m/s ball needs ~14 m/s² accel over 250 ms
    # → 55° tilt. Default 35° clips this and saturates the cascade.
    catcher.controller.max_tilt_deg = 60.0
    if hasattr(run, '_pred_xy_filt'):
        delattr(run, '_pred_xy_filt')
    if hasattr(run, '_min_ee_to_ball'):
        delattr(run, '_min_ee_to_ball')

    phase = "tracking"
    steps = int(duration_s / DT)
    for i in range(steps):
        predicted_xy = None
        if phase == "tracking":
            # PERCEIVED ball state — distance-scaled noise from catcher's POV.
            # Closer ball = more accurate (matches real stereo physics).
            bp_obs, bv_obs = perception.observe(viewer_pos=catcher.position())
            bp_true, bv_true = state(ball)
            ee_pos = catcher.gripper_world_position()
            ee_vel = catcher.gripper_world_velocity()
            ee_to_ball_true = float(np.linalg.norm(ee_pos - bp_true))
            ee_to_ball_obs = float(np.linalg.norm(ee_pos - bp_obs))

            # Time-to-intercept based phase switch:
            #   Compute t_intercept = time for ball to descend to EE z.
            #   If t_intercept ≤ T_LEAD (~250 ms), engage soft catch
            #   (velocity-match the predicted ball state at intercept).
            #   Else stay in phase A (hold position at predicted xy).
            T_LEAD = 0.25  # s — how much head start catcher needs to accel
            G = 9.81
            # Solve bp_z + bv_z·t − ½g·t² = EE_INTERCEPT_Z for t (later root)
            a, b, c = -0.5 * G, bv_obs[2], bp_obs[2] - EE_INTERCEPT_Z
            disc = b * b - 4 * a * c
            t_intercept = None
            if disc >= 0:
                sq = np.sqrt(disc)
                roots = [r for r in [(-b + sq) / (2 * a),
                                     (-b - sq) / (2 * a)] if r > 0]
                if roots:
                    t_intercept = max(roots) if bv_obs[2] > 0 else min(roots)
            # Only use the prediction once the ball is COMMITTED to falling
            # toward the catcher (vz < 0 AND past the throw midline). Before
            # then, predict_landing's output is dominated by noise on a small
            # vz signal — wildly bouncing predictions whip the carrot around.
            ball_committed = (bv_obs[2] < -0.5
                              and bp_obs[0] > 0.0)
            predicted_xy_raw, _ = predict_landing(bp_obs, bv_obs,
                                                  target_z=EE_INTERCEPT_Z)

            if ball_committed and predicted_xy_raw is not None:
                # EWMA smoothing now that the prediction is reliable
                if not hasattr(run, '_pred_xy_filt'):
                    run._pred_xy_filt = np.array(predicted_xy_raw)
                else:
                    run._pred_xy_filt = (0.85 * run._pred_xy_filt
                                          + 0.15 * np.array(predicted_xy_raw))
                predicted_xy = run._pred_xy_filt
            else:
                predicted_xy = None

            soft_catch = (ball_committed
                          and t_intercept is not None
                          and t_intercept <= T_LEAD
                          and predicted_xy is not None)
            if soft_catch:
                # Phase B — horizontal soft catch with RAMPED vel target.
                # Vel feedforward ramps from 0 (at start of phase B) to
                # ball's xy velocity (at intercept moment). At t=0 (just
                # entered B): vel target = 0, catcher is at rest. At
                # t=T_LEAD: vel target = full ball xy. Linear ramp →
                # constant accel, smooth tilt, no overshoot.
                #
                # Ramp progress = how much of the T_LEAD window is gone
                # (t_intercept goes T_LEAD → 0).
                progress = max(0.0, min(1.0,
                                        1.0 - t_intercept / T_LEAD))
                vx_cmd = bv_obs[0] * progress
                vy_cmd = bv_obs[1] * progress
                target_body = np.array([predicted_xy[0] + EE_BACK_OFFSET,
                                        predicted_xy[1], BODY_HOVER_Z])
                catcher.set_target(target_body,
                                   vel=(vx_cmd, vy_cmd, 0.0))
                m_ball_target.set([predicted_xy[0], predicted_xy[1],
                                    EE_INTERCEPT_Z])
            elif predicted_xy is not None:
                # Phase A — position-only at predicted intercept.
                catcher.set_target([predicted_xy[0] + EE_BACK_OFFSET,
                                     predicted_xy[1], BODY_HOVER_Z],
                                    vel=(0.0, 0.0, 0.0))
                m_ball_target.set([predicted_xy[0], predicted_xy[1],
                                    EE_INTERCEPT_Z])
            else:
                # Pre-commitment: hold the pre-positioned intercept so
                # we don't waste energy on noisy early predictions.
                catcher.set_target(catcher_intercept_target,
                                   vel=(0.0, 0.0, 0.0))
                m_ball_target.set([target_landing[0], target_landing[1],
                                    EE_INTERCEPT_Z])

            # Diagnostic: per-tick catcher pitch + soft-catch state log
            if not hasattr(run, '_min_ee_to_ball'):
                run._min_ee_to_ball = 1e9
                run._min_at_t = 0.0
                run._min_ee_pos = None
                run._min_ball_pos = None
                run._min_rel_vel = None
                run._catch_trace = []
            if ee_to_ball_true < run._min_ee_to_ball:
                run._min_ee_to_ball = ee_to_ball_true
                run._min_at_t = i * DT
                run._min_ee_pos = ee_pos.copy()
                run._min_ball_pos = bp_true.copy()
                run._min_rel_vel = (bv_true - ee_vel).copy()
            # Log catch-window state when ball is past release plane
            if t_intercept is not None and t_intercept < 0.6:
                _, orn = p.getBasePositionAndOrientation(catcher.body_id)
                _, pitch_now, _ = p.getEulerFromQuaternion(orn)
                run._catch_trace.append((
                    i * DT, t_intercept, soft_catch,
                    catcher.position()[0], catcher.velocity()[0],
                    float(np.degrees(pitch_now)),
                    bp_true.copy(), ee_pos.copy()))

            # Catch trigger: real (true-state) distance + relative velocity.
            # Without 3-finger gripper yet, we still snap a constraint, but
            # only when relative velocity is low (< 1.5 m/s) — closer to
            # a real catch where you can't grab a fast-moving ball.
            rel_vel = float(np.linalg.norm(bv_true - ee_vel))
            if ee_to_ball_true < 0.15 and rel_vel < 1.5:
                if catcher.grasp(ball, max_distance=0.15):
                    phase = "carry_to_cube"
                    print(f"[t={i*DT:.2f}s] caught ball  "
                          f"ee_to_ball={ee_to_ball_true*100:.1f}cm  "
                          f"rel_vel={rel_vel:.2f} m/s")

        elif phase == "carry_to_cube":
            # Translate at hover altitude — descending while translating forces
            # an extreme tilt that kills vertical thrust authority.
            # Catcher needs to BODY-CENTER over cube (since arm will then
            # extend straight down for pickup); subtract the catch-pose
            # EE_BACK_OFFSET because arm is still backward at this point.
            cube_pos, _ = p.getBasePositionAndOrientation(cube)
            above = np.array([cube_pos[0], cube_pos[1], HOVER_Z])
            catcher.set_target(above)
            if np.linalg.norm(catcher.position()[:2] - above[:2]) < 0.15:
                catcher.release()
                # Now switch arm pose: catch-pose (backward, EE behind body)
                # → pickup-pose (straight down, EE below body) so descending
                # puts EE at the cube.
                catcher.extend_arm()
                phase = "descend_to_cube"

        elif phase == "descend_to_cube":
            cube_pos, _ = p.getBasePositionAndOrientation(cube)
            # Target catcher body 0.4 m above cube — that puts the
            # extended arm's EE right at cube level.
            L_arm = cfg.arm.upper_arm_len + cfg.arm.forearm_len
            target_body_z = cube_pos[2] + L_arm + 0.05
            catcher.set_target([cube_pos[0], cube_pos[1], target_body_z])
            if catcher.grasp(cube, max_distance=0.18):
                phase = "lift"
                print(f"[t={i*DT:.2f}s] picked up cube")

        elif phase == "lift":
            catcher.set_target(catcher.home_pos + np.array([0, 0, 0.5]))
            m_ball_target.hide()

        thrower.set_target([-1.5, 0.0, HOVER_Z])
        tick(phase, predicted_xy)

    print(f"[final] phase={phase} catcher_pos={catcher.position()}")
    if hasattr(run, '_min_ee_to_ball'):
        print(f"[catch-diag] closest EE-ball approach: {run._min_ee_to_ball*100:.1f} cm "
              f"at t={run._min_at_t:.2f}s  "
              f"ee_pos={run._min_ee_pos.round(2).tolist()}  "
              f"ball_pos={run._min_ball_pos.round(2).tolist()}  "
              f"rel_vel={np.linalg.norm(run._min_rel_vel):.2f} m/s")
        if run._catch_trace:
            print("\n[catch trace] t  t_int  soft  cat_x   cat_vx  pitch°  ball→ee")
            stride = max(1, len(run._catch_trace) // 20)
            for s in run._catch_trace[::stride]:
                t, ti, sc, cx, cvx, pitch, bp, ee = s
                d = np.linalg.norm(bp - ee)
                print(f"  t={t:5.2f}  ti={ti:.3f}  sc={'Y' if sc else 'N'}  "
                      f"cx={cx:+.2f}  cvx={cvx:+.2f}  pitch={pitch:+5.1f}°  "
                      f"d={d*100:.0f}cm  ball=({bp[0]:+.2f},{bp[1]:+.2f},{bp[2]:.2f})")
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
