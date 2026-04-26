"""PyBullet world setup: indoor room with floor and four walls."""
import pybullet as p
import pybullet_data


def setup(gui: bool = True, room_size: float = 6.0, wall_height: float = 3.0):
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
        vis = p.createVisualShape(p.GEOM_BOX, halfExtents=half_extents,
                                  rgbaColor=[0.85, 0.85, 0.9, 0.25])
        p.createMultiBody(baseMass=0, baseCollisionShapeIndex=col,
                          baseVisualShapeIndex=vis, basePosition=pos)

    if gui:
        p.resetDebugVisualizerCamera(cameraDistance=4.5,
                                     cameraYaw=45, cameraPitch=-25,
                                     cameraTargetPosition=[0, 0, 1.0])
    return cid
