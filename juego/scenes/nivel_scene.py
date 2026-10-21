# juego/scenes/nivel_scene.py
import pygame

from juego.scenes.base_menu import MenuBase
from juego.ui_extra import dibujar_estrella, dibujar_texto_multilinea
from juego.niveles import NIVELES_POR_ID, REQUISITOS_ESTRELLAS
from juego import config as C


class NivelScene(MenuBase):
    """Nivel seleccionado: info, requisitos de estrellas y elección de dificultad."""

    def __init__(self, game, id_nivel):
        super().__init__(game)
        self.nivel = NIVELES_POR_ID[id_nivel]
        self.dificultad = "normal"

        self.botones_dif = {}
        x = 560
        for i, (clave, d) in enumerate(C.DIFICULTADES.items()):
            b = self.boton(x, 200 + i * 70, 220, 55, d["nombre"],
                           lambda c=clave: self._elegir(c))
            self.botones_dif[clave] = b
        self._elegir("normal")

        self.boton(560, 450, 220, 60, "¡Jugar!", self._jugar)
        self.boton(20, C.ALTO - 70, 160, 50, "Volver", lambda: self.game.change_scene("niveles"))

    def _elegir(self, clave):
        self.dificultad = clave
        for c, b in self.botones_dif.items():
            b.seleccionado = (c == clave)

    def _jugar(self):
        self.game.change_scene("juego", id_nivel=self.nivel["id"], dificultad=self.dificultad)

    def draw(self, surface):
        self.dibujar_fondo(surface)
        t = self.fuente_titulo.render(self.nivel["nombre"], True, C.COLOR_TEXTO)
        surface.blit(t, (60, 50))
        dibujar_texto_multilinea(surface, self.fuente_chica, self.nivel["descripcion"],
                                 C.COLOR_TEXTO, 60, 120, 440)

        # Requisitos de cada estrella (las conseguidas, en amarillo)
        e = self.game.progreso.estrellas(self.nivel["id"])
        conseguidas = [e["desempeno"] >= 1, e["desempeno"] >= 2, e["desempeno"] >= 3,
                       e["dificil"], e["experto"]]
        y = 230
        surface.blit(self.fuente.render("Estrellas", True, C.COLOR_TEXTO), (60, y - 40))
        for requisito, ok in zip(REQUISITOS_ESTRELLAS, conseguidas):
            dibujar_estrella(surface, (75, y + 10), 12, llena=ok)
            surface.blit(self.fuente_chica.render(requisito, True, C.COLOR_TEXTO), (100, y))
            y += 40

        surface.blit(self.fuente.render("Dificultad", True, C.COLOR_TEXTO), (560, 160))
        for b in self.botones:
            b.draw(surface)

    def on_enter(self):
        self.game.audio.musica("menu")
