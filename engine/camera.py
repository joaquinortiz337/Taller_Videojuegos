"""
engine/camera.py

Cámara (scrolling) que sigue a una entidad y limita el desplazamiento
al tamaño del mundo.
"""

import pygame


class Camera:
    def __init__(self, screen_width, screen_height, world_width, world_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.world_width = world_width
        self.world_height = world_height
        self.camera_rect = pygame.Rect(0, 0, screen_width, screen_height)

    def apply(self, entity):
        """Devuelve el Rect de la entidad desplazado por la cámara."""
        return entity.rect.move(self.camera_rect.topleft)

    def apply_rect(self, rect):
        """Igual que apply() pero para un Rect cualquiera."""
        return rect.move(self.camera_rect.topleft)

    def update(self, target):
        """Centra la cámara en el objetivo dentro de los límites del mundo."""
        x = -target.rect.centerx + int(self.screen_width / 2)
        y = -target.rect.centery + int(self.screen_height / 2)

        x = min(0, x)
        y = min(0, y)
        x = max(-(self.world_width - self.screen_width), x)
        y = max(-(self.world_height - self.screen_height), y)

        self.camera_rect.topleft = (x, y)
