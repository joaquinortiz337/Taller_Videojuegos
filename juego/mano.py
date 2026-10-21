# juego/mano.py
import pygame
import pymunk

from juego import config as C
from juego import terreno


class Mano:
    """
    Mecánica base: agarrar y lanzar objetos con el mouse.
    No es un poder: siempre está disponible y no tiene niveles.
    Puede agarrar cualquier objeto que tenga el atributo 'agarrable' en True
    (enemigos, bombas y barriles).

    Cómo se siente el peso: en cada cuadro la mano empuja el objeto hacia el cursor,
    pero con una aceleración máxima que baja con la masa. La gravedad sigue actuando,
    así que levantar algo pesado cuesta más que moverlo de costado. Al soltarlo,
    la velocidad máxima también depende del peso.
    """

    def __init__(self, escena):
        self.escena = escena
        self.agarrada = None
        self.desvio_x = 0.0   # pesados: cuánto "caminaron" alejándose del cursor mientras tocan el suelo

    # ---------- Agarrar ----------
    def agarrar_en(self, pos):
        """Busca un objeto agarrable bajo el cursor y lo agarra."""
        info = self.escena.space.point_query_nearest(pos, 5, pymunk.ShapeFilter())
        if info is None:
            return False
        obj = getattr(info.shape, "parent", None)
        if obj is None or not getattr(obj, "agarrable", False):
            return False
        self.agarrar(obj, pos)
        return True

    def agarrar(self, obj, pos=None):
        """Agarra un objeto concreto (lo usa también la bomba al aparecer)."""
        self.soltar()
        obj.agarrada = True
        self.agarrada = obj
        self.desvio_x = 0.0
        self.escena.sonido("agarrar", 0.6)

    # ---------- Mover ----------
    def _aceleracion_maxima(self, obj):
        """Los enemigos tienen su propio 'agarre'; bombas y barriles usan la fórmula por peso."""
        propio = getattr(obj, "datos", {}).get("agarre")
        if propio:
            return propio
        return C.MANO_ACELERACION / (obj.body.mass ** C.MANO_PESO_ACELERACION)

    def _velocidad_lanzamiento(self, obj):
        propio = getattr(obj, "datos", {}).get("lanzamiento")
        if propio:
            return propio
        return C.MANO_VEL_MAX / (obj.body.mass ** C.MANO_PESO_VELOCIDAD)

    def update(self, objetivo, dt):
        """Se llama en cada cuadro ANTES de avanzar la física: lleva el objeto hacia el cursor."""
        if self.agarrada is None:
            return
        obj = self.agarrada
        body = obj.body
        # Si el cursor se aleja demasiado de lo agarrado, la "cuerda" se corta y se suelta
        if (pymunk.Vec2d(*objetivo) - body.position).length > C.CUERDA_LARGO_MAXIMO:
            self._cortar_cuerda(objetivo)
            return
        # Enemigos pesados: si tocan el suelo siguen caminando hacia la base aunque los
        # tengas agarrados (se van corriendo del cursor). Al levantarlos vuelven a la mano.
        if getattr(obj, "pesado", False) and obj.en_suelo():
            self.desvio_x -= obj.vel * C.TIRON_PESADO * dt
        else:
            self.desvio_x *= 0.85
        objetivo = (objetivo[0] + self.desvio_x, objetivo[1])
        # Nunca intentar llevarlo más abajo que el suelo (si no, se hunde al apretarlo)
        bb = obj.shape.bb
        medio_alto = (bb.top - bb.bottom) / 2
        piso = terreno.superficie(body.position.x) - medio_alto
        objetivo = (objetivo[0], min(objetivo[1], piso))
        # Velocidad con la que "querría" ir para llegar al cursor
        deseada = (pymunk.Vec2d(*objetivo) - body.position) * C.MANO_SEGUIMIENTO
        if deseada.length > C.MANO_VEL_SEGUIMIENTO:
            deseada = deseada.scale_to_length(C.MANO_VEL_SEGUIMIENTO)
        # Pero solo puede cambiar su velocidad de a poco, según el peso
        cambio = deseada - body.velocity
        maximo = self._aceleracion_maxima(obj) * dt
        if cambio.length > maximo:
            cambio = cambio.scale_to_length(maximo)
        body.velocity = body.velocity + cambio

    def _cortar_cuerda(self, punto):
        self.escena.sonido("corte")
        self.escena.particulas.emit(punto[0], punto[1], count=8, speed=(60, 180), color=(240, 240, 240),
                                    life=(0.15, 0.35), size=(1, 3), gravity=300)
        self.soltar()   # como soltarlo: sale con su velocidad y cuenta como lanzado por vos

    # ---------- Soltar ----------
    def soltar(self):
        obj = self.agarrada
        if obj is None:
            return
        obj.agarrada = False
        if hasattr(obj, "al_ser_soltada"):
            obj.al_ser_soltada()
        v = obj.body.velocity
        tope = self._velocidad_lanzamiento(obj)
        if v.length > tope:
            obj.body.velocity = v.scale_to_length(tope)
        velocidad = obj.body.velocity.length
        if velocidad > 600:
            self.escena.sonido("lanzar", min(1.0, velocidad / C.MANO_VEL_MAX))
        self.agarrada = None

    def draw(self, surface):
        if self.agarrada is not None:
            a = self.agarrada.position
            pygame.draw.line(surface, (255, 255, 255), (a.x, a.y), self.escena.mouse_mundo(), 2)
