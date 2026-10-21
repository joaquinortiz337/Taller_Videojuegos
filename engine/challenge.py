"""
engine/challenge.py

Reto de opción múltiple con tiempo límite. Sirve para minijuegos de duelo
(por ejemplo, elegir el mejor "insulto" en el fútbol verbal o acertar una
jugada a tiempo).

    reto = Challenge("¿Cuál es la mejor respuesta?",
                     ["opción A", "opción B", "opción C"], correct_index=1,
                     time_limit=5.0)
    reto.start()
"""

import pygame


class Challenge:
    def __init__(self, prompt, options, correct_index, time_limit=5.0,
                 reward=1, penalty=0):
        self.prompt = prompt
        self.options = options
        self.correct_index = correct_index
        self.time_limit = time_limit
        self.reward = reward
        self.penalty = penalty

        self.active = False
        self.time_left = 0.0
        self.selected = 0
        self.result = None  # None=mientras juega, True/False al terminar
        self.font = None

    def start(self):
        self.active = True
        self.time_left = self.time_limit
        self.selected = 0
        self.result = None

    def handle_event(self, event):
        if not self.active:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._answer(self.selected)

    def _answer(self, index):
        self.result = (index == self.correct_index)
        self.active = False

    def update(self, dt):
        if not self.active:
            return
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = 0
            self.result = False
            self.active = False

    def draw(self, surface):
        if self.font is None:
            self.font = pygame.font.Font(None, 30)
            self.big = pygame.font.Font(None, 40)
        w, h = surface.get_size()
        panel = pygame.Rect(0, 0, int(w * 0.8), 260)
        panel.center = (w // 2, h // 2)
        if self.result is None:
            self._draw_play(surface, panel)
        else:
            self._draw_result(surface, panel)

    def _draw_play(self, surface, panel):
        layer = pygame.Surface(panel.size, pygame.SRCALPHA)
        layer.fill((10, 10, 20, 220))
        surface.blit(layer, panel.topleft)
        pygame.draw.rect(surface, (255, 255, 255), panel, 3, border_radius=10)

        prompt = self.big.render(self.prompt, True, (255, 255, 255))
        surface.blit(prompt, (panel.x + 20, panel.y + 18))

        # barra de tiempo
        bar = pygame.Rect(panel.x + 20, panel.y + 60, panel.width - 40, 14)
        pygame.draw.rect(surface, (60, 60, 60), bar)
        ratio = max(0.0, self.time_left / self.time_limit)
        fill = pygame.Rect(bar.x, bar.y, int(bar.width * ratio), bar.height)
        color = (80, 220, 80) if ratio > 0.4 else (240, 180, 40) if ratio > 0.2 else (230, 60, 60)
        pygame.draw.rect(surface, color, fill)

        y = panel.y + 92
        for index, option in enumerate(self.options):
            selected = index == self.selected
            rect = pygame.Rect(panel.x + 24, y, panel.width - 48, 34)
            if selected:
                pygame.draw.rect(surface, (60, 80, 160), rect, border_radius=6)
            color = (255, 255, 120) if selected else (220, 220, 220)
            text = self.font.render(option, True, color)
            surface.blit(text, (rect.x + 8, rect.y + 6))
            y += 40

    def _draw_result(self, surface, panel):
        color = (60, 220, 60) if self.result else (230, 70, 70)
        layer = pygame.Surface(panel.size, pygame.SRCALPHA)
        layer.fill((10, 10, 20, 230))
        surface.blit(layer, panel.topleft)
        pygame.draw.rect(surface, color, panel, 4, border_radius=10)
        msg = "¡Bien!" if self.result else "¡Fallaste!"
        text = self.big.render(msg, True, color)
        surface.blit(text, text.get_rect(center=panel.center))
