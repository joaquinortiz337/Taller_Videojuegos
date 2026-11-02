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
    # suelo: color del terreno jugable (si no está, se usa C.COLOR_SUELO)
    "montanias": dict(cielo_arriba=(135, 165, 205), cielo_abajo=(215, 225, 235),
                      lejos=(175, 185, 205), medio=(115, 125, 145), cerca=(80, 90, 105),
                      tronco=(70, 55, 45), copa=(55, 85, 80), arbol="pino", suelo=(95, 92, 85)),
    "atardecer": dict(cielo_arriba=(140, 110, 170), cielo_abajo=(250, 175, 115),
                      lejos=(150, 105, 130), medio=(100, 70, 95), cerca=(65, 45, 60),
                      tronco=(45, 30, 35), copa=(60, 40, 55), arbol="pino", suelo=(80, 62, 66)),
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


def _mezclar(a, b, t):
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


def _montanias(color, alto_base, semilla):
    """Cordillera muy lejana con picos (se repite cada ANCHO_CAPA píxeles)."""
    rnd = random.Random(semilla)
    capa = pygame.Surface((ANCHO_CAPA, C.ALTO), pygame.SRCALPHA)
    puntos = [(0, C.ALTO), (0, alto_base)]
    x = 0
    while x < ANCHO_CAPA:
        ancho = rnd.randint(110, 240)
        pico = alto_base - rnd.randint(60, 150)
        puntos.append((x + ancho * rnd.uniform(0.4, 0.6), pico))
        x += ancho
        puntos.append((min(x, ANCHO_CAPA), alto_base - rnd.randint(0, 30)))
    puntos[-1] = (ANCHO_CAPA, alto_base)   # el final coincide con el principio: sin cortes al repetir
    puntos.append((ANCHO_CAPA, C.ALTO))
    pygame.draw.polygon(capa, color, puntos)
    # Nieve / luz en las cumbres
    claro = _mezclar(color, (255, 255, 255), 0.35)
    for i in range(2, len(puntos) - 2, 2):
        px, py = puntos[i]
        pygame.draw.polygon(capa, claro, [(px, py), (px - 14, py + 22), (px + 12, py + 20)])
    return capa


def _frente(paleta, semilla):
    """Capa delantera: matas y piedras oscuras abajo de todo, delante del juego (va más rápido)."""
    rnd = random.Random(semilla)
    capa = pygame.Surface((ANCHO_CAPA, C.ALTO), pygame.SRCALPHA)
    color = _mezclar(paleta["cerca"], (0, 0, 0), 0.55) + (165,)
    x = rnd.randint(40, 200)
    while x < ANCHO_CAPA - 80:
        piso = C.ALTO + 6
        tipo = rnd.choice(("pasto", "mata", "piedra"))
        if tipo == "pasto":
            for _ in range(rnd.randint(6, 10)):
                bx = x + rnd.randint(-22, 22)
                alto = rnd.randint(55, 105)
                pygame.draw.polygon(capa, color, [(bx - 4, piso), (bx + rnd.randint(-10, 10), piso - alto), (bx + 4, piso)])
        elif tipo == "mata":
            for _ in range(5):
                pygame.draw.circle(capa, color, (x + rnd.randint(-34, 34), piso - rnd.randint(25, 55)), rnd.randint(22, 34))
        else:
            ancho = rnd.randint(60, 95)
            pygame.draw.ellipse(capa, color, (x - ancho // 2, piso - 70, ancho, 90))
        x += rnd.randint(330, 650)
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
        self.color_suelo = paleta.get("suelo", C.COLOR_SUELO)
        self.cielo = _cielo(paleta)
        # Velocidades bien separadas: cuanto más lejos, más lento (y más "perdido" en la neblina)
        neblina = paleta["cielo_abajo"]
        self.parallax = ParallaxBackground()
        self.parallax.add_layer(_nubes(semilla), 0.03)
        self.parallax.add_layer(_montanias(_mezclar(paleta["lejos"], neblina, 0.5), 300, semilla + 4), 0.06)
        self.parallax.add_layer(_colinas(paleta["lejos"], 340, 70, (2, 3, 5), semilla + 1), 0.18)
        self.parallax.add_layer(_colinas(paleta["medio"], 420, 50, (3, 4, 7), semilla + 2), 0.42)
        self.parallax.add_layer(_arboles(paleta, semilla + 3), 0.72)
        self.nubes = self.parallax.layers[0]
        # Capa delantera: se mueve MÁS rápido que la cámara (da sensación de profundidad)
        self.frente = ParallaxBackground()
        self.frente.add_layer(_frente(paleta, semilla + 5), 1.35)

    def update(self, dx_camara, dt):
        self.parallax.update(dx_camara)
        self.frente.update(dx_camara)
        self.nubes.update(self.VELOCIDAD_NUBES * dt / self.nubes.speed)   # deriva sola

    def draw(self, surface):
        surface.blit(self.cielo, (0, 0))
        self.parallax.draw(surface)

    def draw_frente(self, surface):
        """Se dibuja después del juego y antes del HUD."""
        self.frente.draw(surface)
