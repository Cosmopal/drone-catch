"""GameConfig: single source of truth for scene geometry and per-game tunables.

Room dimensions, drone homes + play areas, cube position, hover height, ceiling
margin — all in one place so changing "where the game is played" only touches
this file. Drone PHYSICS (mass, max_thrust, controller gains) stays on the
Drone/CascadeController classes since those are object-intrinsic.

`world.setup(cfg)`, `Drone(home_pos=cfg.thrower_home, ...)`, planner inputs,
and marker placements all read from one `GameConfig` instance in main.py.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class GameConfig:
    # Room
    room_size: float = 12.0          # m, square footprint (x and y)
    wall_height: float = 3.0         # m, also = ceiling_z
    hover_z: float = 1.5             # default hover/catch altitude
    ceiling_margin: float = 0.4      # safety gap below ceiling for ball apex
    floor_margin: float = 0.2        # min backup z (above ground)

    # Thrower (home + asymmetric play area + start position)
    thrower_home: tuple = (-3.0, 0.0, 1.5)
    thrower_start: tuple = (-3.0, 0.0, 1.5)            # where it spawns
    thrower_play_min_offset: tuple = (-2.5, -1.5, -1.3)  # 2.5m back, 1.3m below home
    thrower_play_max_offset: tuple = (+3.0, +1.5, +1.1)  # to centerline (no overlap)

    # Catcher (home + play area + start). Starts off-home so catching isn't trivial.
    catcher_home: tuple = (+3.0, 0.0, 1.5)
    catcher_start: tuple = (+3.0, 0.5, 1.0)            # off-home, slightly low
    catcher_play_min_offset: tuple = (-3.0, -1.5, -1.3)  # to centerline
    catcher_play_max_offset: tuple = (+2.5, +1.5, +1.1)

    # The cube the catcher picks up after delivering the ball
    cube_pos: tuple = (2.0, -1.0, 0.05)

    # Planner brake_decel (m/s²) — empirically observed average during evade,
    # NOT the theoretical max. See docs/iteration_findings.md.
    brake_decel: float = 10.0

    @property
    def ceiling_z(self) -> float:
        return self.wall_height

    @property
    def max_apex(self) -> float:
        return self.ceiling_z - self.ceiling_margin

    def thrower_play_lo(self):
        import numpy as np
        return tuple(np.array(self.thrower_home) + np.array(self.thrower_play_min_offset))

    def thrower_play_hi(self):
        import numpy as np
        return tuple(np.array(self.thrower_home) + np.array(self.thrower_play_max_offset))


# Default game — tweak this single instance to change geometry.
DEFAULT = GameConfig()
