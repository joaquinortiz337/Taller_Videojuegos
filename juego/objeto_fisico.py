# juego/objeto_fisico.py
import math
from collections import deque
import pygame
import pymunk

from engine.game_object import GameObject
from juego import config as C


class ObjetoFisico(GameObject):
    """
    Clase base de NUESTROS objetos con físicas (Pymunk). Hereda del GameObject del motor.

    El motor del curso trae su propio PhysicsObject, pero ese crea el cuerpo solo como
    caja o círculo y siempre rota la imagen. Nosotros necesitamos además:
      - cuerpos que no giran (enemigos), cinemáticos (agujero negro) y formas a medida,
      - rotar la imagen solo cuando corresponde,
      - métodos auxiliares (apply_impulse, remove_from_space, position, velocity).
    Por eso lo definimos aparte, sin modificar el motor.

    Une un GameObject (imagen + rect + animación) con un cuerpo y una forma
    de Pymunk. En cada update copia la posición (y opcionalmente la rotación)
    del cuerpo físico al sprite, para que se dibuje donde está el objeto.

    Las clases hijas crean su propio body y shape (círculo, caja, polígono...)
    y se los pasan a este constructor.
    """

    con_estela = False   # las subclases que quieran estela lo ponen en True

    def __init__(self, x, y, frames, space, body, shape, rotate_image=False):
        super().__init__(x, y, frames)
        self.estela = deque(maxlen=C.ESTELA_LARGO)   # [(imagen, centro)] de las últimas posiciones
        self.space = space
        self.body = body
        self.shape = shape
        self.rotate_image = rotate_image

        self.body.position = (x, y)
        # Referencia inversa: desde la forma llegamos al objeto del juego
        # (misma convención que el motor: shape.parent). Útil en los callbacks de colisión.
        self.shape.parent = self

        self.space.add(self.body, self.shape)
        self.sync_sprite()

    @property
    def position(self):
        return self.body.position

    @property
    def velocity(self):
        return self.body.velocity

    def apply_impulse(self, impulse):
        """Aplica un impulso (vector) en el centro del cuerpo."""
        self.body.apply_impulse_at_world_point(impulse, self.body.position)

    def sync_sprite(self):
        """Copia la posición/rotación del cuerpo físico a self.image y self.rect."""
        base = self.frames[self.current_frame] if self.is_animated else self.frames[0]
        if self.rotate_image:
            self.image = pygame.transform.rotate(base, -math.degrees(self.body.angle))
        else:
            self.image = base
        x, y = self.body.position
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)  # animación del GameObject
        self.sync_sprite()
        self._actualizar_estela()

    # ---------- Estela ----------
    def _actualizar_estela(self):
        if not self.con_estela or C.ESTELA_VELOCIDAD <= 0:
            return
        if self.body.velocity.length > C.ESTELA_VELOCIDAD:
            self.estela.append((self.image, self.rect.center))
        elif self.estela:
            self.estela.popleft()          # al frenar, la estela se va acortando

    def dibujar_estela(self, surface):
        n = len(self.estela)
        for i, (img, centro) in enumerate(self.estela):
            fantasma = img.copy()
            fantasma.set_alpha(int(110 * (i + 1) / (n + 1)))
            surface.blit(fantasma, fantasma.get_rect(center=centro))

    def draw(self, surface):
        if self.estela:
            self.dibujar_estela(surface)
        super().draw(surface)

    def remove_from_space(self):
        """Saca el objeto de la simulación y de todos los grupos de sprites."""
        if self.body in self.space.bodies:
            self.space.remove(self.body, self.shape)
        self.kill()
