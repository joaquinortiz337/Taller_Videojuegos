"""
engine/ui_elements.py

Piezas de interfaz reutilizables para los menús y el HUD: etiquetas,
paneles, barras de progreso y barras de vida.
"""

import pygame


class Label:
    def __init__(self, text, pos, size=32, color=(255, 255, 255),
                 align="topleft", font=None):
        self.text = text
        self.pos = pos
        self.color = color
        self.align = align
        self.font = font or pygame.font.Font(None, size)

    def draw(self, surface):
        image = self.font.render(self.text, True, self.color)
        rect = image.get_rect(**{self.align: self.pos})
        surface.blit(image, rect)
        return rect


class Panel:
    def __init__(self, rect, color=(0, 0, 0, 160), border=None, border_radius=8):
        self.rect = pygame.Rect(rect)
        self.color = color
        self.border = border
        self.border_radius = border_radius

    def draw(self, surface):
        layer = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        layer.fill(self.color)
        surface.blit(layer, self.rect.topleft)
        if self.border:
            pygame.draw.rect(surface, self.border, self.rect, 2,
                             border_radius=self.border_radius)


class ProgressBar:
    def __init__(self, rect, maximum=100, value=100,
                 color=(80, 220, 80), background=(50, 50, 50)):
        self.rect = pygame.Rect(rect)
        self.maximum = maximum
        self.value = value
        self.color = color
        self.background = background

    def set(self, value):
        self.value = max(0, min(self.maximum, value))

    def draw(self, surface):
        pygame.draw.rect(surface, self.background, self.rect, border_radius=4)
        ratio = self.value / self.maximum if self.maximum else 0
        fill = pygame.Rect(self.rect.x, self.rect.y,
                           int(self.rect.width * ratio), self.rect.height)
        pygame.draw.rect(surface, self.color, fill, border_radius=4)
        pygame.draw.rect(surface, (230, 230, 230), self.rect, 2, border_radius=4)


class HealthBar(ProgressBar):
    def draw(self, surface):
        ratio = self.value / self.maximum if self.maximum else 0
        if ratio > 0.5:
            self.color = (80, 220, 80)
        elif ratio > 0.25:
            self.color = (240, 190, 40)
        else:
            self.color = (230, 60, 60)
        super().draw(surface)
