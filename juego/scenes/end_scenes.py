# juego/scenes/end_scenes.py
import math

import pygame

from juego.scenes.base_menu import MenuBase
from juego.ui_extra import dibujar_estrella
from juego.niveles import NIVELES, NIVELES_POR_ID
from juego import config as C
from juego import estilo as E


class EndScene(MenuBase):
    """Base común para Game Over y Victoria."""
    DEGRADE = E.DEGRADE_DORADO
    TINTE = None    # color que tiñe el fondo (ej: rojo en la derrota)

    def __init__(self, game, id_nivel, dificultad, puntos=0):
        super().__init__(game)
        self.id_nivel = id_nivel
        self.dificultad = dificultad
        self.puntos = puntos
        self.tiempo = 0.0
        cx = C.ANCHO // 2
        self.boton(cx - 410, 455, 260, 56, "Reintentar",
                   lambda: self.game.change_scene("juego", id_nivel=id_nivel, dificultad=dificultad))
        self.boton(cx - 130, 455, 260, 56, "Volver a niveles",
                   lambda: self.game.change_scene("niveles"))
        self.boton(cx + 150, 455, 260, 56, "Menú principal",
                   lambda: self.game.change_scene("menu"))

    def update(self):
        self.tiempo += 1 / C.FPS

    def draw(self, surface):
        self.game.fondo_menu.draw(surface)   # sin el título fijo: acá el título se anima aparte
        if self.TINTE:
            tinte = pygame.Surface((C.ANCHO, C.ALTO), pygame.SRCALPHA)
            tinte.fill(self.TINTE)
            surface.blit(tinte, (0, 0))
        E.panel(surface, (C.ANCHO // 2 - 330, 40, 660, 390))
        # El título entra creciendo y después "respira"
        crecer = min(1.0, self.tiempo / 0.35)
        escala = (0.6 + 0.4 * crecer) * (1 + 0.02 * math.sin(self.tiempo * 3))
        t = E.titulo(self.TITULO, 84, grosor=5, degrade=self.DEGRADE)
        t = pygame.transform.smoothscale(t, (int(t.get_width() * escala), int(t.get_height() * escala)))
        surface.blit(t, t.get_rect(center=(C.ANCHO // 2, 115)))
        info = (f"{NIVELES_POR_ID[self.id_nivel]['nombre']} · "
                f"{C.DIFICULTADES[self.dificultad]['nombre']} · Puntos: {self.puntos}")
        E.texto_sombra(surface, self.fuente, info, E.TEXTO, (C.ANCHO // 2, 190))
        self.dibujar_extra(surface)
        for b in self.botones:
            b.draw(surface)

    def dibujar_extra(self, surface):
        pass


class GameOverScene(EndScene):
    TITULO = "GAME OVER"
    DEGRADE = E.DEGRADE_ROJO
    TINTE = (90, 0, 0, 90)

    def on_enter(self):
        self.game.audio.musica("menu")
        self.game.audio.reproducir("derrota")
        self.game.audio.voz("game_over")

    def dibujar_extra(self, surface):
        t = pygame.font.Font(None, 30).render("La base cayó... ¡Probá otra vez!", True, E.TEXTO_SUAVE)
        surface.blit(t, t.get_rect(center=(C.ANCHO // 2, 290)))


class VictoryScene(EndScene):
    TITULO = "¡VICTORIA!"
    DEGRADE = E.DEGRADE_VERDE
    PRIMERA_ESTRELLA = 0.5    # segundos hasta que aparece la primera estrella
    ENTRE_ESTRELLAS = 0.35

    def __init__(self, game, id_nivel, dificultad, puntos=0, desempeno=1, nuevo_nivel=None):
        super().__init__(game, id_nivel, dificultad, puntos)
        self.desempeno = desempeno
        self.nuevo_nivel = nuevo_nivel
        # Estrellas de esta partida: 3 de desempeño + Difícil + Experto
        self.conseguidas = [desempeno >= 1, desempeno >= 2, desempeno >= 3,
                            dificultad in ("dificil", "experto"), dificultad == "experto"]
        self.sonadas = 0
        if id_nivel == NIVELES[-1]["id"]:   # ganaste el último nivel: botón a los créditos
            self.boton(C.ANCHO // 2 - 130, 525, 260, 54, "Créditos",
                       lambda: self.game.change_scene("creditos"))

    def on_enter(self):
        self.game.audio.musica("menu")
        self.game.audio.reproducir("victoria")

    def update(self):
        super().update()
        # Sonidito por cada estrella conseguida al aparecer
        indices = [i for i, ok in enumerate(self.conseguidas) if ok]
        while self.sonadas < len(indices) and self.tiempo >= self._aparece(indices[self.sonadas]):
            self.sonadas += 1
            self.game.audio.reproducir(f"combo_{min(6, self.sonadas + 1)}", 0.7)

    def _aparece(self, i):
        return self.PRIMERA_ESTRELLA + i * self.ENTRE_ESTRELLAS

    def dibujar_extra(self, surface):
        for i, ok in enumerate(self.conseguidas):
            centro = (C.ANCHO // 2 - 160 + i * 80, 285)
            if not ok:
                dibujar_estrella(surface, centro, 30, llena=False)
                continue
            t = self.tiempo - self._aparece(i)
            if t < 0:
                dibujar_estrella(surface, centro, 30, llena=False)
                continue
            # Aparece grande y rebota hasta su tamaño
            rebote = 1 + 0.6 * math.exp(-t * 7) * math.cos(t * 18)
            if t < 0.3:   # destello
                brillo = pygame.Surface((120, 120), pygame.SRCALPHA)
                pygame.draw.circle(brillo, (255, 230, 120, int(150 * (1 - t / 0.3))), (60, 60), int(30 + 80 * t))
                surface.blit(brillo, (centro[0] - 60, centro[1] - 60))
            dibujar_estrella(surface, centro, max(4, int(32 * rebote)), llena=True)
        if self.nuevo_nivel and NIVELES_POR_ID[self.nuevo_nivel]["disponible"]:
            fin_estrellas = self._aparece(4) + 0.3
            if self.tiempo > fin_estrellas:
                alfa = min(1.0, (self.tiempo - fin_estrellas) / 0.4)
                t = E.fuente(30).render("¡Nuevo nivel desbloqueado!", True, E.DORADO_CLARO)
                t.set_alpha(int(255 * alfa))
                surface.blit(t, t.get_rect(center=(C.ANCHO // 2, 375)))
