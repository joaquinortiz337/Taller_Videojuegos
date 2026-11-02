# juego/scenes/controles_scene.py
import pygame

from juego.scenes.base_menu import MenuBase
from juego import config as C
from juego import estilo as E

CONTROLES = [
    ("Mouse", [
        ("Clic izquierdo", "Agarrar y lanzar (mantener y soltar)"),
        ("Clic izquierdo", "Usar el poder seleccionado"),
        ("Clic en una casilla", "Seleccionar / cancelar un poder"),
        ("Clic derecho corto", "Cancelar el poder"),
        ("Clic derecho + arrastrar", "Mover la cámara"),
        ("Clic en el minimapa", "Saltar a ese punto"),
    ]),
    ("Teclado", [
        ("1  2  3  4", "Seleccionar poder"),
        ("A / D   o   flechas", "Mover la cámara"),
        ("P   o   Esc", "Pausa"),
    ]),
]


def dibujar_controles(surface, y_inicio=150):
    """Dibuja la tabla de controles (la usan la pantalla de controles y la pausa)."""
    fuente_titulo = E.fuente(30)
    fuente_tecla = pygame.font.Font(None, 28)
    fuente = pygame.font.Font(None, 28)
    y = y_inicio
    for titulo, filas in CONTROLES:
        surface.blit(fuente_titulo.render(titulo, True, E.DORADO_CLARO), (150, y))
        y += 40
        for tecla, accion in filas:
            caja = fuente_tecla.render(tecla, True, (255, 255, 255))
            fondo = pygame.Rect(150, y - 3, 300, caja.get_height() + 6)
            pygame.draw.rect(surface, (66, 55, 125), fondo, border_radius=6)
            pygame.draw.rect(surface, E.DORADO, fondo, 1, border_radius=6)
            surface.blit(caja, (fondo.x + 8, y))
            surface.blit(fuente.render(accion, True, E.TEXTO), (470, y))
            y += 34
        y += 14
    return y


class ControlesScene(MenuBase):
    TITULO = "Controles"

    def __init__(self, game):
        super().__init__(game)
        self.boton(20, C.ALTO - 70, 160, 50, "Volver", lambda: self.game.change_scene("menu"))

    def on_enter(self):
        self.game.audio.musica("menu")

    def draw(self, surface):
        self.dibujar_fondo(surface)
        E.panel(surface, (100, 118, C.ANCHO - 200, 418))
        dibujar_controles(surface, 136)
        for b in self.botones:
            b.draw(surface)
