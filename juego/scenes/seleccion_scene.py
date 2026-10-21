# juego/scenes/seleccion_scene.py
import pygame

from juego.scenes.base_menu import MenuBase
from juego.ui_extra import SoundButton, dibujar_estrella
from juego.niveles import NIVELES
from juego import config as C


class BotonNivel(SoundButton):
    """Botón redondo de un nivel (hereda del Button del motor a través de SoundButton)."""
    RADIO = 38

    def __init__(self, nivel, numero, accion, sound, desbloqueado, estrellas):
        x, y = nivel["posicion"]
        r = self.RADIO
        super().__init__(x - r, y - r, r * 2, r * 2, str(numero), accion, sound)
        self.nivel = nivel
        self.habilitado = desbloqueado and nivel["disponible"]
        self.desbloqueado = desbloqueado
        self.estrellas = estrellas
        self.fuente_nombre = pygame.font.Font(None, 26)

    def handle_event(self, event):
        if self.habilitado:
            super().handle_event(event)

    def draw(self, surface):
        centro = self.rect.center
        r = self.RADIO
        encima = self.rect.collidepoint(pygame.mouse.get_pos()) and self.habilitado
        if self.habilitado:
            color = (80, 80, 120) if encima else (50, 50, 80)
        else:
            color = (110, 110, 110)
        pygame.draw.circle(surface, color, centro, r)
        pygame.draw.circle(surface, (20, 20, 20), centro, r, 3)

        if self.habilitado:
            t = self.font.render(self.text, True, (255, 255, 255))
            surface.blit(t, t.get_rect(center=centro))
        elif not self.nivel["disponible"]:
            t = self.font.render("?", True, (230, 230, 230))
            surface.blit(t, t.get_rect(center=centro))
        else:
            # Candado
            cx, cy = centro
            pygame.draw.rect(surface, (230, 230, 230), (cx - 11, cy - 2, 22, 16), border_radius=3)
            pygame.draw.arc(surface, (230, 230, 230), (cx - 8, cy - 14, 16, 22), 0, 3.14, 3)

        nombre = self.fuente_nombre.render(self.nivel["nombre"], True, C.COLOR_TEXTO)
        surface.blit(nombre, nombre.get_rect(center=(centro[0], centro[1] + r + 16)))
        if self.desbloqueado and self.nivel["disponible"]:
            for i in range(5):
                dibujar_estrella(surface, (centro[0] - 40 + i * 20, centro[1] + r + 38), 8,
                                 llena=i < self.estrellas)


class SeleccionScene(MenuBase):
    """Selección de niveles: los botones se ubican según la 'posicion' de cada nivel."""
    TITULO = "Elegí un nivel"

    def __init__(self, game):
        super().__init__(game)
        prog = self.game.progreso
        click = self.game.assets.sounds.get("click")
        self.botones_nivel = []
        for i, nivel in enumerate(NIVELES):
            accion = (lambda id_n=nivel["id"]: self.game.change_scene("nivel", id_nivel=id_n))
            b = BotonNivel(nivel, i + 1, accion, click, prog.desbloqueado(nivel["id"]),
                           prog.total_estrellas(nivel["id"]))
            self.botones_nivel.append(b)
            self.botones.append(b)
        self.boton(20, C.ALTO - 70, 160, 50, "Volver", lambda: self.game.change_scene("menu"))
        if C.DEBUG:
            # Nivel de prueba: solo en modo desarrollo
            self.boton(C.ANCHO - 180, C.ALTO - 70, 160, 50, "Prueba",
                       lambda: self.game.change_scene("juego", id_nivel="prueba", dificultad="normal"))

    def draw(self, surface):
        self.dibujar_fondo(surface)
        # Camino entre niveles (después se reemplaza por el mapa dibujado)
        puntos = [n["posicion"] for n in NIVELES]
        if len(puntos) > 1:
            pygame.draw.lines(surface, (120, 100, 70), False, puntos, 6)
        for b in self.botones:
            b.draw(surface)

    def on_enter(self):
        self.game.audio.musica("menu")
