"""Measurement only, per lead instruction -- do NOT change placement, add a
settle phase, or adjust anything. Checks whether the ball is placed already
interpenetrating a finger at t=0 (before any stepSimulation), across offsets
and directions, using the exact same setup as run_cell (FixedGripper, ready
pose, finger dynamics, prep_strategy, offset placement)."""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
import pybullet as p
import cage_harness as ch


def t0_contacts(offset_m, direction):
    p.connect(p.DIRECT)
    try:
        ch.setup_physics()
        urdf = ch.variants.ensure_variant(4)
        g = ch.FixedGripper(urdf)
        g.set_ready(ch.READY_SPLAYED)
        g.set_finger_dynamics()
        g.prep_strategy("prb")
        az = (math.pi / 2 if direction == "finger"
             else math.pi / 2 + math.pi / 4)
        off = offset_m * np.array([math.cos(az), math.sin(az), 0.0])
        cup = g.cup_world()
        ball = ch.setup_ball(cup + off)
        # NO stepSimulation before this check -- exactly what the lead asked.
        p.performCollisionDetection()
        pts = p.getContactPoints(bodyA=g.body, bodyB=ball)
        results = []
        for c in pts:
            link_a = c[3]
            fid = None
            for k, segs in enumerate(g.finger_joints):
                if link_a in segs:
                    fid = k
                    break
            results.append({"link": link_a, "finger": fid, "contactDistance": c[8],
                           "normalForce_at_query_time": c[9]})
        return results
    finally:
        p.disconnect()


def first_tick_force(offset_m, direction, contact_scale):
    BASE_K = ch.CONTACT_STIFFNESS
    BASE_C = ch.CONTACT_DAMPING
    ch.CONTACT_STIFFNESS = BASE_K * contact_scale
    ch.CONTACT_DAMPING = BASE_C * contact_scale
    p.connect(p.DIRECT)
    try:
        ch.setup_physics()
        urdf = ch.variants.ensure_variant(4)
        g = ch.FixedGripper(urdf)
        g.set_ready(ch.READY_SPLAYED)
        g.set_finger_dynamics()
        g.prep_strategy("prb")
        az = (math.pi / 2 if direction == "finger"
             else math.pi / 2 + math.pi / 4)
        off = offset_m * np.array([math.cos(az), math.sin(az), 0.0])
        cup = g.cup_world()
        ball = ch.setup_ball(cup + off)
        g.hold_arm_rigid()
        g.apply_close("prb", ball_id=ball, progress=0.0)
        p.stepSimulation()   # exactly one physics step
        pts = p.getContactPoints(bodyA=g.body, bodyB=ball)
        forces = [c[9] for c in pts]
        return forces
    finally:
        p.disconnect()
        ch.CONTACT_STIFFNESS, ch.CONTACT_DAMPING = BASE_K, BASE_C


print("=== t=0 contact check (before any stepSimulation) ===")
OFFSETS = [0.015, 0.025, 0.035, 0.045, 0.050, 0.055]
DIRECTIONS = ["finger", "gap"]
penetrating_cells = []
for off in OFFSETS:
    for direction in DIRECTIONS:
        contacts = t0_contacts(off, direction)
        n = len(contacts)
        min_dist = min((c["contactDistance"] for c in contacts), default=None)
        fingers = sorted(set(c["finger"] for c in contacts if c["finger"] is not None))
        print(f"off={off*100:.1f}cm dir={direction:6s} | n_contacts={n} "
             f"min_contactDistance={min_dist if min_dist is None else f'{min_dist*1000:.3f}mm'} "
             f"fingers={fingers}")
        if min_dist is not None and min_dist < 0:
            penetrating_cells.append((off, direction, min_dist))

print("\n=== first-tick contact normal force @ contact scale {0.33,1.0,3.0} "
     "(cells with t=0 penetration only) ===")
for off, direction, min_dist in penetrating_cells:
    for scale in [0.33, 1.0, 3.0]:
        forces = first_tick_force(off, direction, scale)
        fstr = [f"{f:.2f}N" for f in forces]
        print(f"off={off*100:.1f}cm dir={direction:6s} contact_scale={scale:.2f} | "
             f"tick1_normal_forces={fstr}")
