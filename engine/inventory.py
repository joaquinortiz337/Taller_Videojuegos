"""
engine/inventory.py

Inventario sencillo para aventuras gráficas y RPG.
"""

import pygame


class Item:
    def __init__(self, name, image=None, description="", usable=True):
        self.name = name
        self.image = image
        self.description = description
        self.usable = usable


class Inventory:
    def __init__(self, capacity=8):
        self.capacity = capacity
        self.items = []
        self.selected = None

    def add(self, item):
        if len(self.items) < self.capacity and not self.has(item.name):
            self.items.append(item)
            return True
        return False

    def remove(self, name):
        self.items = [i for i in self.items if i.name != name]
        if self.selected and self.selected.name == name:
            self.selected = None

    def has(self, name):
        return any(i.name == name for i in self.items)

    def get(self, name):
        for i in self.items:
            if i.name == name:
                return i
        return None

    def select(self, name):
        self.selected = self.get(name)

    def handle_event(self, event, origin, slot=56):
        """Permite seleccionar un objeto con click. `origin` = (x, y) del panel."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, item in enumerate(self.items):
                rect = pygame.Rect(origin[0], origin[1] + index * slot, slot, slot)
                if rect.collidepoint(event.pos):
                    self.selected = item
                    return item
        return None

    def draw(self, surface, origin, slot=56):
        x, y = origin
        panel = pygame.Rect(x - 6, y - 6, slot + 12,
                            slot * self.capacity + 12)
        pygame.draw.rect(surface, (0, 0, 0, 150), panel, border_radius=6)
        pygame.draw.rect(surface, (220, 220, 220), panel, 2, border_radius=6)

        font = pygame.font.Font(None, 22)
        for index in range(self.capacity):
            rect = pygame.Rect(x, y + index * slot, slot, slot)
            pygame.draw.rect(surface, (70, 70, 90), rect, 1)
            if index < len(self.items):
                item = self.items[index]
                if item.image:
                    img = pygame.transform.scale(item.image, (slot - 10, slot - 10))
                    surface.blit(img, img.get_rect(center=rect.center))
                else:
                    label = font.render(item.name[:6], True, (240, 240, 240))
                    surface.blit(label, label.get_rect(center=rect.center))
                if self.selected is item:
                    pygame.draw.rect(surface, (255, 220, 0), rect, 3)
