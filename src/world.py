"""PyBullet world setup: indoor room with floor and four walls."""
import pybullet as p
import pybullet_data


def setup(gui: bool = True, room_size: float = 12.0, wall_height: float = 3.0):
    cid = p.connect(p.GUI if gui else p.DIRECT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.resetSimulation()
    p.setGravity(0, 0, -9.81)
    p.setTimeStep(1.0 / 240.0)
    p.setRealTimeSimulation(0)

    p.loadURDF("plane.urdf")

    # Four walls as static collision boxes
    half = room_size / 2.0
    h = wall_height / 2.0
    thickness = 0.05
    walls = [
        ([half, 0, h], [thickness, half, h]),
        ([-half, 0, h], [thickness, half, h]),
        ([0, half, h], [half, thickness, h]),
        ([0, -half, h], [half, thickness, h]),
    ]
    for pos, half_extents in walls:
        col = p.createCollisionShape(p.GEOM_BOX, halfExtents=half_extents)
        # Collision only — visuals would render opaque in PyBullet's
        # tinyrenderer (alpha not blended). Visual reference for the arena
        # comes from the play-area wireframe outlines drawn in main.py.
        p.createMultiBody(baseMass=0, baseCollisionShapeIndex=col,
                          baseVisualShapeIndex=-1, basePosition=pos)

    # Ceiling at z = wall_height. Collision only (no visual) — PyBullet's
    # tinyrenderer doesn't blend alpha well, and a semi-transparent ceiling
    # plane covering the room blocks any top-down camera. The ball still
    # bounces off it because the collision shape is present.
    ceiling_half = [half, half, thickness]
    col = p.createCollisionShape(p.GEOM_BOX, halfExtents=ceiling_half)
    p.createMultiBody(baseMass=0, baseCollisionShapeIndex=col,
                      baseVisualShapeIndex=-1,  # no visual
                      basePosition=[0, 0, wall_height])

    if gui:
        p.resetDebugVisualizerCamera(cameraDistance=4.5,
                                     cameraYaw=45, cameraPitch=-25,
                                     cameraTargetPosition=[0, 0, 1.0])
    return cid
