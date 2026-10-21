"""
engine/hotspot.py

Zonas interactivas para aventuras gráficas: una región de la pantalla que
reacciona al pasar/click del ratón (abrir una puerta, coger un objeto,
hablar con un personaje...).
"""

import pygame


class Hotspot:
    def __init__(self, rect, name="", callback=None, cursor="hand",
                 visible=False, color=(255, 255, 0)):
        self.rect = pygame.Rect(rect)
        self.name = name
        self.callback = callback
        self.cursor = cursor
        self.visible = visible
        self.color = color

    def contains(self, pos):
        return self.rect.collidepoint(pos)

    def activate(self):
        if self.callback:
            self.callback(self)

    def handle_event(self, event):
        """Devuelve True si el click cayó dentro de la zona."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.contains(event.pos):
                self.activate()
                return True
        return False

    def draw(self, surface):
        """Dibuja el contorno (solo para depurar)."""
        if self.visible:
            pygame.draw.rect(surface, self.color, self.rect, 2)
