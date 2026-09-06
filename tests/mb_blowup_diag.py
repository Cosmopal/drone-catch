"""Diagnostic (not a fix): at the blow-up corner (prb, n4, 5.0cm, finger,
substep=8, contact x3.0), read per-JOINT angles (not the aggregate flex
sum) against the URDF's per-segment limits (-0.8, 2.0 rad, from
assets/make_gripper_urdf.py), and inspect the raw 26-direction escape-
margin bisection output to check whether EM=0.16g is a real escape or the
margin computation itself hitting instability."""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
import pybullet as p
import cage_harness as ch

BASE_SS = ch.SUBSTEP
BASE_K = ch.CONTACT_STIFFNESS
BASE_C = ch.CONTACT_DAMPING


def set_corner():
    ch.SUBSTEP, ch.SIM_DT = 8, ch.DT / 8
    ch.CONTACT_STIFFNESS = BASE_K * 3.0
    ch.CONTACT_DAMPING = BASE_C * 3.0


def reset():
    ch.SUBSTEP, ch.SIM_DT = BASE_SS, ch.DT / BASE_SS
    ch.CONTACT_STIFFNESS, ch.CONTACT_DAMPING = BASE_K, BASE_C


# --- per-joint angle check ---
set_corner()
p.connect(p.DIRECT)
ch.setup_physics()
urdf = ch.variants.ensure_variant(4)
g = ch.FixedGripper(urdf)
g.set_ready(ch.READY_SPLAYED)
g.set_finger_dynamics()
g.prep_strategy("prb")
az = math.pi / 2
off = 0.050 * np.array([math.cos(az), math.sin(az), 0.0])
cup = g.cup_world()
ball = ch.setup_ball(cup + off)
n_close = (ch.CLOSE_STEPS + ch.SETTLE_STEPS) * ch.SUBSTEP
for s in range(n_close):
    g.hold_arm_rigid()
    g.apply_close("prb", ball_id=ball, progress=s / n_close)
    p.stepSimulation()

print("=== per-joint angles vs URDF limits (-0.8, 2.0 rad) ===")
for fid, segs in enumerate(g.finger_joints):
    angs = [p.getJointState(g.body, j)[0] for j in segs]
    flags = ["AT/BEYOND LIMIT" if (a >= 1.99 or a <= -0.79) else "ok" for a in angs]
    print(f"finger {fid}: segs={['%.3f' % a for a in angs]}  {flags}")

seated = np.array(p.getBasePositionAndOrientation(ball)[0])
print(f"\nball seated pos: {seated}  cup: {cup}  dist from cup: {np.linalg.norm(seated - cup):.4f}m")
p.disconnect()
reset()

# --- raw escape-margin bisection output ---
print("\n=== raw escape-margin bisection (26 directions) ===")
set_corner()
r = ch.run_cell("prb", 4, 0.050, "finger", quality=True)
reset()
print("escape_margin_g:", r["escape_margin_g"])
print("weakest_dir:", r["weakest_dir"])
print("margins (m/s^2, 26 dirs):", [round(m, 2) for m in r["margins"]])
print("survived:", r["survived"], "/", len(r["margins"]))
print("seat_off (cm):", r["seat_off"] * 100)
