# juego/poderes.py
import pymunk

from juego import config as C
from juego import terreno
from juego.bloques import construir_muro
from juego.objetos import Bomba, AgujeroNegro
from juego.efectos import EfectoRayo


class Poder:
    """
    Clase base de los poderes. El costo es fijo; los valores del efecto
    (radio, daño, etc.) se leen de C.PODERES según el nivel actual,
    así mejorar un poder es solo cambiar su nivel.
    """
    clave = ""

    def __init__(self, escena, nivel=1):
        self.escena = escena
        self.nivel = nivel
        self.recarga = 0.0

    # ---- Datos ----
    @property
    def datos(self):
        return C.PODERES[self.clave]

    @property
    def nombre(self):
        return self.datos["nombre"]

    @property
    def costo(self):
        return self.datos["costo"]

    @property
    def recarga_total(self):
        return self.datos.get("recarga", 0)   # solo el rayo tiene

    @property
    def stats(self):
        return self.datos["niveles"][self.nivel - 1]

    @property
    def nivel_max(self):
        return len(self.datos["niveles"])

    # ---- Uso ----
    def disponible(self):
        return self.recarga <= 0 and self.escena.energia >= self.costo

    def usar(self, pos):
        """Intenta usar el poder en pos. Devuelve True si se usó."""
        if not self.disponible():
            return False
        if self.activar(pos):
            self.escena.energia -= self.costo
            self.recarga = self.recarga_total
            return True
        return False

    def activar(self, pos):
        """Lo implementa cada poder. Devuelve True si se pudo usar."""
        raise NotImplementedError

    def update(self, dt):
        if self.recarga > 0:
            self.recarga -= dt


class PoderBomba(Poder):
    """Crea una bomba ya agarrada por la mano; explota 'mecha' segundos después de soltarla."""
    clave = "bomba"

    def activar(self, pos):
        s = self.stats
        bomba = Bomba(self.escena.space, pos[0], pos[1], s["mecha"],
                      s["radio"], s["fuerza"], s["danio"], s["racimo"])
        self.escena.bombas.add(bomba)
        self.escena.mano.agarrar(bomba, pos)
        return True


class PoderAgujero(Poder):
    """Agujero negro fijo en el punto elegido (puede ser en el cielo)."""
    clave = "agujero"

    def activar(self, pos):
        s = self.stats
        agujero = AgujeroNegro(self.escena.space, pos[0], pos[1],
                               s["radio"], s["duracion"], s["fuerza"], s["danio_centro"])
        self.escena.agujeros.add(agujero)
        return True


class PoderMuro(Poder):
    """Muro temporal apoyado en el suelo; el nivel define el material."""
    clave = "muro"

    def activar(self, pos):
        bloques = construir_muro(self.escena.space, self.stats["material"], pos[0])
        self.escena.bloques.add(*bloques)
        return True


class PoderRayo(Poder):
    """
    Rayo del cielo: mucho daño al enemigo más cercano al punto y salta en
    cadena a las siguientes (cada salto hace un poco menos). Paraliza, no empuja.
    """
    clave = "rayo"
    RADIO_IMPACTO = 60

    def activar(self, pos):
        s = self.stats
        punto = pymunk.Vec2d(*pos)
        enemigos = [c for c in self.escena.enemigos if c.viva]

        primera = min(enemigos, key=lambda c: (c.position - punto).length, default=None)
        if primera is None or (primera.position - punto).length > self.RADIO_IMPACTO:
            # No hay nadie cerca: el rayo cae en el suelo y daña bloques muy cercanos
            suelo = (pos[0], terreno.superficie(pos[0]))
            for b in self.escena.bloques:
                if (b.position - pymunk.Vec2d(*suelo)).length < 40:
                    b.recibir_danio(s["danio"] * 0.5)
            self.escena.efectos.add(EfectoRayo([(pos[0], 0), suelo], self.escena.ancho_mundo, C.ALTO))
            self.escena.efecto_rayo([suelo])
            return True

        # Cadena: de la primera a la más cercana que todavía no recibió el rayo
        golpeadas = [primera]
        actual = primera
        for _ in range(s["saltos"]):
            candidatas = [c for c in enemigos if c not in golpeadas
                          and (c.position - actual.position).length <= s["dist_salto"]]
            if not candidatas:
                break
            actual = min(candidatas, key=lambda c: (c.position - actual.position).length)
            golpeadas.append(actual)

        danio = s["danio"]
        for c in golpeadas:
            c.recibir_danio(danio)
            c.paralizar(s["paralisis"])
            danio *= s["decaimiento"]

        puntos = [(primera.position.x, 0)] + [(c.position.x, c.position.y) for c in golpeadas]
        self.escena.efectos.add(EfectoRayo(puntos, self.escena.ancho_mundo, C.ALTO))
        self.escena.efecto_rayo([(c.position.x, c.position.y) for c in golpeadas])
        return True


CLASES_PODER = {"bomba": PoderBomba, "agujero": PoderAgujero,
                "muro": PoderMuro, "rayo": PoderRayo}


def crear_poderes(escena, niveles):
    """Crea los poderes en el orden de las teclas 1, 2, 3, 4."""
    return [CLASES_PODER[clave](escena, niveles.get(clave, 1)) for clave in C.ORDEN_PODERES]
