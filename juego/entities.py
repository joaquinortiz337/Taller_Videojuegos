# juego/entities.py
# Enemigos: una clase base con todo lo común y una subclase por tipo.
import math
import random
import pygame
import pymunk

from juego.objeto_fisico import ObjetoFisico  # Hereda del GameObject del motor
from juego import config as C
from juego.bloques import Bloque
from juego.objetos import Bomba, Roca
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
    empuje_salto = True   # empujoncito hacia adelante mientras sube en un salto

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
        self.animado = 0.0          # segundos que le quedan acelerado por un animador
        self.suelo = "normal"       # tipo de suelo que está pisando (barro, hielo...)

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

    @property
    def vel_actual(self):
        """Su velocidad: más rápida si lo animó un animador; según el suelo (barro, hielo)."""
        suelo = C.SUELOS[self.suelo]["velocidad"] if self.pisando else 1.0
        return self.vel * (C.ANIMO_MULTIPLICADOR if self.animado > 0 else 1.0) * suelo

    @property
    def puede_actuar(self):
        """Para las habilidades (curar, animar): no si lo agarraste, lanzaste o paralizaste."""
        return self.viva and not self.agarrada and not self.lanzado and self.paralizada <= 0

    def curar(self, cantidad):
        self.vida = min(self.vida_max, self.vida + cantidad)

    def en_suelo(self):
        """True si está apoyado en algo (suelo, barril, bloque u otro enemigo)."""
        return self.pisando

    def toca_base(self):
        """Llegó a la base caminando (los voladores la tocan aunque estén en el aire)."""
        return self.position.x < C.BASE_X and self.en_suelo()

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

    def al_entrar(self):
        """Recién aparecido por el borde derecho (los voladores entran volando)."""
        pass

    def actuar(self, escena, dt):
        """Habilidades que necesitan a la escena (curar, animar, pisotón). La llama la escena."""
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
        self.suelo = "normal"
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
                        self.suelo = getattr(otro, "tipo_suelo", "normal")
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
        if self.animado > 0:
            self.animado -= dt
        bloques = self.leer_contactos()
        if self.pisando and not self.salto_reciente:
            self.saltando = False
        self.salto_reciente = False
        # Deja de contar como lanzado cuando ya está apoyado y tranquilo un ratito
        if self._lanzado and not self.agarrada:
            tranquilo = self.pisando and self.body.velocity.length <= max(self.vel_actual * 1.5, 120)
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
        elif self.saltando and self.empuje_salto and self.body.velocity.y < 0:
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
        maxima = self.vel_actual * (0.4 if self.atraida else 1.0)
        if self.body.velocity.length < maxima:       # ya va a su velocidad: no empuja más
            self.body.apply_force_at_world_point(direccion * C.CAMINAR_FUERZA * self.body.mass,
                                                 self.body.position)
        if self.quieto:
            maxima = 0
        v = self.body.velocity
        frenado = C.SUELOS[self.suelo]["frenado"]
        if v.length > maxima and frenado is not None and not self.quieto:
            # Suelo resbaloso: frena de a poco (patina)
            exceso = v.length - maxima
            self.body.velocity = v.scale_to_length(maxima + exceso * max(0.0, 1 - frenado * dt))
        elif v.length > maxima:
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

    def _dibujar_animado(self, surface):
        """Brillo naranja y rayitas de velocidad mientras está animado."""
        if self.animado <= 0:
            return
        cx, cy = self.rect.center
        r = self.radio
        pulso = (math.sin(pygame.time.get_ticks() / 80) + 1) / 2
        brillo = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(brillo, (255, 150, 30, int(50 + 50 * pulso)), (r * 2, r * 2), int(r * 1.35))
        surface.blit(brillo, brillo.get_rect(center=(cx, cy)))
        for k, dy in enumerate((-r * 0.5, 0, r * 0.5)):
            largo = r * (0.8 + 0.4 * ((k + int(pulso * 3)) % 2))
            x0 = cx + r + 4
            pygame.draw.line(surface, (255, 170, 60), (x0, cy + dy), (x0 + largo, cy + dy), 2)

    def draw(self, surface):
        self._dibujar_animado(surface)
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
            if not isinstance(otro, (Enemigo, Bomba, Roca)):
                return   # solo lo dañan enemigos, bombas y rocas que le tirás (no el muro ni el suelo)
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


def _velocidad_con_gravedad_propia(body, gravedad, amortiguacion, dt):
    """Pymunk llama a esto para actualizar la velocidad: aplica solo una parte de la gravedad."""
    pymunk.Body.update_velocity(body, gravedad * body.escala_gravedad, amortiguacion, dt)


class Volador(Enemigo):
    """
    Vuela hacia la base a una altura fija sobre el terreno (el muro no lo frena).
    Estados:
      volando:    controla su vuelo, sin gravedad
      planeando:  lo soltaste o empujaste flojo: casi sin gravedad, el aire lo frena y
                  vuelve a volar enseguida; sus choques hacen menos daño
      derribado:  lo soltaste o empujaste fuerte, lo paralizó el rayo o lo atrapó el agujero:
                  cae con gravedad normal y, tirado en el suelo un rato, vuelve a volar
    """

    def __init__(self, space, clave, x, y=None):
        super().__init__(space, clave, x, y)
        self.estado = "volando"
        self.altura = random.uniform(*C.VOLADOR_ALTURA)
        self.fase = random.uniform(0, 2 * math.pi)
        self.tiempo = 0.0
        self.tiempo_planeo = 0.0
        self.tiempo_en_suelo = 0.0
        self.y_objetivo = self._altura_deseada()
        self.body.escala_gravedad = 0.0
        self.body.velocity_func = _velocidad_con_gravedad_propia

    # ---------- Estados ----------
    def _altura_deseada(self):
        """Altura de vuelo: mira también un poco adelante para subir antes de las colinas."""
        x = self.position.x
        suelo = min(terreno.superficie(x), terreno.superficie(x - 100))
        return suelo - self.radio - self.altura

    def derribar(self):
        self.estado = "derribado"
        self.tiempo_en_suelo = 0.0
        self.marcar_lanzado()

    def planear(self):
        if self.estado == "derribado":
            return   # si ya estaba cayendo, un empujón flojo no lo hace volar de nuevo
        self.estado = "planeando"
        self.tiempo_planeo = C.VOLADOR_PLANEO_DURACION
        self.marcar_lanzado()

    def _segun_velocidad(self, velocidad):
        """Fuerte = derribado; flojo = planea."""
        if velocidad >= C.VOLADOR_VEL_DERRIBO:
            self.derribar()
        else:
            self.planear()

    def _volver_a_volar(self):
        self.estado = "volando"
        self._lanzado = False
        self.tiempo_en_suelo = 0.0
        self.y_objetivo = min(self.y_objetivo, self.position.y)

    def toca_base(self):
        return self.position.x < C.BASE_X

    def al_entrar(self):
        """Entra volando a su altura, sin caer."""
        self.body.position = (self.position.x, self._altura_deseada())
        self.body.velocity = (-self.vel, 0)
        self.invulnerable = 0.0
        self._volver_a_volar()
        self.y_objetivo = self._altura_deseada()

    # ---------- Eventos ----------
    def al_ser_soltada(self):
        # Mano.soltar recorta la velocidad DESPUÉS de llamar a esto: se calcula igual acá
        velocidad = min(self.body.velocity.length, self.datos["lanzamiento"])
        self._segun_velocidad(velocidad)

    def apply_impulse(self, impulso):
        """Explosiones: según con qué velocidad lo dejan, cae derribado o planea."""
        super().apply_impulse(impulso)
        self._segun_velocidad(self.body.velocity.length)

    def paralizar(self, segundos):
        """Paralizado no puede aletear: se cae."""
        super().paralizar(segundos)
        self.derribar()

    def recibir_impacto(self, impulso, otro=None):
        delta_v = impulso / self.body.mass
        if self.estado == "volando" and delta_v >= C.VOLADOR_VEL_DERRIBO:
            self.derribar()   # le pegaste en el aire con algo lanzado fuerte
        if self.estado == "planeando":
            impulso *= C.VOLADOR_PLANEO_DANIO
        super().recibir_impacto(impulso, otro)

    def al_tocar_bloques(self, bloques, dt):
        pass   # no ataca los muros: los pasa por arriba

    # ---------- Movimiento ----------
    def update(self, dt=1 / C.FPS):
        self.tiempo += dt
        if self.destello > 0:
            self.destello -= dt
        if self.invulnerable > 0:
            self.invulnerable -= dt
        if self.paralizada > 0:
            self.paralizada -= dt
        if self.animado > 0:
            self.animado -= dt
        self.aturdida = 0.0
        self.leer_contactos()
        if self.atraida and self.estado != "derribado":
            self.derribar()   # el agujero negro lo arrastra: cuando termina, cae

        if self.agarrada:
            self.body.escala_gravedad = C.VOLADOR_PLANEO_GRAVEDAD
            self.tiempo_en_suelo = 0.0
        elif self.estado == "volando":
            self.body.escala_gravedad = 0.0
            self._volar(dt)
        elif self.estado == "planeando":
            self.body.escala_gravedad = C.VOLADOR_PLANEO_GRAVEDAD
            frenado = max(0.0, 1 - C.VOLADOR_PLANEO_FRENADO * dt)
            self.body.velocity = self.body.velocity * frenado
            self.body.angular_velocity *= frenado
            self.tiempo_planeo -= dt
            if self.tiempo_planeo <= 0 and self.viva:
                self._volver_a_volar()
        else:   # derribado
            self.body.escala_gravedad = 1.0
            if self.pisando:
                frenado = max(0.0, 1 - C.FRENADO_LANZADO * dt)
                self.body.velocity = self.body.velocity * frenado
                self.body.angular_velocity *= frenado
                if self.paralizada <= 0 and not self.atraida:
                    self.tiempo_en_suelo += dt
                if self.tiempo_en_suelo >= C.VOLADOR_TIEMPO_EN_SUELO and self.viva and not self.quieto:
                    # Saltito y vuelve a volar
                    self.body.velocity = (self.body.velocity.x, -C.VOLADOR_DESPEGUE)
                    self._volver_a_volar()
        ObjetoFisico.update(self)

    def _volar(self, dt):
        """Lleva su velocidad hacia la deseada con una aceleración limitada (se puede empujar)."""
        objetivo = self._altura_deseada()
        self.y_objetivo += (objetivo - self.y_objetivo) * min(1.0, 3 * dt)
        amplitud, rapidez = C.VOLADOR_ONDULACION
        y = self.y_objetivo + amplitud * math.sin(self.tiempo * rapidez + self.fase)
        vx = 0.0 if self.quieto else -self.vel_actual
        vy = max(-250.0, min(250.0, (y - self.position.y) * 3))
        cambio = pymunk.Vec2d(vx, vy) - self.body.velocity
        maximo = C.VOLADOR_ACELERACION * dt
        if cambio.length > maximo:
            cambio = cambio.scale_to_length(maximo)
        self.body.velocity = self.body.velocity + cambio
        self.body.angular_velocity *= 0.9

    # ---------- Dibujo ----------
    def _dibujar_alas(self, surface):
        cx, cy = self.rect.center
        r = self.radio
        if self.agarrada:
            alto, color = math.sin(self.tiempo * 30) * r * 0.7, (235, 235, 245)   # aletea desesperado
        elif self.estado == "volando":
            alto, color = math.sin(self.tiempo * 14 + self.fase) * r * 0.6, (235, 235, 245)
        elif self.estado == "planeando":
            alto, color = -r * 0.1, (235, 235, 245)                              # alas extendidas
        else:
            alto, color = r * 0.7, (170, 170, 180)                               # alas caídas
        for lado in (-1, 1):
            hombro = (cx + lado * r * 0.4, cy - r * 0.35)
            punta = (cx + lado * r * 1.7, cy - r * 0.4 - alto)
            borde = (cx + lado * r * 1.1, cy + r * 0.15 - alto * 0.4)
            pygame.draw.polygon(surface, color, (hombro, punta, borde))
            pygame.draw.polygon(surface, (60, 60, 70), (hombro, punta, borde), 1)

    def draw(self, surface):
        self._dibujar_alas(surface)
        super().draw(surface)


class Saltarin(Enemigo):
    """No camina: avanza a saltos y puede pasar por encima del muro.
    Entre salto y salto se queda quieto en el piso (ahí conviene agarrarlo)."""
    empuje_salto = False

    def __init__(self, space, clave, x, y=None):
        super().__init__(space, clave, x, y)
        self.espera_salto = random.uniform(*self.datos["espera"])

    @property
    def preparando(self):
        """Se agacha justo antes de saltar (aviso visual)."""
        return self.pisando and not self.lanzado and not self.quieto and self.espera_salto < 0.25

    def al_tocar_bloques(self, bloques, dt):
        pass   # no ataca los muros: los salta

    def _caminar(self, dt):
        if not self.viva:
            return
        frenado = max(0.0, 1 - 6 * dt)   # quieto en el piso
        self.body.velocity = self.body.velocity * frenado
        self.body.angular_velocity *= frenado
        if self.quieto or self.saltando:
            return
        self.espera_salto -= dt * (C.ANIMO_MULTIPLICADOR if self.animado > 0 else 1.0)
        if self.espera_salto <= 0:
            alto, vx = self.datos["salto_alto"], self.vel_actual
            if self.bloqueado:          # algo adelante: salto más alto y más corto
                alto, vx = alto * 1.2, vx * 0.6
            self.body.velocity = (-vx, -math.sqrt(2 * C.GRAVEDAD * alto))
            self.saltando = True
            self.salto_reciente = True
            self.espera_salto = random.uniform(*self.datos["espera"])

    def draw(self, surface):
        if self.preparando and self.destello <= 0:
            base = self.frames[0]
            w, h = base.get_size()
            agachado = pygame.transform.smoothscale(base, (int(w * 1.2), int(h * 0.75)))
            surface.blit(agachado, agachado.get_rect(midbottom=self.rect.midbottom))
            self._dibujar_barra(surface, self.vida, self.vida_max, (50, 200, 70), 0)
        else:
            super().draw(surface)


class Divisor(Enemigo):
    """Al morir se parte en dos enemigos más chicos que salen disparados hacia los costados."""

    def al_morir(self, escena):
        if not self.con_recompensa:
            return
        d = self.datos
        radio_hijo = C.ENEMIGOS[d["hijo"]]["radio"]
        vx, vy = d["velocidad_hijos"]
        for lado in (-1, 1):
            x = self.position.x + lado * (radio_hijo + 1)
            y = min(self.position.y, terreno.superficie(x) - radio_hijo - 1)
            velocidad = self.body.velocity * 0.5 + pymunk.Vec2d(lado * vx, -vy)
            hijo = escena.agregar_enemigo(d["hijo"], x, y, velocidad, d["invulnerable_hijos"])
            hijo.marcar_lanzado()   # salen rodando y se frenan solos

    def draw(self, surface):
        super().draw(surface)
        # Grieta en el medio: avisa que se va a partir
        cx, cy = self.rect.center
        r = self.radio
        puntos = [(cx, cy - r + 2), (cx - 3, cy - r // 3), (cx + 3, cy + r // 3), (cx, cy + r - 2)]
        pygame.draw.lines(surface, (30, 10, 40), False, puntos, 2)


class Chaman(Enemigo):
    """Cada tanto cura a los enemigos heridos que tiene cerca (nunca a sí mismo).
    No ataca los muros. Agarrado, lanzado o paralizado no cura."""

    def __init__(self, space, clave, x, y=None):
        super().__init__(space, clave, x, y)
        self.espera = self.datos["intervalo"] * random.uniform(0.5, 1.0)

    def al_tocar_bloques(self, bloques, dt):
        pass

    def actuar(self, escena, dt):
        self.espera -= dt
        if self.espera > 0 or not self.puede_actuar:
            return
        d = self.datos
        heridos = [c for c in escena.enemigos if c is not self and c.viva and c.vida < c.vida_max
                   and (c.position - self.position).length <= d["radio_cura"]]
        if not heridos:
            self.espera = 0.5        # nadie para curar: vuelve a mirar en un rato
            return
        for c in heridos:
            c.curar(c.vida_max * d["cura"])
        escena.efecto_cura(self, heridos)
        self.espera = d["intervalo"]

    def draw(self, surface):
        super().draw(surface)
        # Aureola verde arriba de la cabeza
        cx, cy = self.rect.center
        r = self.radio
        pygame.draw.ellipse(surface, (120, 255, 150), (cx - r * 0.7, cy - r - 9, r * 1.4, 7), 2)


class Animador(Enemigo):
    """Cada tanto acelera a los enemigos cercanos por unos segundos (no se acumula).
    Agarrado, lanzado o paralizado no anima."""

    def __init__(self, space, clave, x, y=None):
        super().__init__(space, clave, x, y)
        self.espera = self.datos["intervalo"] * random.uniform(0.5, 1.0)

    def actuar(self, escena, dt):
        self.espera -= dt
        if self.espera > 0 or not self.puede_actuar:
            return
        d = self.datos
        cercanos = [c for c in escena.enemigos if c is not self and c.viva
                    and (c.position - self.position).length <= d["radio_animo"]]
        if not cercanos:
            self.espera = 0.5
            return
        for c in cercanos:
            c.animado = d["duracion_animo"]   # si ya estaba animado, solo se renueva
        escena.efecto_animar(self, cercanos)
        self.espera = d["intervalo"]

    def draw(self, surface):
        super().draw(surface)
        # Banderita arriba
        cx, cy = self.rect.center
        r = self.radio
        palo = (cx + r * 0.3, cy - r)
        punta = (palo[0], palo[1] - 16)
        pygame.draw.line(surface, (60, 40, 20), palo, punta, 2)
        pygame.draw.polygon(surface, (255, 220, 60), (punta, (punta[0] + 12, punta[1] + 4), (punta[0], punta[1] + 8)))


class Jefe(Enemigo):
    """
    Pesado y con mucha vida. Cada tanto da un salto corto y al caer pisotea:
    la escena suelta una onda que daña y empuja los muros, empuja los barriles y
    levanta a los demás enemigos sin dañarlos. Agarrado o paralizado no pisotea.
    """
    es_jefe = True   # la escena muestra el aviso al entrar y su barra de vida arriba

    def __init__(self, space, clave, x, y=None):
        super().__init__(space, clave, x, y)
        self.espera_pisoton = self.datos["intervalo_pisoton"]
        self.en_pisoton = False      # saltó para pisotear y todavía no cayó
        self.despego = False         # ya se separó del suelo en este salto
        self.pisoton_listo = False   # cayó: la escena tiene que hacer la onda

    def _caminar(self, dt):
        super()._caminar(dt)
        if self.quieto or self.saltando or self.en_pisoton:
            return
        self.espera_pisoton -= dt
        if self.espera_pisoton <= 0:
            alto = self.datos["salto_pisoton"]
            self.body.velocity = (self.body.velocity.x * 0.3, -math.sqrt(2 * C.GRAVEDAD * alto))
            self.saltando = True
            self.salto_reciente = True
            self.en_pisoton = True
            self.despego = False
            self.espera_pisoton = self.datos["intervalo_pisoton"]

    def update(self, dt=1 / C.FPS):
        super().update(dt)
        if self.agarrada or self._lanzado or self.paralizada > 0:
            self.en_pisoton = False      # lo interrumpiste: no hay pisotón
        elif self.en_pisoton:
            if not self.pisando:
                self.despego = True
            elif self.despego:
                self.en_pisoton = False
                self.pisoton_listo = True

    def actuar(self, escena, dt):
        if self.pisoton_listo:
            self.pisoton_listo = False
            if self.viva:
                escena.pisoton(self)

    def draw(self, surface):
        super().draw(surface)
        # Corona
        cx, cy = self.rect.center
        r = self.radio
        base_y = cy - r + 14          # apoyada en la cabeza, debajo de la barra de vida
        x0, x1 = cx - r * 0.5, cx + r * 0.5
        puntos = [(x0, base_y), (x0, base_y - 14), (cx - r * 0.25, base_y - 6), (cx, base_y - 18),
                  (cx + r * 0.25, base_y - 6), (x1, base_y - 14), (x1, base_y)]
        pygame.draw.polygon(surface, (250, 200, 50), puntos)
        pygame.draw.polygon(surface, (120, 80, 10), puntos, 2)


CLASES_ENEMIGO = {
    "comun_chico": Comun, "comun_mediano": Comun, "comun_grande": Comun,
    "corredor": Corredor, "acorazado": Acorazado, "explosivo": Explosivo,
    "volador_chico": Volador, "volador_mediano": Volador, "corredor_volador": Volador,
    "saltarin": Saltarin, "divisor": Divisor,
    "chaman": Chaman, "animador": Animador, "jefe": Jefe,
}


def crear_enemigo(space, clave, x, y=None):
    return CLASES_ENEMIGO[clave](space, clave, x, y)
