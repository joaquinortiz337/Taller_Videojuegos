# juego/entities.py
# Enemigos: una clase base con todo lo común y una subclase por tipo.
import math
import random
import pygame
import pymunk

from juego.objeto_fisico import ObjetoFisico  # Hereda del GameObject del motor
from juego import config as C
from juego.bloques import Bloque
from juego.objetos import Bomba
from juego import terreno


def crear_imagen_enemigo(radio, color):
    """Imagen provisoria dibujada por código (después se reemplaza por sprites)."""
    tam = radio * 2 + 2
    img = pygame.Surface((tam, tam), pygame.SRCALPHA)
    centro = (tam // 2, tam // 2)
    pygame.draw.circle(img, color, centro, radio)
    ojo = (centro[0] - radio // 3, centro[1] - radio // 4)
    pygame.draw.circle(img, (240, 220, 40), ojo, max(3, radio // 4))
    pygame.draw.circle(img, (0, 0, 0), (ojo[0] - 1, ojo[1]), max(1, radio // 8))
    return img


class Enemigo(ObjetoFisico):
    """
    Comportamiento común a todos los enemigos: caminar hacia la base, frenarse
    contra los muros, hacer fila, recibir daño por impactos y por poderes.

    "Ganchos" que las subclases pueden cambiar:
      al_tocar_bloques(bloques, dt) -> True si se frena
      al_morir(escena)              -> qué pasa cuando muere
      al_llegar_a_base(escena)      -> qué pasa si llega a la base
    """
    inmune_agujero = False
    es_enemigo = True
    con_estela = True

    def __init__(self, space, clave, x, y=None):
        datos = C.ENEMIGOS[clave]
        self.clave = clave
        self.datos = datos
        self.radio = datos["radio"]
        self.vida_max = datos["vida"]
        self.vida = datos["vida"]
        self.vel = datos["vel"]
        self.ataque = datos["ataque"]
        self.puntos = datos["puntos"]
        self.pesado = datos.get("pesado", False)
        self.valor_combo = datos.get("valor_combo", 1)
        self.danio_base = datos["danio_base"]

        self.agarrada = False
        self.aturdida = 0.0     # segundos sin caminar después de un golpe
        self.paralizada = 0.0   # segundos paralizada (rayo)
        # Contactos del último cuadro (ver leer_contactos)
        self.pisando = False
        self.normal_piso = None
        self.algo_encima = False
        self.bloqueado = False
        self.saltando = False
        self.salto_reciente = False
        # "Lanzado": lo puso en movimiento algo externo (la mano, una explosión, el agujero negro,
        # o el golpe de otro enemigo lanzado). Solo así sus choques con otros enemigos y con el
        # suelo hacen daño; su propio salto, su caminata o su entrada al aparecer no.
        self._lanzado = False
        self._calma = 0.0
        self.atraida = False    # un agujero negro la está atrayendo
        self.con_recompensa = True  # False si murió "sola" (ej: explosivo contra un muro)
        self.destello = 0.0         # segundos que queda blanco tras un golpe
        self.quieto = False         # nivel de prueba: "enemigos quietos"
        self.invulnerable = 0.0     # segundos sin daño por choques tras recibir un golpe

        # El cuerpo físico RUEDA al caminar (como en Slammings); el dibujo queda derecho
        body = pymunk.Body(datos["masa"], pymunk.moment_for_circle(datos["masa"], 0, self.radio))
        shape = pymunk.Circle(body, self.radio)
        shape.friction = 0.8
        shape.elasticity = 0.2
        shape.collision_type = C.TIPO_ENEMIGO

        imagen = crear_imagen_enemigo(self.radio, datos["color"])
        # Silueta blanca para el destello (misma forma, todo blanco)
        self.imagen_blanca = imagen.copy()
        self.imagen_blanca.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
        if y is None:
            y = terreno.superficie(x) - self.radio - 1
        super().__init__(x, y, imagen, space, body, shape)

    # ---------- Estado ----------
    @property
    def agarrable(self):
        return True

    @property
    def lanzado(self):
        # Mientras lo tenés agarrado o lo atrae un agujero negro, también cuenta (lo estás moviendo vos)
        return self._lanzado or self.agarrada or self.atraida

    def marcar_lanzado(self):
        self._lanzado = True
        self._calma = 0.0

    def al_ser_soltada(self):
        """Lo soltó la mano: aunque lo sueltes quieto desde arriba, la caída cuenta como tuya."""
        self.marcar_lanzado()

    @property
    def viva(self):
        return self.vida > 0

    def en_suelo(self):
        """True si está apoyado en algo (suelo, barril, bloque u otro enemigo)."""
        return self.pisando

    # ---------- Daño ----------
    def _limitar_pesado(self, cantidad, maximo):
        """Enemigos pesados: ningún golpe les saca más que una parte de su máximo."""
        if self.pesado:
            return min(cantidad, maximo * C.DANIO_MAXIMO_PESADO)
        return cantidad

    def recibir_danio(self, cantidad):
        cantidad = self._limitar_pesado(cantidad, self.vida_max)
        self.vida -= cantidad
        self.aturdida = 0.6
        self._destellar(cantidad)

    def _destellar(self, cantidad):
        if cantidad >= C.DESTELLO_DANIO_MIN:
            self.destello = C.DESTELLO_DURACION

    def recibir_impacto(self, impulso, otro=None):
        """Choques: el daño depende del cambio de velocidad (las livianas sufren más)."""
        delta_v = impulso / self.body.mass
        self._danio_por_choque((delta_v - C.UMBRAL_IMPACTO) * C.FACTOR_DANIO, self.recibir_danio)

    def _danio_por_choque(self, danio, aplicar):
        """Filtro común a todos los choques: daño mínimo e invulnerabilidad breve."""
        if danio < C.DANIO_MINIMO or self.invulnerable > 0:
            return
        aplicar(danio)
        self.invulnerable = C.INVULNERABLE_CHOQUE

    def paralizar(self, segundos):
        self.paralizada = max(self.paralizada, segundos)

    def apply_impulse(self, impulso):
        """Empujones de poderes/explosiones: la deja aturdida para que no
        'frene en seco' al seguir caminando, y cuenta como lanzada."""
        super().apply_impulse(impulso)
        self.aturdida = max(self.aturdida, 0.8)
        self.marcar_lanzado()

    # ---------- Ganchos (las subclases los cambian) ----------
    def al_tocar_bloques(self, bloques, dt):
        """Por defecto: ataca el primer bloque que toca (y sigue empujando con su fuerza)."""
        bloques[0].recibir_danio(self.ataque * dt)

    def al_morir(self, escena):
        pass

    def al_llegar_a_base(self, escena):
        pass

    # ---------- Movimiento ----------
    def leer_contactos(self):
        """
        Clasifica los contactos según DÓNDE tocan al enemigo (como en Slammings):
          - abajo: lo que pisa (suelo, barril, bloque u otro enemigo) -> puede caminar
          - arriba: algo encima
          - adelante (hacia la base): algo que lo bloquea -> puede saltar
        También devuelve los bloques del muro que está tocando.
        """
        self.pisando = False
        self.normal_piso = None
        self.sobre_enemigo = False
        self.algo_encima = False
        self.bloqueado = False
        bloques = []
        centro = self.body.position
        punto_mas_bajo = [None]

        def revisar(arbitro):
            otro = None
            for forma in arbitro.shapes:
                if forma.body is not self.body:
                    otro = forma
            if otro is None or otro.sensor:
                return
            obj = getattr(otro, "parent", None)
            if isinstance(obj, Bloque) and obj not in bloques:
                bloques.append(obj)
            for punto in arbitro.contact_point_set.points:
                p = punto.point_a if arbitro.shapes[0].body is self.body else punto.point_b
                angulo = math.atan2(p.y - centro.y, p.x - centro.x)   # y crece hacia abajo
                if 0.2 * math.pi < angulo < 0.8 * math.pi:            # abajo
                    self.pisando = True
                    if punto_mas_bajo[0] is None or p.y > punto_mas_bajo[0]:
                        punto_mas_bajo[0] = p.y
                        n = arbitro.normal
                        if n.y > 0:
                            n = -n                                     # que apunte hacia arriba
                        self.normal_piso = n
                        self.sobre_enemigo = getattr(obj, "es_enemigo", False)
                elif -0.8 * math.pi < angulo < -0.2 * math.pi:        # arriba
                    self.algo_encima = True
                elif abs(angulo) > 0.8 * math.pi:                     # adelante (izquierda)
                    self.bloqueado = True

        self.body.each_arbiter(revisar)
        return bloques

    def update(self, dt=1 / C.FPS):
        if self.destello > 0:
            self.destello -= dt
        if self.invulnerable > 0:
            self.invulnerable -= dt
        bloques = self.leer_contactos()
        if self.pisando and not self.salto_reciente:
            self.saltando = False
        self.salto_reciente = False
        # Deja de contar como lanzado cuando ya está apoyado y tranquilo un ratito
        if self._lanzado and not self.agarrada:
            tranquilo = self.pisando and self.body.velocity.length <= max(self.vel * 1.5, 120)
            self._calma = self._calma + dt if tranquilo else 0.0
            if self._calma >= C.CALMA_LANZADO:
                self._lanzado = False

        if self.paralizada > 0:
            self.paralizada -= dt
        elif self.aturdida > 0:
            self.aturdida -= dt
        elif self.agarrada:
            pass   # agarrado no camina (los pesados "siguen caminando" desde la Mano)
        elif self.pisando:
            if bloques:
                self.al_tocar_bloques(bloques, dt)   # atacar el muro (o lo que haga cada tipo)
            if self._lanzado:
                # Recién lanzado y tocando algo: rueda/se desliza y se va frenando solo,
                # sin caminar (si caminara, su velocidad máxima lo frenaría en seco)
                frenado = max(0.0, 1 - C.FRENADO_LANZADO * dt)
                self.body.velocity = self.body.velocity * frenado
                self.body.angular_velocity *= frenado
            else:
                self._caminar(dt)
        elif self.saltando and self.body.velocity.y < 0:
            # Mientras sube en un salto, un empujoncito hacia adelante para pasar por encima
            self.body.apply_force_at_world_point((-C.SALTO_EMPUJE * self.body.mass, 0),
                                                 self.body.position)
        super().update()

    def _caminar(self, dt):
        """Camina con una FUERZA limitada a lo largo de lo que pisa, con velocidad máxima.
        Así empuja según su peso, se amontona con otros y sube/baja pendientes de forma natural."""
        if not self.viva:
            return
        n = self.normal_piso or pymunk.Vec2d(0, -1)
        direccion = pymunk.Vec2d(n.y, -n.x)          # tangente hacia la izquierda (hacia la base)
        self.body.apply_force_at_world_point(direccion * C.CAMINAR_FUERZA * self.body.mass,
                                             self.body.position)
        maxima = self.vel * (0.4 if self.atraida else 1.0)
        if self.quieto:
            maxima = 0
        v = self.body.velocity
        if v.length > maxima:
            self.body.velocity = v.scale_to_length(maxima) if maxima > 0 else pymunk.Vec2d(0, 0)
        # Bloqueado y sin nada encima: a veces salta para pasar el obstáculo
        # (parado arriba de otro enemigo no salta: así no arman "escaleras" tan fácil)
        if (self.bloqueado and not self.algo_encima and not self.saltando and not self.sobre_enemigo
                and not self.quieto and random.random() < C.SALTO_PROBABILIDAD):
            self.body.velocity = self.body.velocity + n * C.SALTO_VELOCIDAD
            self.saltando = True
            self.salto_reciente = True

    # ---------- Dibujo ----------
    def _dibujar_barra(self, surface, valor, maximo, color, desplazamiento):
        r = self.radio
        x, y = self.rect.centerx, self.rect.centery
        y_barra = y - r - 10 - desplazamiento
        pygame.draw.rect(surface, (60, 60, 60), (x - r, y_barra, r * 2, 5))
        pygame.draw.rect(surface, color, (x - r, y_barra, int(r * 2 * max(0, valor) / maximo), 5))

    def draw(self, surface):
        if self.destello > 0:
            if self.estela:
                self.dibujar_estela(surface)
            surface.blit(self.imagen_blanca, self.imagen_blanca.get_rect(center=self.rect.center))
        else:
            super().draw(surface)
        self._dibujar_barra(surface, self.vida, self.vida_max, (50, 200, 70), 0)
        if self.paralizada > 0 and int(self.paralizada * 12) % 2 == 0:
            pygame.draw.circle(surface, (255, 240, 80), self.rect.center, self.radio + 3, 2)


class Comun(Enemigo):
    """Camina y ataca los muros. Viene en 3 tamaños (definidos en config)."""


class Corredor(Enemigo):
    """Rápido y débil. No ataca los muros: solo empuja (y salta si puede)."""

    def al_tocar_bloques(self, bloques, dt):
        pass


class Acorazado(Enemigo):
    """
    Con armadura: no se puede agarrar, el agujero negro no lo mueve y rompe al
    instante cada bloque que toca. El daño va primero a la armadura.
    Al romperse la armadura se comporta como un enemigo común.
    """

    def __init__(self, space, clave, x, y=None):
        super().__init__(space, clave, x, y)
        self.armadura_max = self.datos["armadura"]
        self.armadura = self.armadura_max
        self.armadura_recien_rota = False   # la escena lo usa para mostrar el mensaje

    @property
    def con_armadura(self):
        return self.armadura > 0

    @property
    def agarrable(self):
        return not self.con_armadura

    @property
    def inmune_agujero(self):
        return self.con_armadura

    def _danio_armadura(self, cantidad):
        cantidad = self._limitar_pesado(cantidad, self.armadura_max)
        self._destellar(cantidad)
        self.armadura -= cantidad
        if self.armadura <= 0:
            self.armadura = 0
            self.armadura_recien_rota = True

    def recibir_danio(self, cantidad):
        if self.con_armadura:
            self._danio_armadura(cantidad)   # lo que sobra no pasa a la vida
        else:
            super().recibir_danio(cantidad)

    def recibir_impacto(self, impulso, otro=None):
        if self.con_armadura:
            if not isinstance(otro, (Enemigo, Bomba)):
                return   # solo lo dañan los enemigos y bombas que le tirás (no el muro ni el suelo)
            # Se usa la fuerza total del choque: un enemigo grande lanzado daña mucho más
            umbral = self.datos["umbral_armadura"]
            self._danio_por_choque((impulso - umbral) * self.datos["factor_armadura"],
                                   self._danio_armadura)
        else:
            super().recibir_impacto(impulso, otro)

    def apply_impulse(self, impulso):
        if self.con_armadura:
            ObjetoFisico.apply_impulse(self, impulso)  # lo empuja, pero no lo aturde
            self.marcar_lanzado()
        else:
            super().apply_impulse(impulso)

    def al_tocar_bloques(self, bloques, dt):
        if self.con_armadura:
            for b in bloques:
                b.vida = 0          # los rompe al instante y sigue caminando
        else:
            super().al_tocar_bloques(bloques, dt)

    def draw(self, surface):
        super().draw(surface)
        if self.con_armadura:
            pygame.draw.circle(surface, (170, 170, 180), self.rect.center, self.radio + 2, 4)
            self._dibujar_barra(surface, self.armadura, self.armadura_max, (180, 180, 190), 7)


class Explosivo(Enemigo):
    """
    Al morir explota y daña todo alrededor (puede encadenar con otros explosivos).
    Si toca un muro explota contra él. Si llega a la base, explota y quita más vidas.
    """

    def al_tocar_bloques(self, bloques, dt):
        self.vida = 0
        self.con_recompensa = False   # explotó solo: no da puntos ni energía

    def al_morir(self, escena):
        d = self.datos
        escena.explosion(self.position, d["radio_explosion"], d["fuerza_explosion"],
                         d["danio_explosion"], excluir=self)

    def al_llegar_a_base(self, escena):
        escena.explosion(self.position, self.datos["radio_explosion"], 0, 0, excluir=self)

    def draw(self, surface):
        # Brillo rojo que late (se dibuja detrás del enemigo)
        pulso = (math.sin(pygame.time.get_ticks() / 150) + 1) / 2
        brillo = pygame.Surface((self.radio * 4, self.radio * 4), pygame.SRCALPHA)
        pygame.draw.circle(brillo, (255, 60, 20, int(40 + 70 * pulso)),
                           (self.radio * 2, self.radio * 2), int(self.radio * (1.3 + 0.3 * pulso)))
        surface.blit(brillo, brillo.get_rect(center=self.rect.center))
        super().draw(surface)


CLASES_ENEMIGO = {
    "comun_chico": Comun, "comun_mediano": Comun, "comun_grande": Comun,
    "corredor": Corredor, "acorazado": Acorazado, "explosivo": Explosivo,
}


def crear_enemigo(space, clave, x, y=None):
    return CLASES_ENEMIGO[clave](space, clave, x, y)
