"""
engine/ui.py

Elementos de interfaz reutilizables por cualquier escena.

- Scene: clase base para todas las escenas del juego.
- Button: botón sencillo con estado "hover" y callback.
"""

import pygame


class Scene:
    """
    Clase base para todas las escenas.

    Recibe una referencia al juego (`game`) para poder usar sus gestores
    (assets, audio, screen, change_scene...) y para cambiar de escena.
    """

    def __init__(self, game):
        self.game = game

    # Se llama justo al ENTRAR a la escena (después de crearla).
    def on_enter(self):
        pass

    # Se llama justo al SALIR de la escena.
    def on_exit(self):
        pass

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self, surface):
        pass


class Button:
    """Botón rectangular con texto, efecto hover y callback."""

    def __init__(self, x, y, width, height, text, callback,
                 font_size=40, color=(50, 50, 80), hover_color=(80, 80, 110),
                 text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.font = pygame.font.Font(None, font_size)
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surface):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        color = self.hover_color if hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (20, 20, 30), self.rect, width=2, border_radius=8)
        text_surf = self.font.render(self.text, True, self.text_color)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))
