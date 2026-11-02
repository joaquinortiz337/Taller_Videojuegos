# juego/estilo.py
# Estilo visual de los menús: colores, fuente de títulos, títulos dorados, paneles y el fondo
# animado que comparten todas las pantallas de menú.
import math
import os
import random

import pygame

from juego import config as C

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_FUENTE = os.path.join(RAIZ, "assets", "fonts", "LilitaOne-Regular.ttf")

# Colores
TEXTO = (255, 244, 220)          # crema
TEXTO_SUAVE = (210, 200, 225)
DORADO = (240, 195, 80)
DORADO_CLARO = (255, 225, 120)
PANEL = (28, 22, 60, 215)
BOTON_ARRIBA = (66, 55, 125)
BOTON_ABAJO = (34, 28, 74)

_fuentes = {}


def fuente(tam):
    """Fuente de títulos y botones (Lilita One). Si falta el archivo, la de pygame."""
    if tam not in _fuentes:
        ruta = RUTA_FUENTE if os.path.exists(RUTA_FUENTE) else None
        _fuentes[tam] = pygame.font.Font(ruta, tam if ruta else int(tam * 1.3))
    return _fuentes[tam]


_titulos = {}


DEGRADE_DORADO = ((255, 228, 115), (245, 133, 30))
DEGRADE_ROJO = ((255, 130, 105), (185, 25, 25))
DEGRADE_VERDE = ((190, 255, 140), (60, 170, 60))


def titulo(texto, tam, grosor=4, degrade=DEGRADE_DORADO):
    """Texto con degradé (dorado por defecto), borde oscuro y sombra (se guarda para no rehacerlo)."""
    clave = (texto, tam, grosor, degrade)
    if clave in _titulos:
        return _titulos[clave]
    f = fuente(tam)
    base = f.render(texto, True, (255, 255, 255))
    borde = f.render(texto, True, (40, 20, 30))
    sombra = f.render(texto, True, (0, 0, 0))
    sombra.set_alpha(110)
    w, h = base.get_width() + grosor * 2 + 6, base.get_height() + grosor * 2 + 6
    img = pygame.Surface((w, h), pygame.SRCALPHA)
    img.blit(sombra, (grosor + 5, grosor + 5))
    for dx in range(-grosor, grosor + 1):
        for dy in range(-grosor, grosor + 1):
            if dx * dx + dy * dy <= grosor * grosor:
                img.blit(borde, (grosor + dx, grosor + dy))
    capa_degrade = pygame.Surface(base.get_size(), pygame.SRCALPHA)
    for y in range(base.get_height()):
        t = y / base.get_height()
        arriba, abajo = degrade
        pygame.draw.line(capa_degrade, [int(arriba[i] + (abajo[i] - arriba[i]) * t) for i in range(3)],
                         (0, y), (base.get_width(), y))
    capa_degrade.blit(base, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    img.blit(capa_degrade, (grosor, grosor))
    _titulos[clave] = img
    return img


def texto_sombra(surface, fuente_, texto, color, pos, ancla="center"):
    """Texto con una sombrita debajo (se lee sobre cualquier fondo)."""
    sombra = fuente_.render(texto, True, (10, 6, 25))
    t = fuente_.render(texto, True, color)
    r = t.get_rect(**{ancla: pos})
    surface.blit(sombra, r.move(2, 2))
    surface.blit(t, r)
    return r


def panel(surface, rect, borde=True):
    """Tarjeta semitransparente con bordes redondeados y borde dorado."""
    rect = pygame.Rect(rect)
    capa = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(capa, PANEL, (0, 0, *rect.size), border_radius=16)
    surface.blit(capa, rect)
    if borde:
        pygame.draw.rect(surface, DORADO, rect, 2, border_radius=16)


def degrade_redondeado(tam, arriba, abajo, radio):
    """Rectángulo redondeado con degradé vertical."""
    w, h = tam
    img = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        t = y / max(1, h - 1)
        pygame.draw.line(img, [int(arriba[i] + (abajo[i] - arriba[i]) * t) for i in range(3)], (0, y), (w, y))
    mascara = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mascara, (255, 255, 255, 255), (0, 0, w, h), border_radius=radio)
    img.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return img


class FondoMenu:
    """Paisaje de atardecer que se desliza solo, con la silueta de la torre y algún volador
    que cruza. Es el mismo objeto para todas las pantallas de menú (no se reinicia)."""
    VELOCIDAD = 18   # px/s de la "cámara"

    def __init__(self):
        from juego.fondo import Fondo   # acá para evitar importaciones circulares
        self.fondo = Fondo("atardecer", semilla=1234)
        self.velo = pygame.Surface((C.ANCHO, C.ALTO), pygame.SRCALPHA)
        for y in range(C.ALTO):   # más oscuro arriba y abajo: el centro queda más vivo
            t = abs(y / C.ALTO - 0.45) * 2
            pygame.draw.line(self.velo, (15, 10, 40, int(95 + 90 * t)), (0, y), (C.ANCHO, y))
        self.voladores = []
        self.espera = 3.0
        self.tiempo = 0.0
        self.suelo = self._crear_suelo()

    def _crear_suelo(self):
        """Lomas del primer plano con la silueta de la torre a la izquierda."""
        capa = pygame.Surface((C.ANCHO, C.ALTO), pygame.SRCALPHA)
        color = (45, 30, 45)
        puntos = [(0, C.ALTO)]
        for x in range(0, C.ANCHO + 1, 10):
            puntos.append((x, 520 - 22 * math.sin(x / 160) - 12 * math.sin(x / 70 + 1)))
        puntos.append((C.ANCHO, C.ALTO))
        pygame.draw.polygon(capa, color, puntos)
        x0, base = 40, 510
        pygame.draw.rect(capa, color, (x0, base - 120, 60, 125))
        for i in range(4):
            pygame.draw.rect(capa, color, (x0 + i * 17, base - 133, 10, 14))
        pygame.draw.rect(capa, color, (x0 + 60, base - 70, 14, 12))
        pygame.draw.rect(capa, color, (x0 + 68, base - 112, 22, 50))
        pygame.draw.line(capa, color, (x0 + 30, base - 133), (x0 + 30, base - 175), 3)
        pygame.draw.polygon(capa, color, [(x0 + 31, base - 175), (x0 + 56, base - 168), (x0 + 31, base - 160)])
        for vx, vy in ((x0 + 14, base - 95), (x0 + 38, base - 95), (x0 + 26, base - 60)):
            pygame.draw.rect(capa, (255, 200, 110), (vx, vy, 7, 10))
        return capa

    def update(self, dt):
        self.tiempo += dt
        self.fondo.update(self.VELOCIDAD * dt, dt)
        self.espera -= dt
        if self.espera <= 0:
            self.espera = random.uniform(4, 9)
            self.voladores.append([C.ANCHO + 30, random.uniform(150, 330), random.uniform(60, 110),
                                   random.uniform(0, 6)])
        for v in self.voladores:
            v[0] -= v[2] * dt
        self.voladores = [v for v in self.voladores if v[0] > -40]

    def draw(self, surface):
        self.fondo.draw(surface)
        for x, y, _, fase in self.voladores:
            y += math.sin(self.tiempo * 2 + fase) * 8
            ala = math.sin(self.tiempo * 14 + fase) * 6
            color = (40, 28, 50)
            pygame.draw.polygon(surface, color, [(x - 3, y - 2), (x - 16, y - 6 - ala), (x - 8, y + 2)])
            pygame.draw.polygon(surface, color, [(x + 3, y - 2), (x + 16, y - 6 - ala), (x + 8, y + 2)])
            pygame.draw.circle(surface, color, (int(x), int(y)), 7)
        surface.blit(self.suelo, (0, 0))
        surface.blit(self.velo, (0, 0))
