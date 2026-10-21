"""
engine/cursor.py

Cursor personalizado para aventuras gráficas. Se dibuja el puntero nosotros
mismos (en vez del del sistema) para poder cambiar de aspecto cuando está
sobre una zona interactiva (hotspot).
"""

import pygame


class Cursor:
    def __init__(self, normal=None, hover=None, size=22):
        self.size = size
        self.normal = normal or self._make_arrow((255, 255, 255), (0, 0, 0))
        self.hover = hover or self._make_cross((255, 80, 80), (0, 0, 0))
        self.visible = True

    def _make_arrow(self, fill, outline):
        size = self.size * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        points = [(4, 2), (4, size - 8), (size // 2 - 2, size // 2 + 2), (size - 4, size // 2 + 2)]
        pygame.draw.polygon(surf, fill, points)
        pygame.draw.polygon(surf, outline, points, 2)
        return surf

    def _make_cross(self, fill, outline):
        size = self.size
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surf, fill, (size // 2, size // 2), size // 2 - 2)
        pygame.draw.circle(surf, outline, (size // 2, size // 2), size // 2 - 2, 2)
        return surf

    def draw(self, surface, hovered=False):
        if not self.visible:
            return
        pygame.mouse.set_visible(False)
        image = self.hover if hovered else self.normal
        pos = pygame.mouse.get_pos()
        surface.blit(image, image.get_rect(center=pos))
