# juego/base.py
# La base que defendés: un fortín dibujado por código, su plaza empedrada, la empalizada que marca
# la zona de peligro y las personitas que viven ahí. Todo es decorado: no participa de la física.
import math
import random

import pygame

from juego import config as C

ANCHO_TORRE = 66          # la torre va de x=4 a x=70 (el borde que cuenta para el juego es C.BASE_X)
ALTO_TORRE = 150
FIN_PLAZA = 230           # la plaza empedrada va de x=0 a acá
CANT_PERSONAS = 6


def _mezclar(a, b, t):
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


class Persona:
    """Figurita simple: pasea tranquila, corre a la torre si hay peligro y sale cuando se calma."""
    COLORES = [(200, 60, 60), (60, 110, 200), (230, 180, 50), (70, 160, 90), (170, 90, 170), (220, 130, 60)]

    def __init__(self, indice):
        self.x = random.uniform(90, FIN_PLAZA - 15)
        self.destino = self.x
        self.estado = "paseo"            # paseo, huyendo, adentro, saliendo
        self.espera = random.uniform(0.5, 3.0)
        self.paso = random.uniform(0, 6)  # fase de la animación de las piernas
        self.mira = 1
        self.color = self.COLORES[indice % len(self.COLORES)]
        self.carga = random.random() < 0.4   # lleva una caja
        self.salida = 0.0

    def update(self, dt, peligro, puerta_x):
        if self.estado in ("paseo", "saliendo") and peligro > C.BASE_PANICO:
            self.estado = "huyendo"
        if self.estado == "adentro":
            self.salida -= dt
            if peligro < C.BASE_CALMA and self.salida <= 0:
                self.estado = "saliendo"
                self.x = puerta_x
                self.destino = random.uniform(90, FIN_PLAZA - 15)
            return
        if self.estado == "huyendo":
            velocidad, self.destino = C.BASE_VEL_CORRER, puerta_x
        else:
            velocidad = C.BASE_VEL_CAMINAR
        dx = self.destino - self.x
        if abs(dx) < 2:
            if self.estado == "huyendo":
                self.estado = "adentro"
                self.salida = random.uniform(0.5, 4.0)   # salen de a una, no todas juntas
            elif self.estado == "saliendo":
                self.estado = "paseo"
            else:
                self.espera -= dt
                if self.espera <= 0:
                    self.destino = random.uniform(90, FIN_PLAZA - 15)
                    self.espera = random.uniform(1.0, 4.0)
            return
        self.mira = 1 if dx > 0 else -1
        avance = min(abs(dx), velocidad * dt)
        self.x += self.mira * avance
        self.paso += avance * 0.25

    def draw(self, surface, piso):
        if self.estado == "adentro":
            return
        y = piso(self.x) - 1
        pierna = math.sin(self.paso) * 4
        cadera = (self.x, y - 9)
        hombro = (self.x, y - 17)
        pygame.draw.line(surface, (40, 40, 50), cadera, (self.x - pierna, y), 2)
        pygame.draw.line(surface, (40, 40, 50), cadera, (self.x + pierna, y), 2)
        pygame.draw.line(surface, self.color, cadera, hombro, 4)
        if self.carga and self.estado != "huyendo":
            pygame.draw.line(surface, (240, 200, 160), hombro, (self.x - 3, y - 25), 2)
            pygame.draw.line(surface, (240, 200, 160), hombro, (self.x + 3, y - 25), 2)
            pygame.draw.rect(surface, (150, 105, 60), (self.x - 6, y - 33, 12, 9))
            pygame.draw.rect(surface, (90, 60, 30), (self.x - 6, y - 33, 12, 9), 1)
        else:
            brazo = -pierna if self.estado != "huyendo" else 0
            alto_brazo = -6 if self.estado == "huyendo" else 0    # corriendo, brazos arriba
            pygame.draw.line(surface, (240, 200, 160), hombro,
                             (self.x + brazo * 0.8 + self.mira * 2, y - 11 + alto_brazo), 2)
        pygame.draw.circle(surface, (240, 200, 160), (int(self.x), int(y - 21)), 4)


class Base:
    """El fortín: se va rompiendo con el daño, se sacude con los golpes y cambia con las mejoras."""

    def __init__(self, terreno, mejora, vidas_max, color_suelo):
        self.terreno = terreno
        self.mejora = mejora               # 1, 2 o 3 (mejora "Base")
        self.vidas_max = vidas_max
        self.suelo_y = terreno.superficie(C.BASE_X / 2)
        self.tiempo = 0.0
        self.sacudon = 0.0
        self.humo = []                     # [x, y, radio, vida]
        self.espera_humo = 0.0
        self.color_plaza = _mezclar(color_suelo, (150, 145, 140), 0.55)
        self.personas = [Persona(i) for i in range(CANT_PERSONAS)]
        self.puerta_x = 4 + ANCHO_TORRE // 2
        rng = random.Random(5)             # grietas siempre iguales
        self.grietas = []
        for _ in range(8):
            x = rng.uniform(12, ANCHO_TORRE - 8)
            y = rng.uniform(25, ALTO_TORRE - 40)
            puntos = [(x, y)]
            for _ in range(3):
                x += rng.uniform(-7, 7)
                y += rng.uniform(6, 13)
                puntos.append((x, y))
            self.grietas.append(puntos)
        self._superficie = None
        self._rojo = None             # silueta roja (torre + torrecita) para cuando la golpean
        self._danio_dibujado = None
        self.tope_torrecita = None

    # ---------- Eventos ----------
    def golpe(self, particulas):
        """Un enemigo llegó: sacudón y pedacitos de piedra."""
        self.sacudon = 0.45
        particulas.emit(C.BASE_X - 6, self.suelo_y - ALTO_TORRE * 0.6, count=16, speed=(60, 240),
                        color=(130, 125, 120), life=(0.5, 1.0), size=(3, 6), gravity=600,
                        angle=-40, spread=80)

    def update(self, dt, peligro, vidas):
        self.tiempo += dt
        self.vidas = vidas
        self.sacudon = max(0.0, self.sacudon - dt)
        for p in self.personas:
            p.update(dt, peligro, self.puerta_x)
        # Humo con 2 corazones o menos
        if 0 < vidas <= 2:
            self.espera_humo -= dt
            if self.espera_humo <= 0:
                self.espera_humo = 0.12 if vidas == 1 else 0.25
                if self.tope_torrecita and random.random() < 0.4:   # también de la torrecita rota
                    hx = self.tope_torrecita[0]
                    hy = self.suelo_y + 2 - self._superficie.get_height() + self.tope_torrecita[1]
                else:
                    hx, hy = random.uniform(15, ANCHO_TORRE - 10), self.suelo_y - ALTO_TORRE + 5
                self.humo.append([hx + random.uniform(-4, 4), hy, random.uniform(5, 8), 1.0])
        for h in self.humo:
            h[1] -= 28 * dt
            h[0] += 10 * dt
            h[2] += 9 * dt
            h[3] -= dt / 2.2
        self.humo = [h for h in self.humo if h[3] > 0]

    # ---------- Dibujo ----------
    def dibujar_plaza(self, surface):
        """Empedrado sobre el suelo (va después del terreno y antes de todo lo demás)."""
        piso = self.terreno.superficie
        borde = [(x, piso(x) - C.GROSOR_SUELO) for x in range(0, FIN_PLAZA + 1, 10)]
        abajo = [(x, y + 16) for x, y in reversed(borde)]
        pygame.draw.polygon(surface, self.color_plaza, borde + abajo)
        oscuro = _mezclar(self.color_plaza, (40, 40, 40), 0.35)
        for fila, desfase in ((0, 0), (8, 9)):
            for x in range(desfase, FIN_PLAZA - 6, 18):
                y = piso(x) - C.GROSOR_SUELO + fila
                pygame.draw.line(surface, oscuro, (x, y), (x, y + 8), 1)
        pygame.draw.lines(surface, oscuro, False, [(x, y + 8) for x, y in borde], 1)
        pygame.draw.lines(surface, _mezclar(self.color_plaza, (255, 255, 255), 0.3), False, borde, 2)
        # Cajas y farol
        x = 150
        y = piso(x) - C.GROSOR_SUELO
        for dx, dy, t in ((0, 0, 16), (16, 0, 16), (8, -14, 14)):
            pygame.draw.rect(surface, (150, 105, 60), (x + dx, y - t + dy, t, t))
            pygame.draw.rect(surface, (90, 60, 30), (x + dx, y - t + dy, t, t), 1)
        x = 205
        y = piso(x) - C.GROSOR_SUELO
        pygame.draw.line(surface, (50, 45, 45), (x, y), (x, y - 48), 3)
        luz = 0.85 + 0.15 * math.sin(self.tiempo * 9)
        brillo = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(brillo, (255, 220, 120, int(70 * luz)), (20, 20), 18)
        surface.blit(brillo, (x - 20, y - 70))
        pygame.draw.rect(surface, (255, 225, 130), (x - 4, y - 56, 8, 9))
        pygame.draw.rect(surface, (50, 45, 45), (x - 5, y - 57, 10, 11), 1)

    def dibujar_empalizada(self, surface):
        """Estacas donde empieza la zona de peligro (donde suena la alarma)."""
        x0 = C.BASE_X + C.ZONA_PELIGRO
        piso = self.terreno.superficie
        puntas = []
        for i in range(4):
            x = x0 - 18 + i * 12
            y = piso(x) - C.GROSOR_SUELO + 3
            alto = 30 + (i % 2) * 6
            puntas.append((x, y - alto * 0.6))
            pygame.draw.polygon(surface, (120, 85, 50), [(x - 4, y), (x - 4, y - alto + 6), (x, y - alto),
                                                         (x + 4, y - alto + 6), (x + 4, y)])
            pygame.draw.polygon(surface, (70, 45, 25), [(x - 4, y), (x - 4, y - alto + 6), (x, y - alto),
                                                        (x + 4, y - alto + 6), (x + 4, y)], 1)
        pygame.draw.lines(surface, (200, 180, 120), False, puntas, 1)

    def _crear_torre(self, perdidas):
        """La torre como imagen (se rehace solo cuando cambia el daño)."""
        ancho, alto = ANCHO_TORRE + 44, ALTO_TORRE + 80
        img = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        ox, piso = 4, alto - 2         # x de la torre dentro de la imagen y su apoyo
        arriba = piso - ALTO_TORRE
        piedra, junta = (150, 145, 138), (105, 100, 95)
        pygame.draw.rect(img, piedra, (ox, arriba, ANCHO_TORRE, ALTO_TORRE))
        rng = random.Random(9)
        for fila, y in enumerate(range(arriba, piso, 12)):
            desfase = 0 if fila % 2 == 0 else 11
            pygame.draw.line(img, junta, (ox, y), (ox + ANCHO_TORRE, y), 1)
            for x in range(ox + desfase, ox + ANCHO_TORRE, 22):
                pygame.draw.line(img, junta, (x, y), (x, min(piso, y + 12)), 1)
                if rng.random() < 0.25:   # algunas piedras de otro tono
                    tono = _mezclar(piedra, (110, 105, 100), rng.uniform(0.2, 0.5))
                    ancho_piedra = min(20, ox + ANCHO_TORRE - x - 2)
                    if ancho_piedra > 3:
                        pygame.draw.rect(img, tono, (x + 1, y + 1, ancho_piedra, min(10, piso - y - 1)))
        # Almenas: con el daño van faltando
        almenas = 5
        faltan = {1, 3, 0}
        faltan = set(list(sorted(faltan))[:max(0, min(3, perdidas - 1))])
        ancho_almena = ANCHO_TORRE / (almenas * 2 - 1)
        for i in range(almenas):
            if i in faltan:
                continue
            x = ox + i * 2 * ancho_almena
            pygame.draw.rect(img, piedra, (x, arriba - 14, ancho_almena, 14))
            pygame.draw.rect(img, junta, (x, arriba - 14, ancho_almena, 14), 1)
        if self.mejora >= 3:            # refuerzos de metal con remaches
            for y in (arriba + 30, piso - 50):
                pygame.draw.rect(img, (95, 100, 110), (ox, y, ANCHO_TORRE, 6))
                for x in range(ox + 5, ox + ANCHO_TORRE, 12):
                    pygame.draw.circle(img, (190, 195, 205), (x, y + 3), 2)
        # Puerta con arco
        px = ox + ANCHO_TORRE // 2
        pygame.draw.rect(img, (95, 60, 30), (px - 12, piso - 34, 24, 34))
        pygame.draw.circle(img, (95, 60, 30), (px, piso - 34), 12)
        for x in (px - 6, px, px + 6):
            pygame.draw.line(img, (70, 45, 20), (x, piso - 40), (x, piso), 1)
        pygame.draw.rect(img, (60, 40, 20), (px - 12, piso - 34, 24, 34), 2)
        # Grietas (una por corazón perdido)
        for puntos in self.grietas[:perdidas]:
            pygame.draw.lines(img, (60, 55, 50), False, [(ox + x, arriba + y) for x, y in puntos], 2)
        pygame.draw.rect(img, (70, 65, 60), (ox, arriba, ANCHO_TORRE, ALTO_TORRE), 2)
        if self.mejora >= 2:
            self._dibujar_torrecita(img, ox + ANCHO_TORRE, piso, perdidas)
        return img

    def _dibujar_torrecita(self, img, derecha, piso, perdidas):
        """Mejora 2: torrecita que sale del costado de la torre como el brazo de un cactus.
        Comparte el daño: grietas, y con pocos corazones se rompe la parte de arriba."""
        piedra, junta, borde = (150, 145, 138), (105, 100, 95), (70, 65, 60)
        vidas = self.vidas_max - perdidas
        # Brazo horizontal que sale de la torre
        brazo = pygame.Rect(derecha - 2, piso - 88, 16, 16)
        # La torrecita: se acorta cuando queda poca vida
        x0, ancho = derecha + 8, 24
        base_y = piso - 72
        alto = 62 if vidas > 2 else (36 if vidas == 2 else 18)
        tope = base_y - alto
        pygame.draw.rect(img, piedra, brazo)
        pygame.draw.rect(img, piedra, (x0, tope, ancho, alto))
        for y in range(tope + 10, base_y, 10):
            pygame.draw.line(img, junta, (x0, y), (x0 + ancho, y), 1)
        pygame.draw.line(img, junta, (x0 + 12, tope), (x0 + 12, base_y), 1)
        # Ménsula de apoyo debajo
        pygame.draw.polygon(img, piedra, [(x0, base_y), (x0 + ancho, base_y), (x0 + 12, base_y + 12)])
        pygame.draw.polygon(img, borde, [(x0, base_y), (x0 + ancho, base_y), (x0 + 12, base_y + 12)], 1)
        if vidas > 2:
            for i in range(3):    # almenitas
                pygame.draw.rect(img, piedra, (x0 + i * 9, tope - 8, 6, 8))
                pygame.draw.rect(img, junta, (x0 + i * 9, tope - 8, 6, 8), 1)
            pygame.draw.rect(img, (255, 210, 110), (x0 + 8, tope + 18, 8, 10))   # ventanita
            pygame.draw.rect(img, borde, (x0 + 8, tope + 18, 8, 10), 1)
        else:
            # Borde roto, irregular
            dientes = [(x0, tope), (x0 + 5, tope - 6), (x0 + 9, tope + 2), (x0 + 15, tope - 4),
                       (x0 + 19, tope + 3), (x0 + ancho, tope - 3)]
            pygame.draw.polygon(img, piedra, dientes + [(x0 + ancho, tope + 4), (x0, tope + 4)])
            pygame.draw.lines(img, borde, False, dientes, 2)
        if perdidas >= 2:         # grietas también en la torrecita
            pygame.draw.lines(img, (60, 55, 50), False,
                              [(x0 + 6, base_y - 4), (x0 + 10, base_y - 14), (x0 + 7, base_y - 22)], 2)
        if perdidas >= 4 and alto > 30:
            pygame.draw.lines(img, (60, 55, 50), False,
                              [(x0 + 18, tope + 8), (x0 + 15, tope + 17), (x0 + 19, tope + 27)], 2)
        pygame.draw.rect(img, borde, (x0, tope, ancho, alto), 2)
        pygame.draw.rect(img, borde, brazo, 2)
        pygame.draw.rect(img, piedra, (brazo.x + 2, brazo.y + 2, brazo.w - 2, brazo.h - 4))   # unión sin borde
        self.tope_torrecita = (x0 + ancho / 2, tope)

    def draw(self, surface, flash):
        perdidas = self.vidas_max - max(0, self.vidas)
        if perdidas != self._danio_dibujado:
            self._superficie = self._crear_torre(perdidas)
            self._rojo = pygame.mask.from_surface(self._superficie).to_surface(
                setcolor=(230, 30, 30, 140), unsetcolor=(0, 0, 0, 0))
            self._danio_dibujado = perdidas
        dx = math.sin(self.tiempo * 70) * 4 * (self.sacudon / 0.45) if self.sacudon > 0 else 0
        img = self._superficie
        x, y = dx, self.suelo_y + 2 - img.get_height()
        surface.blit(img, (x, y))
        arriba = self.suelo_y - ALTO_TORRE
        # Ventanas con luz (titilan)
        for i, (vx, vy) in enumerate(((22, 40), (48, 40), (35, 80))):
            luz = 0.8 + 0.2 * math.sin(self.tiempo * 5 + i * 2)
            pygame.draw.rect(surface, _mezclar((60, 40, 20), (255, 210, 110), luz), (x + vx, arriba + vy, 8, 12))
            pygame.draw.rect(surface, (60, 55, 50), (x + vx, arriba + vy, 8, 12), 1)
        # Bandera (a media asta con un solo corazón)
        mastil_x = x + 4 + ANCHO_TORRE // 2
        tope = arriba - 14 - 45
        pygame.draw.line(surface, (60, 50, 40), (mastil_x, arriba - 14), (mastil_x, tope), 3)
        alto_bandera = tope + (22 if self.vidas == 1 else 2)
        largo = 34 if self.mejora >= 3 else 26
        puntos = []
        for k in range(7):
            t = k / 6
            ola = math.sin(self.tiempo * 6 - t * 4) * 3 * t
            puntos.append((mastil_x + t * largo, alto_bandera + ola))
        puntos += [(px, py + 16) for px, py in reversed(puntos)]
        color_bandera = (40, 90, 200) if self.mejora < 3 else (200, 40, 50)
        pygame.draw.polygon(surface, color_bandera, puntos)
        pygame.draw.polygon(surface, (20, 30, 60), puntos, 1)
        # Banderín de la torrecita (mejora 3, mientras esté entera)
        if self.mejora >= 3 and self.tope_torrecita and self.vidas > 2:
            bx, by = x + self.tope_torrecita[0], y + self.tope_torrecita[1] - 8
            pygame.draw.line(surface, (60, 50, 40), (bx, by), (bx, by - 20), 2)
            ola = math.sin(self.tiempo * 7) * 2
            pygame.draw.polygon(surface, (200, 40, 50), [(bx, by - 20), (bx + 14, by - 16 + ola), (bx, by - 12)])
        # Golpe: torre y torrecita titilan en rojo
        if flash:
            surface.blit(self._rojo, (x, y))
        # Humo
        for hx, hy, r, vida in self.humo:
            humo = pygame.Surface((int(r * 2) + 2, int(r * 2) + 2), pygame.SRCALPHA)
            pygame.draw.circle(humo, (70, 70, 75, int(150 * vida)), (int(r) + 1, int(r) + 1), int(r))
            surface.blit(humo, (x + hx - r, hy - r))

    def dibujar_personas(self, surface):
        for p in self.personas:
            p.draw(surface, self.terreno.superficie)
