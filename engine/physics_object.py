"""
engine/physics_object.py

Piezas reutilizables de PyMunk para construir juegos físicos (billar,
resortera, minigolf...): cuerpos estáticos (paredes, suelo) y un
`PhysicsObject` genérico listo para usar.

Incluye "tipos de colisión" para que los callbacks de PyMunk sepan qué
chocó contra qué.
"""

import pymunk

from engine.game_object import GameObject
from engine.physics import PhysicsMixin

# Tipos de colisión (se usan en add_collision_handler)
COLLISION_DEFAULT = 1
COLLISION_BALL = 2
COLLISION_BLOCK = 3
COLLISION_PLAYER = 4
COLLISION_WALL = 5


def add_static_segment(space, a, b, thickness=5, elasticity=0.6, friction=0.6,
                       collision_type=COLLISION_WALL):
    seg = pymunk.Segment(space.static_body, a, b, thickness)
    seg.elasticity = elasticity
    seg.friction = friction
    seg.collision_type = collision_type
    space.add(seg)
    return seg


def add_walls(space, width, height, thickness=5, elasticity=0.6, friction=0.6):
    """Crea el marco del mundo (suelo + paredes)."""
    return [
        add_static_segment(space, (thickness, thickness),
                           (thickness, height - thickness), thickness, elasticity, friction),
        add_static_segment(space, (width - thickness, thickness),
                           (width - thickness, height - thickness), thickness, elasticity, friction),
        add_static_segment(space, (thickness, height - thickness),
                           (width - thickness, height - thickness), thickness, elasticity, friction),
        add_static_segment(space, (thickness, thickness),
                           (width - thickness, thickness), thickness, elasticity, friction),
    ]


class PhysicsObject(GameObject, PhysicsMixin):
    """
    GameObject con cuerpo físico (caja o círculo).

    Ejemplo:
        bola = PhysicsObject(x, y, imagen, space=space, shape="circle",
                             radius=12, mass=1, elasticity=0.9,
                             collision_type=COLLISION_BALL)
    """

    def __init__(self, x, y, image, space, mass=1.0, shape="box",
                 elasticity=0.5, friction=0.6, radius=None,
                 collision_type=COLLISION_DEFAULT):
        super().__init__(x, y, image)
        self.original_image = self.image

        if shape == "circle":
            self.init_physics_circle(space, mass, radius or self.rect.width // 2,
                                     elasticity, friction)
        else:
            self.init_physics_box(space, mass, elasticity, friction)

        self.shape.collision_type = collision_type

    def update(self, *args, **kwargs):
        self.update_from_physics()
