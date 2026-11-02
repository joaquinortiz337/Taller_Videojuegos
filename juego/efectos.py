# juego/efectos.py
import math
import random
import pygame

from engine.game_object import GameObject  # Hereda del motor


class EfectoOnda(GameObject):
    """Círculo que se expande y se desvanece (explosiones, ráfagas, etc.)."""

    def __init__(self, x, y, radio_max, color, duracion=0.35):
        self.radio_max = radio_max
        self.color = color
        self.duracion = duracion
        self.tiempo = 0.0
        tam = radio_max * 2 + 4
        super().__init__(x, y, pygame.Surface((tam, tam), pygame.SRCALPHA))

    @property
    def terminado(self):
        return self.tiempo >= self.duracion

    def update(self, dt):
        self.tiempo += dt
        progreso = min(1.0, self.tiempo / self.duracion)
        self.image.fill((0, 0, 0, 0))
        radio = int(self.radio_max * progreso)
        alfa = int(200 * (1 - progreso))
        centro = (self.image.get_width() // 2, self.image.get_height() // 2)
        if radio > 2:
            pygame.draw.circle(self.image, (*self.color, alfa), centro, radio, 4)
        super().update()


class EfectoCruz(GameObject):
    """Crucecita verde que sube y se desvanece (enemigo curado por el chamán)."""

    def __init__(self, x, y, duracion=0.8):
        self.duracion = duracion
        self.tiempo = 0.0
        self.y = y
        img = pygame.Surface((14, 14), pygame.SRCALPHA)
        pygame.draw.rect(img, (90, 230, 120), (5, 0, 4, 14))
        pygame.draw.rect(img, (90, 230, 120), (0, 5, 14, 4))
        super().__init__(x, y, img)

    @property
    def terminado(self):
        return self.tiempo >= self.duracion

    def update(self, dt):
        self.tiempo += dt
        self.y -= 35 * dt
        self.rect.centery = int(self.y)
        self.image.set_alpha(int(255 * (1 - min(1.0, self.tiempo / self.duracion))))
        super().update()


class TextoFlotante(GameObject):
    """Texto chico que sube y se desvanece (ej: '+15' de energía)."""

    def __init__(self, x, y, texto, color, duracion=1.0, tam=32):
        self.duracion = duracion
        self.tiempo = 0.0
        self.y = y
        fuente = pygame.font.Font(None, tam)
        base = fuente.render(texto, True, color)
        sombra = fuente.render(texto, True, (20, 20, 30))
        img = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)
        img.blit(sombra, (2, 2))
        img.blit(base, (0, 0))
        super().__init__(x, y, img)

    @property
    def terminado(self):
        return self.tiempo >= self.duracion

    def update(self, dt):
        self.tiempo += dt
        self.y -= 40 * dt
        self.rect.centery = int(self.y)
        self.image.set_alpha(int(255 * (1 - min(1.0, self.tiempo / self.duracion))))
        super().update()


class EfectoRayo(GameObject):
    """Rayo en zigzag que pasa por una lista de puntos, con destello."""

    def __init__(self, puntos, ancho_pantalla, alto_pantalla, duracion=0.35):
        self.puntos = puntos
        self.duracion = duracion
        self.tiempo = 0.0
        self.ancho, self.alto = ancho_pantalla, alto_pantalla
        super().__init__(ancho_pantalla // 2, alto_pantalla // 2,
                         pygame.Surface((ancho_pantalla, alto_pantalla), pygame.SRCALPHA))
        # El zigzag se calcula una sola vez para que no "tiemble"
        self.trazo = self._zigzag(puntos)

    @staticmethod
    def _zigzag(puntos):
        trazo = [puntos[0]]
        for (x1, y1), (x2, y2) in zip(puntos, puntos[1:]):
            pasos = max(3, int(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 // 25))
            for k in range(1, pasos):
                t = k / pasos
                trazo.append((x1 + (x2 - x1) * t + random.randint(-10, 10),
                              y1 + (y2 - y1) * t + random.randint(-10, 10)))
            trazo.append((x2, y2))
        return trazo

    @property
    def terminado(self):
        return self.tiempo >= self.duracion

    def update(self, dt):
        self.tiempo += dt
        prop = 1 - min(1.0, self.tiempo / self.duracion)
        self.image.fill((255, 255, 255, int(70 * prop * prop)))  # destello
        if len(self.trazo) > 1:
            pygame.draw.lines(self.image, (255, 255, 180, int(255 * prop)), False, self.trazo, 6)
            pygame.draw.lines(self.image, (255, 255, 255, int(255 * prop)), False, self.trazo, 2)
        super().update()


def aplicar_explosion(objetos, centro, radio, fuerza, danio):
    """
    Empuja hacia afuera y daña a todos los objetos dentro del radio.
    El efecto es máximo en el centro y cae a cero en el borde.
    Como es un impulso fijo, a los objetos pesados los mueve menos.
    """
    for obj in objetos:
        direccion = obj.position - centro
        distancia = direccion.length
        if distancia >= radio:
            continue
        intensidad = 1 - distancia / radio
        if distancia < 1:
            direccion = type(obj.position)(0, -1)
        empuje = direccion.normalized() * fuerza * intensidad
        empuje = type(empuje)(empuje.x, empuje.y - fuerza * 0.3 * intensidad)  # un poco hacia arriba
        obj.apply_impulse(empuje)
        if hasattr(obj, "recibir_danio"):
            obj.recibir_danio(danio * intensidad)


class Temblor:
    """Sacudida de pantalla: un desplazamiento al azar que se va apagando."""

    def __init__(self, amortiguacion):
        self.intensidad = 0.0
        self.amortiguacion = amortiguacion
        self.offset = (0, 0)

    def agregar(self, intensidad):
        self.intensidad = max(self.intensidad, intensidad)   # no se acumula: gana el más fuerte

    def update(self):
        if self.intensidad < 0.5:
            self.intensidad = 0.0
            self.offset = (0, 0)
            return
        i = int(self.intensidad)
        self.offset = (random.randint(-i, i), random.randint(-i, i))
        self.intensidad *= self.amortiguacion


class TextoCombo:
    """Texto de combo que aparece grande y rebota hasta su tamaño. Queda visible
    mientras dure el combo y se desvanece cuando termina (terminar())."""
    DESVANECER = 0.3

    def __init__(self, combo, energia=0):
        self.combo = combo
        self.tiempo = 0.0
        self.fin = None   # tiempo en que empezó a desvanecerse
        if combo >= 5:
            self.color = (255, 60, 40)
        elif combo >= 3:
            self.color = (255, 150, 40)
        else:
            self.color = (255, 220, 60)
        tam = min(90, 48 + 8 * (combo - 2))
        fuente = pygame.font.Font(None, tam)
        texto = f"¡Combo x{combo}!" + (f"  +{energia}" if energia else "")
        base = fuente.render(texto, True, self.color)
        sombra = fuente.render(texto, True, (40, 20, 10))
        self.imagen = pygame.Surface((base.get_width() + 3, base.get_height() + 3), pygame.SRCALPHA)
        self.imagen.blit(sombra, (3, 3))
        self.imagen.blit(base, (0, 0))

    def terminar(self):
        if self.fin is None:
            self.fin = self.tiempo

    @property
    def terminado(self):
        return self.fin is not None and self.tiempo - self.fin >= self.DESVANECER

    def update(self, dt):
        self.tiempo += dt

    def draw(self, surface, centro):
        t = self.tiempo
        escala = 1 + 0.9 * math.exp(-10 * t) * math.cos(16 * t)   # rebote amortiguado
        img = pygame.transform.rotozoom(self.imagen, 0, max(0.1, escala))
        if self.fin is not None:
            restante = self.DESVANECER - (t - self.fin)
            img.set_alpha(int(255 * max(0, restante) / self.DESVANECER))
        surface.blit(img, img.get_rect(center=centro))

