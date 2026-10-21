"""
engine/dialogue_manager.py

Muestra mensajes/diálogos en pantalla, con duración opcional.
"""

import pygame


class DialogueManager:
    def __init__(self, screen, font_size=50, color=(255, 255, 255)):
        self.screen = screen
        self.font = pygame.font.Font(None, font_size)
        self.color = color

        self.active_message = None
        self.message_surface = None
        self.message_rect = None
        self.message_timer = 0
        self.message_duration = 0  # 0 => mensaje permanente

    def show_message(self, text, duration_seconds=0, position="center"):
        """Muestra un mensaje. Si la duración es 0, es permanente."""
        self.active_message = text
        self.message_surface = self.font.render(text, True, self.color)

        screen_rect = self.screen.get_rect()
        if position == "center":
            self.message_rect = self.message_surface.get_rect(center=screen_rect.center)
        elif position == "top":
            self.message_rect = self.message_surface.get_rect(
                centerx=screen_rect.centerx, top=20
            )
        else:
            self.message_rect = self.message_surface.get_rect(center=screen_rect.center)

        self.message_duration = duration_seconds * 1000
        self.message_timer = pygame.time.get_ticks()

    def update(self):
        if self.message_duration > 0:
            if pygame.time.get_ticks() - self.message_timer > self.message_duration:
                self.clear_message()

    def draw(self):
        if self.message_surface:
            self.screen.blit(self.message_surface, self.message_rect)

    def clear_message(self):
        self.active_message = None
        self.message_surface = None
        self.message_duration = 0
