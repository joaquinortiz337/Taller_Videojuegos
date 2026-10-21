# juego/bloques.py
import math
import pygame
import pymunk

from juego.objeto_fisico import ObjetoFisico  # Hereda del GameObject del motor
from juego import config as C
from juego import terreno


class Bloque(ObjetoFisico):
    """
    Bloque rígido de un material (madera, piedra, metal...).
    El material define su masa, resistencia, fricción y color.
    Se daña por impactos fuertes y por el ataque de los enemigos.
    """

    def __init__(self, space, material, x, y, duracion=None):
        datos = C.MATERIALES[material]
        self.material = material
        self.vida_max = datos["vida"]
        self.vida = datos["vida"]
        self.umbral = datos["umbral"]
        self.color = datos["color"]
        self.duracion = duracion          # None = no desaparece solo
        self.invulnerable = 0.0           # segundos sin daño por choques tras un golpe
        self.uniones = []                 # uniones con los bloques vecinos del mismo muro
        self.tam = C.TAM_BLOQUE

        masa = datos["masa"]
        body = pymunk.Body(masa, pymunk.moment_for_box(masa, (self.tam, self.tam)))
        shape = pymunk.Poly.create_box(body, (self.tam, self.tam), radius=0.5)
        shape.friction = datos["friccion"]
        shape.elasticity = datos["elasticidad"]
        shape.collision_type = C.TIPO_BLOQUE

        super().__init__(x, y, self._crear_imagen(), space, body, shape, rotate_image=True)
        self.body.parent_bloque = self

    # ---------- Imagen ----------
    def _crear_imagen(self):
        """Imagen provisoria: color del material + grietas según el daño."""
        img = pygame.Surface((self.tam, self.tam), pygame.SRCALPHA)
        img.fill(self.color)
        pygame.draw.rect(img, (30, 30, 30), img.get_rect(), 2)
        danio = 1 - max(0, self.vida) / self.vida_max
        if danio > 0.33:
            pygame.draw.line(img, (30, 30, 30), (4, 6), (self.tam // 2, self.tam // 2), 2)
        if danio > 0.66:
            pygame.draw.line(img, (30, 30, 30), (self.tam - 5, 4), (8, self.tam - 6), 2)
        return img

    def _actualizar_imagen(self):
        self.frames = [self._crear_imagen()]

    # ---------- Daño ----------
    @property
    def destruido(self):
        return self.vida <= 0 or (self.duracion is not None and self.duracion <= 0)

    def despegar(self):
        """Suelta este bloque de sus vecinos (el muro se empieza a desarmar)."""
        for union in list(self.uniones):
            self._quitar_union(union)

    def recibir_danio(self, cantidad):
        if cantidad >= C.MURO_DANIO_SEPARA:
            self.despegar()
        vida_antes = self.vida
        self.vida -= cantidad
        # Solo redibujamos si cambió de "etapa" de grietas (más eficiente)
        if int(vida_antes / self.vida_max * 3) != int(max(0, self.vida) / self.vida_max * 3):
            self._actualizar_imagen()

    def recibir_impacto(self, impulso, otro=None):
        """Llamado desde el callback de colisión con el impulso del choque."""
        delta_v = impulso / self.body.mass   # los pesados casi no se inmutan
        danio = (delta_v - self.umbral) * C.FACTOR_DANIO_BLOQUE
        if danio < C.DANIO_MINIMO or self.invulnerable > 0:
            return   # golpe muy chico, o acaba de recibir uno
        self.recibir_danio(danio)
        self.invulnerable = C.INVULNERABLE_CHOQUE

    # ---------- Ciclo ----------
    def update(self, dt=1 / C.FPS):
        if self.duracion is not None:
            self.duracion -= dt
        if self.invulnerable > 0:
            self.invulnerable -= dt
        super().update()

    def _quitar_union(self, union):
        for bloque in (union.a.parent_bloque, union.b.parent_bloque):
            if union in bloque.uniones:
                bloque.uniones.remove(union)
        if union in self.space.constraints:
            self.space.remove(union)

    def remove_from_space(self):
        for union in list(self.uniones):
            self._quitar_union(union)
        super().remove_from_space()


def construir_muro(space, material, x, duracion=C.MURO_DURACION):
    """
    Crea un muro de MURO_COLUMNAS x MURO_FILAS bloques apoyado en el suelo,
    centrado en x. En una pendiente, el muro se apoya inclinado siguiendo el
    terreno (perpendicular al suelo), así no se vuelca ni se desliza.
    Devuelve la lista de bloques creados.
    """
    t = C.TAM_BLOQUE
    angulo = math.atan(terreno.pendiente(x))
    cos_a, sin_a = math.cos(angulo), math.sin(angulo)
    base_x, base_y = x, terreno.superficie(x) - 2
    bloques = []
    for fila in range(C.MURO_FILAS):
        for col in range(C.MURO_COLUMNAS):
            # Posición dentro del muro (x hacia la derecha a lo largo del suelo, y hacia arriba)
            lx = (col - (C.MURO_COLUMNAS - 1) / 2) * t
            ly = -(t / 2 + fila * t)
            # Girada según la pendiente
            bx = base_x + lx * cos_a - ly * sin_a
            by = base_y + lx * sin_a + ly * cos_a
            b = Bloque(space, material, bx, by, duracion)
            b.body.angle = angulo
            b.sync_sprite()
            bloques.append(b)

    # Unir cada bloque con el de su derecha y el de arriba (como si tuvieran mezcla):
    # el muro se comporta como una sola pieza hasta que un golpe fuerte despega bloques.

    def bloque(fila, col):
        return bloques[fila * C.MURO_COLUMNAS + col]

    def unir(a, b):
        """Soldadura entre dos bloques: un punto de giro en el centro del lado que
        comparten + un engranaje que impide que giren uno respecto del otro."""
        medio = (a.body.position + b.body.position) / 2
        pivote = pymunk.PivotJoint(a.body, b.body, medio)
        engranaje = pymunk.GearJoint(a.body, b.body, b.body.angle - a.body.angle, 1)
        for union in (pivote, engranaje):
            union.collide_bodies = False   # los bloques unidos no chocan entre sí
            space.add(union)
            a.uniones.append(union)
            b.uniones.append(union)

    for fila in range(C.MURO_FILAS):
        for col in range(C.MURO_COLUMNAS):
            if col + 1 < C.MURO_COLUMNAS:
                unir(bloque(fila, col), bloque(fila, col + 1))
            if fila + 1 < C.MURO_FILAS:
                unir(bloque(fila, col), bloque(fila + 1, col))
    return bloques
