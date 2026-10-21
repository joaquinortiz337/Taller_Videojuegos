# juego/objetos.py
# Objetos físicos que crean los poderes (bomba, agujero negro).
import pygame
import pymunk

from juego.objeto_fisico import ObjetoFisico  # Hereda del GameObject del motor
from juego import config as C
from juego import terreno


def _imagen_bomba(radio, encendida):
    tam = radio * 2 + 8
    img = pygame.Surface((tam, tam), pygame.SRCALPHA)
    c = tam // 2
    color = (220, 60, 40) if encendida else (35, 35, 35)
    pygame.draw.circle(img, color, (c, c + 2), radio)
    pygame.draw.circle(img, (90, 90, 90), (c - radio // 3, c - radio // 3 + 2), max(2, radio // 4))
    pygame.draw.line(img, (150, 110, 60), (c, c + 2 - radio), (c + 3, 1), 2)  # mecha
    return img


class Bomba(ObjetoFisico):
    """
    Bomba física: se agarra y se lanza con la mano.
    Solo explota por tiempo: la mecha empieza a correr al soltarla.
    Parpadea cada vez más rápido a medida que se acaba la mecha.
    """
    agarrable = True
    con_estela = True

    def __init__(self, space, x, y, mecha, radio_explosion, fuerza, danio,
                 racimo=False, tam=12, encendida=False):
        self.mecha = mecha
        self.radio_explosion = radio_explosion
        self.fuerza = fuerza
        self.danio = danio
        self.racimo = racimo
        self.tam = tam
        self.agarrada = False
        self.encendida = encendida   # la mecha corre solo si está encendida
        self._img_normal = _imagen_bomba(tam, False)
        self._img_roja = _imagen_bomba(tam, True)

        masa = 2 if tam >= 12 else 1
        body = pymunk.Body(masa, pymunk.moment_for_circle(masa, 0, tam))
        shape = pymunk.Circle(body, tam)
        shape.friction = 0.7
        shape.elasticity = 0.4
        super().__init__(x, y, self._img_normal, space, body, shape)

    @property
    def lista_para_explotar(self):
        return self.encendida and self.mecha <= 0

    def al_ser_soltada(self):
        self.encendida = True

    def update(self, dt=1 / C.FPS):
        if self.encendida:
            self.mecha -= dt
        # Parpadeo: más rápido cuanto menos mecha queda
        if self.encendida:
            frecuencia = 2 if self.mecha > 1.5 else (5 if self.mecha > 0.6 else 12)
            roja = int(self.mecha * frecuencia) % 2 == 0
            self.frames = [self._img_roja if roja else self._img_normal]
        super().update()


class AgujeroNegro(ObjetoFisico):
    """
    Queda fijo donde lo ponés (también en el cielo) y atrae a los enemigos
    dentro de su radio durante un tiempo. Los enemigos chocan contra él y entre sí.
    """

    def __init__(self, space, x, y, radio, duracion, fuerza, danio_centro):
        self.radio = radio
        self.duracion = duracion
        self.fuerza = fuerza
        self.danio_centro = danio_centro
        self.tiempo = 0.0
        self.tam = 18

        body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)  # no lo mueve nada
        shape = pymunk.Circle(body, self.tam)
        shape.friction = 0.5
        imagen = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
        super().__init__(x, y, imagen, space, body, shape)
        self._dibujar()

    @property
    def terminado(self):
        return self.tiempo >= self.duracion

    def atraer(self, enemigos, dt):
        """Aplica la atracción. Se llama ANTES de avanzar la física."""
        centro = self.body.position
        for c in enemigos:
            if c.inmune_agujero:
                continue
            direccion = centro - c.position
            d = direccion.length
            if d > self.radio or d < 1:
                continue
            c.atraida = True
            c.marcar_lanzado()   # lo está moviendo el agujero: sus golpes y su caída cuentan
            # Fuerza fija (más fuerte cerca del centro): a los pesados les cuesta más
            f = self.fuerza * (0.6 + 0.4 * (1 - d / self.radio))
            c.body.apply_force_at_world_point(direccion.normalized() * f, c.position)
            # Un poco de "rozamiento" para que se amontonen en vez de orbitar
            c.body.velocity = c.body.velocity * 0.97
            # Nivel 3: daño continuo a las que quedan pegadas al centro
            if self.danio_centro and d < self.tam + c.radio + 8:
                c.recibir_danio(self.danio_centro * dt)

    def _dibujar(self):
        img = self.frames[0]
        img.fill((0, 0, 0, 0))
        c = self.radio
        alfa = 60 if self.duracion - self.tiempo > 0.5 else int(120 * (self.duracion - self.tiempo))
        pygame.draw.circle(img, (120, 60, 200, max(0, alfa)), (c, c), self.radio, 2)
        giro = int(self.tiempo * 20) % 6
        pygame.draw.circle(img, (90, 40, 160), (c, c), self.tam + 6 + giro % 3)
        pygame.draw.circle(img, (10, 0, 20), (c, c), self.tam)

    def update(self, dt=1 / C.FPS):
        self.tiempo += dt
        self._dibujar()
        super().update()


def _imagen_barril(ancho, alto):
    img = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    pygame.draw.rect(img, (170, 40, 30), img.get_rect(), border_radius=5)
    for y in (6, alto - 9):
        pygame.draw.rect(img, (60, 60, 60), (0, y, ancho, 3))       # aros
    pygame.draw.rect(img, (240, 200, 40), (ancho // 2 - 5, alto // 2 - 5, 10, 10))  # símbolo
    pygame.draw.rect(img, (30, 30, 30), img.get_rect(), 2, border_radius=5)
    return img


class Barril(ObjetoFisico):
    """
    Elemento de ayuda del mapa. Se agarra y se tira como un enemigo.
    Explota SOLO al chocar con un enemigo a cierta velocidad (C.BARRIL["velocidad_explosion"]),
    y solo si lo moviste vos: agarrado o lanzado. Un enemigo que le tirás encima, o una
    explosión que lo empuja, no lo hacen explotar. Contra el suelo o un muro no pasa nada.
    (La escena es la que mide la velocidad del choque y marca 'explotar'.)
    """
    agarrable = True
    con_estela = True

    def __init__(self, space, x):
        d = C.BARRIL
        self.datos = d
        self.agarrada = False
        self.explotar = False     # la escena lo hace explotar cuando esto es True
        self._lanzado = False     # lo soltaste vos y todavía no quedó quieto
        self._calma = 0.0
        body = pymunk.Body(d["masa"], pymunk.moment_for_box(d["masa"], (d["ancho"], d["alto"])))
        shape = pymunk.Poly.create_box(body, (d["ancho"], d["alto"]), radius=1)
        shape.friction = 0.8
        shape.elasticity = 0.2
        y = terreno.superficie(x) - d["alto"] / 2 - 1
        super().__init__(x, y, _imagen_barril(d["ancho"], d["alto"]), space, body, shape,
                         rotate_image=True)

    @property
    def radio_explosion(self):
        return self.datos["radio_explosion"]

    @property
    def lanzado(self):
        """True si lo tenés agarrado o lo lanzaste y todavía no quedó quieto."""
        return self.agarrada or self._lanzado

    def al_ser_soltada(self):
        self._lanzado = True
        self._calma = 0.0

    def update(self, dt=1 / C.FPS):
        if self._lanzado and not self.agarrada:
            quieto = self.body.velocity.length < 30
            self._calma = self._calma + dt if quieto else 0.0
            if self._calma >= 0.25:
                self._lanzado = False
        super().update()
