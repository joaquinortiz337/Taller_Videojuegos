# juego/scenes/nivel_scene.py
import pygame

from juego.scenes.base_menu import MenuBase
from juego.scenes.seleccion_scene import COLORES_NIVEL
from juego.ui_extra import dibujar_estrella, dibujar_texto_multilinea
from juego.niveles import NIVELES_POR_ID, REQUISITOS_ESTRELLAS
from juego import config as C
from juego import estilo as E

# Color de cada dificultad (arriba y abajo del degradé del botón) y qué cambia
COLORES_DIFICULTAD = {
    "normal": ((80, 165, 85), (40, 100, 50)),
    "dificil": ((225, 145, 50), (150, 85, 20)),
    "experto": ((205, 70, 65), (125, 30, 35)),
}


def _descripcion_dificultad(d):
    if d["cantidad"] == 1.0:
        return "La experiencia pensada para el nivel."
    return (f"+{round((d['cantidad'] - 1) * 100)}% de enemigos, más a la vez y "
            f"aparecen un {round((d['ritmo'] - 1) * 100)}% más rápido.")


class NivelScene(MenuBase):
    """Nivel seleccionado: info, requisitos de estrellas y elección de dificultad."""

    def __init__(self, game, id_nivel):
        super().__init__(game)
        self.nivel = NIVELES_POR_ID[id_nivel]
        self.dificultad = "normal"
        self.fuente_texto = pygame.font.Font(None, 26)

        self.botones_dif = {}
        for i, (clave, d) in enumerate(C.DIFICULTADES.items()):
            b = self.boton(600, 175 + i * 66, 300, 54, d["nombre"], lambda c=clave: self._elegir(c))
            b.color_arriba, b.color_abajo = COLORES_DIFICULTAD.get(clave, (None, None))
            self.botones_dif[clave] = b
        self._elegir("normal")

        jugar = self.boton(600, 440, 300, 64, "¡Jugar!", self._jugar)
        jugar.color_arriba, jugar.color_abajo, jugar.color_texto = (255, 215, 95), (205, 135, 35), (70, 35, 10)
        jugar.font = E.fuente(34)
        self.boton(20, C.ALTO - 70, 160, 50, "Volver", lambda: self.game.change_scene("niveles"))

    def _elegir(self, clave):
        self.dificultad = clave
        for c, b in self.botones_dif.items():
            b.seleccionado = (c == clave)

    def _jugar(self):
        self.game.change_scene("juego", id_nivel=self.nivel["id"], dificultad=self.dificultad)

    def draw(self, surface):
        self.dibujar_fondo(surface)

        # Tarjeta izquierda: nombre, descripción y estrellas
        tarjeta = pygame.Rect(40, 40, 510, 460)
        E.panel(surface, tarjeta)
        color = COLORES_NIVEL.get(self.nivel["id"], E.DORADO)
        pygame.draw.rect(surface, color, (tarjeta.x + 2, tarjeta.y + 2, tarjeta.w - 4, 10),
                         border_top_left_radius=14, border_top_right_radius=14)
        nombre = E.titulo(self.nivel["nombre"], 50)
        surface.blit(nombre, (tarjeta.x + 18, tarjeta.y + 20))
        dibujar_texto_multilinea(surface, self.fuente_texto, self.nivel["descripcion"], E.TEXTO,
                                 tarjeta.x + 25, tarjeta.y + 95, tarjeta.w - 50)

        e = self.game.progreso.estrellas(self.nivel["id"])
        conseguidas = [e["desempeno"] >= 1, e["desempeno"] >= 2, e["desempeno"] >= 3,
                       e["dificil"], e["experto"]]
        y = tarjeta.y + 195
        E.texto_sombra(surface, E.fuente(28), "Estrellas", E.DORADO_CLARO, (tarjeta.x + 25, y), "topleft")
        y += 45
        for requisito, ok in zip(REQUISITOS_ESTRELLAS, conseguidas):
            dibujar_estrella(surface, (tarjeta.x + 42, y + 9), 13, llena=ok)
            color_req = E.TEXTO if ok else E.TEXTO_SUAVE
            surface.blit(self.fuente_texto.render(requisito, True, color_req), (tarjeta.x + 66, y))
            y += 40

        # Columna derecha: dificultad
        derecha = pygame.Rect(580, 105, 340, 310)
        E.panel(surface, derecha)
        E.texto_sombra(surface, E.fuente(30), "Dificultad", E.DORADO_CLARO, (derecha.centerx, 140))
        d = C.DIFICULTADES[self.dificultad]
        dibujar_texto_multilinea(surface, pygame.font.Font(None, 23), _descripcion_dificultad(d), E.TEXTO,
                                 derecha.x + 22, 375, derecha.w - 44, interlineado=2)
        for b in self.botones:
            b.draw(surface)

    def on_enter(self):
        self.game.audio.musica("menu")
