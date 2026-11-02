# juego/panel_prueba.py
# Panel del nivel de prueba (solo para desarrollo, no va en la versión final).
import pygame

from engine.ui_elements import Panel, Label  # Usa el motor
from juego.ui_extra import SoundButton
from juego.entities import CLASES_ENEMIGO
from juego import config as C

ESTILO = dict(font_size=22)


class PanelPrueba:
    """Botones para crear enemigos, activar trucos y cambiar niveles de poderes."""

    def __init__(self, escena):
        self.escena = escena
        self.visible = True
        click = escena.game.assets.sounds.get("click")
        self.rect = pygame.Rect(6, 66, 352, 470)
        self.fondo = Panel(self.rect, color=(10, 10, 25, 190), border=(200, 200, 200))
        self.etiquetas = []
        self.botones = []

        # --- Arriba: enemigos en dos columnas ---
        x, y = 14, 74
        self.etiquetas.append(Label("Enemigos", (x, y), size=24, color=(255, 220, 60)))
        y += 22
        self.botones_enemigo = {}
        claves = list(CLASES_ENEMIGO)
        filas = (len(claves) + 1) // 2
        for i, clave in enumerate(claves):
            nombre = C.ENEMIGOS[clave]["nombre"]
            bx = 14 if i < filas else 188
            by = y + (i % filas) * 27
            b = SoundButton(bx, by, 162, 24, nombre, lambda c=clave: escena.prueba_elegir_enemigo(c),
                            click, **ESTILO)
            self.botones_enemigo[clave] = b
            self.botones.append(b)
        y_abajo = y + filas * 27 + 8

        # --- Columna 1: acciones y niveles de poderes ---
        x, y = 14, y_abajo
        self.etiquetas.append(Label("Acciones", (x, y), size=24, color=(255, 220, 60)))
        y += 22
        self.botones.append(SoundButton(x, y, 162, 24, "Borrar enemigos", escena.prueba_borrar_enemigos,
                                        click, **ESTILO))
        y += 27
        self.botones.append(SoundButton(x, y, 162, 24, "Reponer objetos", escena.prueba_reponer_barriles,
                                        click, **ESTILO))
        y += 32
        self.etiquetas.append(Label("Nivel de poderes", (x, y), size=24, color=(255, 220, 60)))
        y += 22
        self.botones_nivel = {}
        for poder in escena.poderes:
            self.etiquetas.append(Label(poder.nombre, (x, y + 4), size=22))
            for n in (1, 2, 3):
                b = SoundButton(x + 72 + (n - 1) * 30, y, 26, 24, str(n),
                                lambda p=poder, n=n: escena.prueba_nivel_poder(p, n), click, **ESTILO)
                self.botones_nivel[(poder.clave, n)] = b
                self.botones.append(b)
            y += 27

        # --- Columna 2: opciones ---
        x, y = 188, y_abajo
        self.etiquetas.append(Label("Opciones", (x, y), size=24, color=(255, 220, 60)))
        y += 22
        self.botones_opcion = {}
        for clave, texto in (("energia_infinita", "Energía infinita"), ("sin_recarga", "Sin recarga"),
                             ("base_invencible", "Base invencible"), ("enemigos_quietos", "Enemigos quietos")):
            b = SoundButton(x, y, 162, 24, texto, lambda c=clave: escena.prueba_alternar(c), click, **ESTILO)
            self.botones_opcion[clave] = b
            self.botones.append(b)
            y += 27
        self.etiquetas.append(Label("Tab: mostrar/ocultar", (x, self.rect.bottom - 22), size=20,
                                    color=(180, 180, 180)))

    def contiene(self, pos):
        return self.visible and self.rect.collidepoint(pos)

    def handle_event(self, evento):
        for b in self.botones:
            b.handle_event(evento)

    def draw(self, surface):
        if not self.visible:
            t = pygame.font.Font(None, 22).render("Tab: panel de prueba", True, (40, 40, 40))
            surface.blit(t, (10, 70))
            return
        e = self.escena
        for clave, b in self.botones_enemigo.items():
            b.seleccionado = (e.enemigo_a_crear == clave)
        for clave, b in self.botones_opcion.items():
            b.seleccionado = e.trucos[clave]
        for (clave, n), b in self.botones_nivel.items():
            b.seleccionado = any(p.clave == clave and p.nivel == n for p in e.poderes)
        self.fondo.draw(surface)
        for et in self.etiquetas:
            et.draw(surface)
        for b in self.botones:
            b.draw(surface)
