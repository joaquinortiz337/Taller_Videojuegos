# juego/fondo.py
# Fondo con profundidad (parallax) dibujado por código, usando el ParallaxBackground del motor.
# Cuando haya fondos dibujados, alcanza con reemplazar las imágenes de cada capa.
import math
import random
import pygame

from engine.background import ParallaxBackground  # Usa el motor
from juego import config as C

ANCHO_CAPA = 1600   # ancho de cada capa (se repite en bucle)

PALETAS = {
    "pradera": dict(cielo_arriba=(120, 180, 235), cielo_abajo=(205, 230, 240),
                    lejos=(150, 175, 195), medio=(110, 165, 110), cerca=(70, 130, 70),
                    tronco=(95, 70, 45), copa=(60, 120, 60), arbol="redondo"),
    "bosque": dict(cielo_arriba=(80, 110, 140), cielo_abajo=(165, 185, 180),
                   lejos=(95, 120, 120), medio=(55, 95, 70), cerca=(35, 70, 45),
                   tronco=(70, 50, 35), copa=(30, 75, 45), arbol="pino"),
}


def _colinas(color, alto_base, amplitud, armonicos, semilla):
    """Silueta de colinas que se repite perfectamente cada ANCHO_CAPA píxeles."""
    rnd = random.Random(semilla)
    capa = pygame.Surface((ANCHO_CAPA, C.ALTO), pygame.SRCALPHA)
    fases = [(k, rnd.uniform(0, 2 * math.pi), rnd.uniform(0.3, 1.0)) for k in armonicos]
    puntos = [(0, C.ALTO)]
    for x in range(0, ANCHO_CAPA + 1, 8):
        y = sum(peso * math.sin(2 * math.pi * k * x / ANCHO_CAPA + fase) for k, fase, peso in fases)
        puntos.append((x, alto_base - amplitud * y / len(fases)))
    puntos.append((ANCHO_CAPA, C.ALTO))
    pygame.draw.polygon(capa, color, puntos)
    return capa


def _arboles(paleta, semilla):
    rnd = random.Random(semilla)
    capa = pygame.Surface((ANCHO_CAPA, C.ALTO), pygame.SRCALPHA)
    piso = C.SUELO_Y - 10
    x = 20
    while x < ANCHO_CAPA - 40:
        alto = rnd.randint(60, 120)
        if paleta["arbol"] == "pino":
            pygame.draw.rect(capa, paleta["tronco"], (x - 4, piso - 20, 8, 20))
            for i in range(3):
                ancho = 34 - i * 8
                base_y = piso - 15 - i * alto // 4
                pygame.draw.polygon(capa, paleta["copa"],
                                    [(x - ancho, base_y), (x + ancho, base_y), (x, base_y - alto // 2)])
        else:
            pygame.draw.rect(capa, paleta["tronco"], (x - 5, piso - alto // 2, 10, alto // 2))
            pygame.draw.circle(capa, paleta["copa"], (x, piso - alto // 2 - 15), alto // 3)
            pygame.draw.circle(capa, paleta["copa"], (x - 14, piso - alto // 2 - 2), alto // 4)
            pygame.draw.circle(capa, paleta["copa"], (x + 14, piso - alto // 2 - 2), alto // 4)
        x += rnd.randint(90, 220)
    return capa


def _nubes(semilla):
    rnd = random.Random(semilla)
    capa = pygame.Surface((ANCHO_CAPA, 220), pygame.SRCALPHA)
    for _ in range(7):
        cx, cy = rnd.randint(60, ANCHO_CAPA - 60), rnd.randint(40, 180)
        for _ in range(5):
            r = rnd.randint(18, 34)
            pygame.draw.circle(capa, (255, 255, 255, 200), (cx + rnd.randint(-40, 40), cy + rnd.randint(-8, 8)), r)
    return capa


def _cielo(paleta):
    cielo = pygame.Surface((C.ANCHO, C.ALTO))
    a, b = paleta["cielo_arriba"], paleta["cielo_abajo"]
    for y in range(C.ALTO):
        p = y / C.ALTO
        pygame.draw.line(cielo, [int(a[i] + (b[i] - a[i]) * p) for i in range(3)], (0, y), (C.ANCHO, y))
    return cielo


class Fondo:
    """Cielo con degradé + capas que se mueven a distinta velocidad según la cámara."""
    VELOCIDAD_NUBES = 8   # px/s que se desplazan solas

    def __init__(self, tipo="pradera", semilla=1):
        paleta = PALETAS.get(tipo, PALETAS["pradera"])
        self.cielo = _cielo(paleta)
        self.parallax = ParallaxBackground()
        self.parallax.add_layer(_nubes(semilla), 0.05)
        self.parallax.add_layer(_colinas(paleta["lejos"], 330, 70, (2, 3, 5), semilla + 1), 0.15)
        self.parallax.add_layer(_colinas(paleta["medio"], 420, 50, (3, 4, 7), semilla + 2), 0.4)
        self.parallax.add_layer(_arboles(paleta, semilla + 3), 0.7)
        self.nubes = self.parallax.layers[0]

    def update(self, dx_camara, dt):
        self.parallax.update(dx_camara)
        self.nubes.update(self.VELOCIDAD_NUBES * dt / self.nubes.speed)   # deriva sola

    def draw(self, surface):
        surface.blit(self.cielo, (0, 0))
        self.parallax.draw(surface)
