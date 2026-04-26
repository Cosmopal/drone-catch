# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

PyBullet sandbox for prototyping a two-drone "play catch" indoor scenario plus arm-style object pickup. Pure Python; no ROS, no Gazebo. Intended for control/RL prototyping — port to Gazebo+ROS2+PX4 SITL only when targeting real hardware.

## Environment

Always use the `robots` conda env. Do not `pip install` against system Python.

```bash
conda activate robots
python src/main.py             # run demo with GUI
python src/main.py --headless  # no viewer; use for sanity checks
python src/main.py --duration 30

# one-time setup:
# conda create -n robots python=3.11 -y
# conda activate robots && pip install -r requirements.txt
```

`src/main.py` imports siblings as top-level modules (`from world import setup`), so it must be run with `src/` as the working directory or by invoking the file path directly (Python adds the script's directory to `sys.path`). It is *not* a package — there's no `__init__.py`. Don't switch to `python -m src.main` without restructuring.

## Architecture

Three layers, each one file:

1. **World** (`src/world.py`) — `setup(gui)` connects to PyBullet, loads `plane.urdf` from `pybullet_data`, builds four static box walls, sets gravity and a 240 Hz timestep. Returns the connection id. Caller owns `p.stepSimulation()` and `p.disconnect()`.

2. **Drone** (`src/drone.py`) — `Drone` dataclass wraps one quadrotor body. **The dynamics model is intentionally simplified**: every `step()` applies a single net force in the *world frame* (PD on position/velocity + gravity feed-forward, clipped to `max_force`). It does **not** model rotor thrust, body torques, roll/pitch/yaw coupling, or attitude. This is enough to prototype catching trajectories but will not transfer to real flight controllers — anything that depends on underactuation (aggressive maneuvers, wind rejection, sim2real) needs a real attitude/thrust cascade before it's meaningful. The "arm" is also a stand-in: `grasp()` creates a `JOINT_FIXED` PyBullet constraint when the target body is within `max_distance`, and `release()` removes it (optionally setting a launch velocity for throws). There are no arm joints, no contact-based grip, no force closure.

3. **Ball / prediction** (`src/ball.py`) — `spawn_ball()` instantiates a sphere with tuned mass/restitution/damping. `predict_landing(pos, vel, target_z)` solves the ballistic quadratic and returns the *later* (descending) root, used by the catcher to pick an interception XY at hover height. Assumes pure ballistic flight — no drag model.

Demo orchestration (`src/main.py`) is a phase machine: `tracking → carry_to_cube → descend_to_cube → lift`. Each phase reassigns `catcher.set_target(...)` every step; transitions are distance-threshold checks. The thrower's release velocity is open-loop and hand-tuned (`throw_dir * 4.0 + [0,0,3.5]`) — the catcher does the closed-loop work.

### Quadrotor URDF (`assets/quadrotor.urdf`)

Hand-authored: a `0.18 x 0.18 x 0.04` box base with four cosmetic prop disks fixed-jointed in. The disks have tiny inertials (1e-6) purely to silence PyBullet's "no inertial data" warnings — they're cosmetic, fixed-joint, and don't affect dynamics. Only `base_link` matters physically (`MASS = 0.5` in `drone.py` must match the URDF). Non-base reference URDFs (`plane.urdf`, `sphere_small.urdf`, `cube_small.urdf`, `pr2_gripper.urdf`) are pulled live from `pybullet_data` at runtime.

## Tuning gotchas

- `MASS` in `drone.py` and `<mass>` in the URDF must agree, otherwise gravity feed-forward is wrong and the drone drifts vertically.
- When carrying via constraint, the drone's effective mass increases but the gravity feed-forward still uses `MASS` — expect a small steady-state z-error while holding objects. Acceptable for the demo; fix with feed-forward by held mass if it matters.
- `grasp()` checks center-to-center distance only — set `max_distance` based on object size (cube_small ≈ 5cm half-extent, sphere_small ≈ 2.5cm radius). Loose thresholds make catching easier but mask controller errors.
- The catcher's PID gains (`kp=[6,6,12]`, `kd=[4,4,6]`) are tuned for ~1 m/s tracking. Faster intercepts will need re-tuning or a feed-forward velocity term.
- Throw velocity in `main.py` is hand-tuned for the specific drone separation. Change start positions and the open-loop throw will miss; consider closing the loop on the throw before adding more scenarios.

## Deferred / future work

A list of design ideas we've discussed but haven't implemented. Each one has a real motivation (referenced) — don't lose these.

- **Extending arm / 1-DOF revolute or prismatic joint as the gripper.** The current gripper is a fixed offset 8 cm below the body, so the *whole drone* has to chase ball velocity (throw or catch). A real arm would let the drone hover steady while the arm swings/extends. Fixes three problems at once: (1) inefficient mass coupling, (2) catch geometry — gripper can articulate up to receive a ball from above instead of the ball hitting the body's +z surface, (3) throw release — arm can fling without the drone needing high body velocity. This is the right long-term direction.
- **`thrust_mode = "vectored"` on `Drone`.** Optional flag for a drone whose thrust direction is decoupled from body orientation (omnidirectional / tilt-rotor / coaxial-with-gimbal style). Default stays `"underactuated"` (current cascaded controller). Use for prototyping launcher-arm or non-quad concepts. Same conceptual family as the extending-arm idea above — both decouple end-effector dynamics from body dynamics.
- **Real catch geometry.** `Drone.grasp()` currently checks center-to-center distance only and snaps a fixed constraint regardless of orientation. A proper catch needs: (a) check ball is at the *gripper's* world position, not the body's COM; (b) catcher approaches from below/behind rather than colliding with the ball's path; (c) timed pitch-up at the moment of capture so the gripper sweeps up to meet the descending ball ("bird approaching its prey").
- **Pre-throw windup dip.** Real throwers crouch before launching upward — drops the body to gain runway for the upward stroke. Adding a `dip` phase (target z=0.5 before the throw) would give us ~2 m of vertical lane instead of ~1 m, enabling stronger throws without hitting the ceiling.
- **Wider arena and more drone separation.** Currently 6 m room with thrower/catcher 3 m apart; throws are short and the ball barely arcs. Bumping to 10 m room with drones at ±4 m makes the throw and catch genuinely interesting (more flight time, more room for prediction error).
- **Gain scheduling on held mass.** Currently kR/kw are sized for the bare drone. Effective inertia is ~14% higher when holding the ball. PD absorbs it but we'd want explicit scaling for heavier loads.
- **Soft catching (velocity-matched grasp).** The current `grasp()` snaps a fixed constraint the moment the ball is within `max_distance` regardless of relative velocity. In reality this would deliver a hard impulse — the constraint solver yanks the ball to the gripper frame in one step — that on real hardware would shock the airframe and the gripper mechanism. Soft catch: as the catcher closes on the ball, set its `vel_target` to match the ball's velocity (or ramp toward it) so that at grasp time the relative velocity is ~0 and the constraint forms with minimal jerk. Same idea as a person catching a baseball by drawing the glove backward to spread the impulse over more time.
- **Geometric attitude controller singularity at 180°.** With `R_des` 180° from `R`, the vee-mapped error `0.5(R_des^T R − R^T R_des)` is exactly zero — the controller can't tell which way to rotate. Worse, in degenerate planar geometries (e.g., yaw=π and thrust_vec in the same plane as the desired body-x), the cascade becomes blind to the desired tilt and the drone freezes. Worked around so far by avoiding singular configurations (don't pre-yaw drones, don't face-the-ball during tracking). Proper fix: detect the singularity (e.g., `trace(R_des^T R) < threshold AND |e_R| small`) and inject a perturbation. Sensible choices for the perturbation direction, in order of preference: (1) the cross product `body_z × z_des` (rotates body-z toward where it should be), (2) the current angular velocity `ω` (continues whatever rotation is already happening rather than fighting it), (3) a small random axis (last resort if the body is perfectly stationary). Or switch to a quaternion-error formulation when geometric error is near the singularity (hybrid controller).
- **Velocity-feedforward overshoot.** With `set_target(pos, vel)` and a static target, the drone overshoots position because at steady state (drone at pos with target_vel) the controller does nothing — drone keeps moving through. Current workaround is a lookahead target (aim past the desired release point along the velocity vector). Proper fix is a time-parameterized reference trajectory.

## Tests / lint

None configured. There is no test suite, linter, or formatter. The only verification path is running `main.py --headless` and checking that the `[t=...] caught ball` and `[t=...] picked up cube` log lines appear before the duration ends.
