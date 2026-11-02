# juego/scenes/menu_scene.py
import math

import pygame

from juego.scenes.base_menu import MenuBase
from juego import config as C
from juego import estilo as E


class MenuScene(MenuBase):
    """Menú principal: logo, y Jugar, Controles, Opciones, Créditos, Salir."""
    TITULO = ""   # el logo se dibuja aparte (más grande y flotando)

    def __init__(self, game):
        super().__init__(game)
        cx = C.ANCHO // 2 - 140
        self.boton(cx, 205, 280, 54, "Jugar", lambda: self.game.change_scene("niveles"))
        self.boton(cx, 272, 280, 54, "Controles", lambda: self.game.change_scene("controles"))
        self.boton(cx, 339, 280, 54, "Opciones", lambda: self.game.change_scene("opciones"))
        self.boton(cx, 406, 280, 54, "Créditos", lambda: self.game.change_scene("creditos"))
        self.boton(cx, 473, 280, 54, "Salir", self.game.salir)
        self.logo = E.titulo(C.TITULO, 84, grosor=5)

    def on_enter(self):
        self.game.audio.musica("menu")

    def draw(self, surface):
        self.dibujar_fondo(surface)
        flota = math.sin(pygame.time.get_ticks() / 600) * 5
        surface.blit(self.logo, self.logo.get_rect(center=(C.ANCHO // 2, 105 + flota)))
        for b in self.botones:
            b.draw(surface)
