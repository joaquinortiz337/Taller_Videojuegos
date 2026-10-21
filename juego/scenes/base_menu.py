# juego/scenes/base_menu.py
import pygame

from engine.ui import Scene  # Hereda del motor
from juego.ui_extra import SoundButton
from juego import config as C


class MenuBase(Scene):
    """Base para todas las pantallas de menú: título + lista de botones con sonido."""
    TITULO = ""

    def __init__(self, game):
        super().__init__(game)
        self.fuente_titulo = pygame.font.Font(None, 80)
        self.fuente = pygame.font.Font(None, 34)
        self.fuente_chica = pygame.font.Font(None, 26)
        self.botones = []

    def boton(self, x, y, ancho, alto, texto, accion):
        b = SoundButton(x, y, ancho, alto, texto, accion, self.game.assets.sounds.get("click"))
        self.botones.append(b)
        return b

    def handle_events(self, events):
        for e in events:
            for b in list(self.botones):
                b.handle_event(e)

    def dibujar_fondo(self, surface):
        surface.fill(C.COLOR_CIELO)
        if self.TITULO:
            t = self.fuente_titulo.render(self.TITULO, True, C.COLOR_TEXTO)
            surface.blit(t, t.get_rect(center=(C.ANCHO // 2, 80)))

    def draw(self, surface):
        self.dibujar_fondo(surface)
        for b in self.botones:
            b.draw(surface)
