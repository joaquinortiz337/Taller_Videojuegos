# juego/scenes/base_menu.py
from engine.ui import Scene  # Hereda del motor
from juego.ui_extra import SoundButton
from juego import config as C
from juego import estilo as E


class MenuBase(Scene):
    """Base para todas las pantallas de menú: fondo animado + título dorado + botones con sonido."""
    TITULO = ""
    FONDO_MENU = True    # el juego mueve el fondo animado mientras esta pantalla está activa

    def __init__(self, game):
        super().__init__(game)
        self.fuente = E.fuente(28)
        self.fuente_chica = E.fuente(21)
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
        self.game.fondo_menu.draw(surface)
        if self.TITULO:
            t = E.titulo(self.TITULO, 64)
            surface.blit(t, t.get_rect(center=(C.ANCHO // 2, 75)))

    def draw(self, surface):
        self.dibujar_fondo(surface)
        for b in self.botones:
            b.draw(surface)
