# juego/terreno.py
# Terreno con relieve (colinas). Cada nivel lo define como una lista de puntos
# de control (x, desnivel); entre punto y punto se suaviza con una curva.
# desnivel: píxeles respecto al suelo base (C.SUELO_Y). Negativo = más alto.
import math
import pygame
import pymunk

from juego import config as C

PASO = 25   # cada cuántos píxeles se arma un tramo recto del suelo físico


class Terreno:
    def __init__(self, puntos, ancho_mundo, suelos=None):
        self.suelos = list(suelos or [])   # [(desde_x, hasta_x, tipo), ...]; el resto es "normal"
        if not puntos:
            puntos = [(0, 0), (ancho_mundo, 0)]
        self.control = sorted(puntos)
        if self.control[-1][0] < ancho_mundo + 200:
            self.control.append((ancho_mundo + 200, self.control[-1][1]))
        if self.control[0][0] > -100:
            self.control.insert(0, (-100, self.control[0][1]))
        # Línea del suelo muestreada cada PASO px (centro de los segmentos físicos)
        x0, x1 = self.control[0][0], self.control[-1][0]
        self.linea = [(x, self._centro(x)) for x in range(int(x0), int(x1) + 1, PASO)]

    def _centro(self, x):
        """Altura de la línea central del suelo (interpolación coseno entre puntos de control)."""
        pts = self.control
        if x <= pts[0][0]:
            return C.SUELO_Y + pts[0][1]
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            if xa <= x <= xb:
                t = (x - xa) / (xb - xa) if xb > xa else 0
                t = (1 - math.cos(math.pi * t)) / 2
                return C.SUELO_Y + ya + (yb - ya) * t
        return C.SUELO_Y + pts[-1][1]

    def superficie(self, x):
        """y de la superficie del suelo en x (donde se apoyan las cosas)."""
        return self._centro(x) - C.GROSOR_SUELO

    def pendiente(self, x):
        """dy/dx del suelo en x (positivo = sube hacia la izquierda, hacia la base)."""
        d = 4
        return (self._centro(x + d) - self._centro(x - d)) / (2 * d)

    def tipo(self, x):
        """Tipo de suelo en x ("normal", "barro", "hielo")."""
        for desde, hasta, tipo in self.suelos:
            if desde <= x <= hasta:
                return tipo
        return "normal"

    def crear_fisica(self, space):
        """Segmentos estáticos encadenados (vecinos marcados para que nada se trabe en las uniones)."""
        # Segmentos gruesos corridos hacia abajo: la superficie queda en el mismo lugar que con
        # el grosor de siempre, pero así algo que cae muy rápido no puede atravesar el suelo
        bajar = C.RADIO_FISICO_SUELO - C.GROSOR_SUELO
        segs = []
        for (xa, ya), (xb, yb) in zip(self.linea, self.linea[1:]):
            s = pymunk.Segment(space.static_body, (xa, ya + bajar), (xb, yb + bajar), C.RADIO_FISICO_SUELO)
            tipo = self.tipo((xa + xb) / 2)
            s.tipo_suelo = tipo            # lo leen los enemigos y los efectos de choque
            s.friction = C.SUELOS[tipo]["friccion"]
            s.elasticity = C.SUELOS[tipo]["rebote"]
            segs.append(s)
        for i, s in enumerate(segs):
            anterior = segs[i - 1].b if i > 0 else s.a
            siguiente = segs[i + 1].b if i + 1 < len(segs) else s.b
            s.set_neighbors(anterior, siguiente)
        space.add(*segs)
        return segs

    def dibujar(self, surface, color):
        borde = tuple(max(0, c - 25) for c in color)
        puntos = [(x, y - C.GROSOR_SUELO) for x, y in self.linea]
        pygame.draw.polygon(surface, color, puntos + [(puntos[-1][0], C.ALTO), (puntos[0][0], C.ALTO)])
        pygame.draw.lines(surface, borde, False, puntos, 4)
        for desde, hasta, tipo in self.suelos:
            self._dibujar_tramo(surface, desde, hasta, tipo)

    def _dibujar_tramo(self, surface, desde, hasta, tipo):
        color = C.SUELOS[tipo]["color"]
        if color is None:
            return
        borde = tuple(max(0, c - 35) for c in color)
        arriba = [(x, self._centro(x) - C.GROSOR_SUELO) for x in range(int(desde), int(hasta) + 1, 10)]
        # Capa de unos 40 px que sigue la forma del suelo y se afina en los extremos
        abajo = []
        for x, y in reversed(arriba):
            afinado = min(1.0, (x - desde) / 30, (hasta - x) / 30)
            abajo.append((x, y + 4 + 36 * max(0.0, afinado)))
        pygame.draw.polygon(surface, color, arriba + abajo)
        pygame.draw.lines(surface, borde, False, arriba, 4)
        if tipo == "barro":
            # Charquitos brillantes
            for x in range(int(desde) + 30, int(hasta) - 20, 55):
                y = self._centro(x) - C.GROSOR_SUELO + 9
                pygame.draw.ellipse(surface, (70, 50, 32), (x - 14, y - 3, 28, 8))
                pygame.draw.ellipse(surface, (140, 110, 80), (x - 8, y - 2, 9, 3))
        elif tipo == "hielo":
            # Reflejos blancos en diagonal
            for x in range(int(desde) + 20, int(hasta) - 20, 40):
                y = self._centro(x) - C.GROSOR_SUELO + 6
                pygame.draw.line(surface, (245, 252, 255), (x, y + 12), (x + 10, y), 3)
                pygame.draw.line(surface, (225, 240, 250), (x + 9, y + 14), (x + 15, y + 6), 2)


# Terreno del nivel en curso (lo fija la escena de juego). Sin nivel: suelo plano.
ACTUAL = None


def superficie(x):
    return ACTUAL.superficie(x) if ACTUAL else C.SUELO_Y - C.GROSOR_SUELO


def pendiente(x):
    return ACTUAL.pendiente(x) if ACTUAL else 0.0
