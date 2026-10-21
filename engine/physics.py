"""
engine/physics.py

`PhysicsMixin` añade físicas de PyMunk a un GameObject usando herencia
múltiple:

    class Bola(GameObject, PhysicsMixin):
        def __init__(self, x, y, r, space):
            super().__init__(x, y, imagen)
            self.original_image = self.image
            self.init_physics_circle(space, mass=10, radius=r,
                                     elasticity=0.6, friction=0.8)

        def update(self):
            self.update_from_physics()
"""

import math

import pygame
import pymunk


class PhysicsMixin:
    """Añade un cuerpo/collider de PyMunk a un GameObject."""

    def init_physics_circle(self, space, mass, radius, elasticity, friction):
        """Crea un cuerpo físico circular."""
        moment = pymunk.moment_for_circle(mass, 0, radius)
        self.body = pymunk.Body(mass, moment)
        self.body.position = self.rect.center
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = elasticity
        self.shape.friction = friction
        self.shape.parent = self  # referencia inversa al objeto del juego
        space.add(self.body, self.shape)

    def init_physics_box(self, space, mass, elasticity, friction):
        """Crea un cuerpo físico rectangular."""
        size = self.rect.size
        moment = pymunk.moment_for_box(mass, size)
        self.body = pymunk.Body(mass, moment)
        self.body.position = self.rect.center
        self.shape = pymunk.Poly.create_box(self.body, size)
        self.shape.elasticity = elasticity
        self.shape.friction = friction
        self.shape.parent = self
        space.add(self.body, self.shape)

    def update_from_physics(self):
        """Sincroniza la posición y la rotación del sprite con el cuerpo."""
        self.rect.center = self.body.position
        # PyMunk usa radianes; Pygame usa grados.
        self.image = pygame.transform.rotate(
            self.original_image, -math.degrees(self.body.angle)
        )
        self.rect = self.image.get_rect(center=self.rect.center)
