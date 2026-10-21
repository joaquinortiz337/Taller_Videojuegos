# juego/scenes/end_scenes.py
import pygame

from juego.scenes.base_menu import MenuBase
from juego.ui_extra import dibujar_estrella
from juego.niveles import NIVELES_POR_ID
from juego import config as C


class EndScene(MenuBase):
    """Base común para Game Over y Victoria."""
    COLOR = (0, 0, 0)

    def __init__(self, game, id_nivel, dificultad, puntos=0):
        super().__init__(game)
        self.id_nivel = id_nivel
        self.dificultad = dificultad
        self.puntos = puntos
        self.fuente_titulo = pygame.font.Font(None, 100)
        cx = C.ANCHO // 2
        self.boton(cx - 410, 460, 260, 60, "Reintentar",
                   lambda: self.game.change_scene("juego", id_nivel=id_nivel, dificultad=dificultad))
        self.boton(cx - 130, 460, 260, 60, "Volver a niveles",
                   lambda: self.game.change_scene("niveles"))
        self.boton(cx + 150, 460, 260, 60, "Menú principal",
                   lambda: self.game.change_scene("menu"))

    def draw(self, surface):
        surface.fill(C.COLOR_CIELO)
        t = self.fuente_titulo.render(self.TITULO, True, self.COLOR)
        surface.blit(t, t.get_rect(center=(C.ANCHO // 2, 110)))
        info = (f"{NIVELES_POR_ID[self.id_nivel]['nombre']} · "
                f"{C.DIFICULTADES[self.dificultad]['nombre']} · Puntos: {self.puntos}")
        i = self.fuente.render(info, True, C.COLOR_TEXTO)
        surface.blit(i, i.get_rect(center=(C.ANCHO // 2, 180)))
        for b in self.botones:
            b.draw(surface)


class GameOverScene(EndScene):
    TITULO = "GAME OVER"
    COLOR = (150, 0, 0)

    def on_enter(self):
        self.game.audio.musica("menu")
        self.game.audio.reproducir("derrota")


class VictoryScene(EndScene):
    TITULO = "¡VICTORIA!"
    COLOR = (20, 120, 40)

    def __init__(self, game, id_nivel, dificultad, puntos=0, desempeno=1, nuevo_nivel=None):
        super().__init__(game, id_nivel, dificultad, puntos)
        self.desempeno = desempeno
        self.nuevo_nivel = nuevo_nivel

    def on_enter(self):
        self.game.audio.musica("menu")
        self.game.audio.reproducir("victoria")

    def draw(self, surface):
        super().draw(surface)
        # Estrellas de esta partida: 3 de desempeño + Difícil + Experto
        conseguidas = [self.desempeno >= 1, self.desempeno >= 2, self.desempeno >= 3,
                       self.dificultad in ("dificil", "experto"), self.dificultad == "experto"]
        for i, ok in enumerate(conseguidas):
            dibujar_estrella(surface, (C.ANCHO // 2 - 160 + i * 80, 290), 32, llena=ok)
        if self.nuevo_nivel and NIVELES_POR_ID[self.nuevo_nivel]["disponible"]:
            t = self.fuente.render("¡Nuevo nivel desbloqueado!", True, (20, 100, 160))
            surface.blit(t, t.get_rect(center=(C.ANCHO // 2, 380)))
