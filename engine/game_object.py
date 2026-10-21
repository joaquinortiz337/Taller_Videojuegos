"""
engine/game_object.py

Objeto base para todo lo que aparece en pantalla.

Puede representar:
- Un sprite estático (una sola Surface).
- Una animación (lista de Surfaces que se van rotando).
"""

import pygame


class GameObject(pygame.sprite.Sprite):
    """
    Sprite base con soporte de imagen estática o animación por frames.
    """

    def __init__(self, x, y, frames, anim_speed=0.1):
        super().__init__()

        if isinstance(frames, list):
            self.frames = frames
            self.is_animated = True
            self.current_frame = 0
            self.image = self.frames[self.current_frame]
            self.anim_speed = anim_speed  # frames avanzados por tick
            self.anim_timer = 0.0
        else:
            # Una sola Surface => estático
            self.frames = [frames]
            self.is_animated = False
            self.image = frames

        self.rect = self.image.get_rect(center=(x, y))

    def update_animation(self):
        """Avanza el frame de la animación cuando corresponde."""
        if not self.is_animated or len(self.frames) < 2:
            return

        self.anim_timer += self.anim_speed
        if self.anim_timer >= 1:
            self.anim_timer -= 1
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]

    def update(self, *args, **kwargs):
        """Actualización genérica: por defecto solo anima."""
        self.update_animation()

    def draw(self, surface):
        surface.blit(self.image, self.rect)
