"""
engine/particle.py

Sistema de partículas muy simple (chispas, polvo, explosiones...).
Se usa, por ejemplo, al golpear en el Arkanoid, al saltar en el
plataformero o como fondo estrellado.
"""

import random

import pygame


class Particle:
    def __init__(self, x, y, velocity, color, life, size,
                 gravity=0.0, fade=True):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(velocity)
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.gravity = gravity
        self.fade = fade

    def update(self, dt):
        self.vel.y += self.gravity * dt
        self.pos += self.vel * dt
        self.life -= dt

    @property
    def dead(self):
        return self.life <= 0

    def draw(self, surface):
        if self.size <= 0:
            return
        alpha = 255
        if self.fade:
            alpha = max(0, min(255, int(255 * (self.life / self.max_life))))
        radius = max(1, int(self.size))
        layer = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(layer, (*self.color, alpha), (radius, radius), radius)
        surface.blit(layer, (self.pos.x - radius, self.pos.y - radius))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, count=20, speed=(60, 220), color=(255, 200, 60),
             life=(0.3, 0.8), size=(2, 5), gravity=250.0, angle=0.0, spread=360.0):
        """Crea un "chorro" de partículas desde (x, y)."""
        for _ in range(count):
            a = angle + random.uniform(-spread / 2, spread / 2)
            s = random.uniform(*speed)
            rad = pygame.math.Vector2(1, 0).rotate(a) * s
            self.particles.append(
                Particle(x, y, (rad.x, rad.y),
                         color if isinstance(color, tuple) else (255, 255, 255),
                         random.uniform(*life), random.uniform(*size), gravity)
            )

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.dead]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    def __len__(self):
        return len(self.particles)
