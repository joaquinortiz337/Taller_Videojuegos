# juego/scenes/seleccion_scene.py
import math
import pygame

from juego.scenes.base_menu import MenuBase
from juego.ui_extra import SoundButton, dibujar_estrella, dibujar_texto_multilinea
from juego.niveles import NIVELES
from juego import config as C
from juego import estilo as E

# Color de cada nivel en el mapa (combina con su paisaje)
COLORES_NIVEL = {"nivel1": (95, 175, 80), "nivel2": (45, 115, 75), "nivel3": (115, 135, 175),
                 "nivel4": (150, 85, 160)}


class BotonNivel(SoundButton):
    """Medallón de un nivel en el mapa (hereda del Button del motor a través de SoundButton)."""
    RADIO = 40

    def __init__(self, nivel, numero, accion, sound, desbloqueado, estrellas, proximo):
        x, y = nivel["posicion"]
        r = self.RADIO
        super().__init__(x - r, y - r, r * 2, r * 2, str(numero), accion, sound)
        self.nivel = nivel
        self.habilitado = desbloqueado and nivel["disponible"]
        self.desbloqueado = desbloqueado
        self.estrellas = estrellas
        self.proximo = proximo          # el que te toca jugar: anillo que late
        self.color = COLORES_NIVEL.get(nivel["id"], (90, 90, 140))
        self.fuente_nombre = E.fuente(21)

    def handle_event(self, event):
        if self.habilitado:
            super().handle_event(event)

    @property
    def encima(self):
        return math.dist(pygame.mouse.get_pos(), self.rect.center) <= self.RADIO

    def draw(self, surface):
        t = pygame.time.get_ticks() / 1000
        objetivo = 1.08 if (self.encima and self.habilitado) else 1.0
        self.escala += (objetivo - self.escala) * 0.25
        r = int(self.RADIO * self.escala)
        cx, cy = self.rect.center

        if self.proximo:   # anillo que late alrededor del próximo nivel
            pulso = (math.sin(t * 4) + 1) / 2
            aro = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(aro, (255, 225, 120, int(70 + 90 * pulso)), (r * 2, r * 2), int(r + 8 + 6 * pulso), 4)
            surface.blit(aro, (cx - r * 2, cy - r * 2))

        pygame.draw.circle(surface, (10, 6, 25), (cx + 3, cy + 5), r)          # sombra
        color = self.color if self.habilitado else (85, 85, 95)
        claro = tuple(min(255, c + 50) for c in color)
        pygame.draw.circle(surface, color, (cx, cy), r)
        pygame.draw.circle(surface, claro, (cx - r // 4, cy - r // 4), int(r * 0.55))   # brillo
        pygame.draw.circle(surface, color, (cx, cy), int(r * 0.78))
        pygame.draw.circle(surface, E.DORADO if self.habilitado else (140, 140, 150), (cx, cy), r, 4)

        if self.habilitado:
            numero = E.titulo(self.text, 40, grosor=3)
            surface.blit(numero, numero.get_rect(center=(cx, cy + 1)))
        else:   # candado
            pygame.draw.rect(surface, (225, 225, 230), (cx - 12, cy - 3, 24, 18), border_radius=4)
            pygame.draw.arc(surface, (225, 225, 230), (cx - 9, cy - 16, 18, 24), 0, math.pi, 4)
            pygame.draw.circle(surface, (85, 85, 95), (cx, cy + 5), 3)

        E.texto_sombra(surface, self.fuente_nombre, self.nivel["nombre"], E.TEXTO, (cx, cy + r + 18))
        if self.habilitado:
            pastilla = pygame.Rect(0, 0, 112, 24)
            pastilla.center = (cx, cy + r + 44)
            pygame.draw.rect(surface, (20, 14, 45), pastilla, border_radius=12)
            pygame.draw.rect(surface, E.DORADO, pastilla, 1, border_radius=12)
            for i in range(5):
                dibujar_estrella(surface, (cx - 42 + i * 21, cy + r + 44), 8, llena=i < self.estrellas)


class SeleccionScene(MenuBase):
    """Selección de niveles como un mapa: los medallones se ubican según la 'posicion' de cada nivel."""
    TITULO = "Elegí un nivel"

    def __init__(self, game):
        super().__init__(game)
        prog = self.game.progreso
        click = self.game.assets.sounds.get("click")
        self.botones_nivel = []
        # Próximo nivel: el último desbloqueado que todavía no ganaste
        proximo = None
        for nivel in NIVELES:
            if prog.desbloqueado(nivel["id"]) and nivel["disponible"] and prog.total_estrellas(nivel["id"]) == 0:
                proximo = nivel["id"]
        for i, nivel in enumerate(NIVELES):
            accion = (lambda id_n=nivel["id"]: self.game.change_scene("nivel", id_nivel=id_n))
            b = BotonNivel(nivel, i + 1, accion, click, prog.desbloqueado(nivel["id"]),
                           prog.total_estrellas(nivel["id"]), nivel["id"] == proximo)
            self.botones_nivel.append(b)
            self.botones.append(b)
        self.boton(20, C.ALTO - 70, 160, 50, "Volver", lambda: self.game.change_scene("menu"))
        self.boton_mejoras = self.boton(C.ANCHO // 2 - 90, C.ALTO - 70, 180, 50, "Mejoras",
                                        lambda: self.game.change_scene("mejoras"))
        self.disponibles = prog.estrellas_disponibles()
        self.fuente_aviso = E.fuente(22)
        self.fuente_info = pygame.font.Font(None, 26)
        if C.DEBUG:
            # Nivel de prueba: solo en modo desarrollo
            self.boton(C.ANCHO - 180, C.ALTO - 70, 160, 50, "Prueba",
                       lambda: self.game.change_scene("juego", id_nivel="prueba", dificultad="normal"))

    def draw(self, surface):
        self.dibujar_fondo(surface)
        self._dibujar_camino(surface)
        for b in self.botones:
            b.draw(surface)
        self._dibujar_info(surface)
        self._dibujar_aviso_mejoras(surface)

    def _dibujar_camino(self, surface):
        """Camino de puntitos entre niveles: dorado hasta donde llegaste, gris lo bloqueado."""
        for a, b in zip(self.botones_nivel, self.botones_nivel[1:]):
            (xa, ya), (xb, yb) = a.rect.center, b.rect.center
            largo = math.dist((xa, ya), (xb, yb))
            color = E.DORADO if b.habilitado else (120, 115, 130)
            pasos = int(largo / 16)
            for i in range(1, pasos):
                t = i / pasos
                x = xa + (xb - xa) * t
                y = ya + (yb - ya) * t - math.sin(t * math.pi) * 18   # arco suave
                if math.dist((x, y), (xa, ya)) > a.RADIO + 6 and math.dist((x, y), (xb, yb)) > b.RADIO + 6:
                    pygame.draw.circle(surface, (10, 6, 25), (int(x) + 1, int(y) + 2), 4)
                    pygame.draw.circle(surface, color, (int(x), int(y)), 4)

    def _dibujar_info(self, surface):
        """Al pasar el mouse por un nivel: su nombre y descripción en una tarjeta."""
        b = next((b for b in self.botones_nivel if b.encima), None)
        if b is None:
            return
        tarjeta = pygame.Rect(C.ANCHO // 2 - 260, 400, 520, 105)
        E.panel(surface, tarjeta)
        if b.habilitado:
            nombre, texto = b.nivel["nombre"], b.nivel["descripcion"]
        else:
            nombre, texto = b.nivel["nombre"], "Ganá el nivel anterior para desbloquearlo."
        E.texto_sombra(surface, E.fuente(26), nombre, E.DORADO_CLARO, (tarjeta.centerx, tarjeta.y + 20))
        dibujar_texto_multilinea(surface, self.fuente_info, texto, E.TEXTO,
                                 tarjeta.x + 22, tarjeta.y + 42, tarjeta.w - 44)

    def _dibujar_aviso_mejoras(self, surface):
        """Circulito que late con las estrellas sin gastar."""
        if self.disponibles <= 0:
            return
        x, y = self.boton_mejoras.rect.topright
        r = 15 + 2 * math.sin(pygame.time.get_ticks() / 180)
        pygame.draw.circle(surface, (230, 60, 50), (x - 4, y + 2), r)
        pygame.draw.circle(surface, (255, 255, 255), (x - 4, y + 2), r, 2)
        t = self.fuente_aviso.render(str(self.disponibles), True, (255, 255, 255))
        surface.blit(t, t.get_rect(center=(x - 4, y + 2)))

    def on_enter(self):
        self.game.audio.musica("menu")
