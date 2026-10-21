# juego/ui_extra.py
import math
import pygame

from engine.ui import Button  # Hereda del motor


class SoundButton(Button):
    """Botón del motor + sonido al hacer clic (requisito del enunciado)."""

    def __init__(self, x, y, width, height, text, callback, sound=None, **estilo):
        super().__init__(x, y, width, height, text, callback, **estilo)
        self.sound = sound
        self.seleccionado = False   # para resaltar (ej: dificultad elegida)

    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos) and self.sound):
            self.sound.play()
        super().handle_event(event)

    def draw(self, surface):
        super().draw(surface)
        if self.seleccionado:
            pygame.draw.rect(surface, (255, 220, 60), self.rect, 3, border_radius=8)


def dibujar_estrella(surface, centro, radio, llena=True):
    """Estrella de 5 puntas: amarilla si está conseguida, gris si no."""
    cx, cy = centro
    puntos = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = radio if i % 2 == 0 else radio * 0.45
        puntos.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    color = (255, 210, 50) if llena else (110, 110, 110)
    pygame.draw.polygon(surface, color, puntos)
    pygame.draw.polygon(surface, (60, 50, 20), puntos, 2)


def dibujar_texto_multilinea(surface, fuente, texto, color, x, y, ancho_max, interlineado=4):
    """Escribe un texto partiéndolo en varias líneas para que no pase de ancho_max."""
    palabras = texto.split()
    linea = ""
    for palabra in palabras:
        prueba = (linea + " " + palabra).strip()
        if fuente.size(prueba)[0] > ancho_max and linea:
            surface.blit(fuente.render(linea, True, color), (x, y))
            y += fuente.get_height() + interlineado
            linea = palabra
        else:
            linea = prueba
    if linea:
        surface.blit(fuente.render(linea, True, color), (x, y))
        y += fuente.get_height() + interlineado
    return y
