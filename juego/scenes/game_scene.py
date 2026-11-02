# juego/scenes/game_scene.py
import math
import random
import pygame
import pymunk
import pymunk.pygame_util

from engine.ui import Scene                  # Hereda del motor
from engine.dialogue_manager import DialogueManager  # Usa el motor
from engine.particle import ParticleSystem   # Usa el motor
from engine.cursor import Cursor             # Usa el motor
from engine.ui_elements import Panel  # Usa el motor
from juego.entities import Enemigo, Acorazado, crear_enemigo
from juego.poderes import crear_poderes
from juego.mano import Mano
from juego.objetos import Bomba, Barril, Roca, Cristal
from juego.director import Director
from juego.narrador import Narrador, evento_combo
from juego.base import Base
from juego.niveles import NIVELES_POR_ID
from juego.efectos import EfectoOnda, EfectoCruz, TextoFlotante, aplicar_explosion, Temblor, TextoCombo
from juego.ui_extra import SoundButton
from juego.camara import CamaraManual
from juego.fondo import Fondo
from juego import terreno
from juego.terreno import Terreno
from juego.scenes.controles_scene import dibujar_controles
from juego.panel_prueba import PanelPrueba
from juego import cursores
from juego import hud
from juego import config as C
from juego import estilo as E


class GameScene(Scene):
    def __init__(self, game, id_nivel="nivel1", dificultad="normal"):
        super().__init__(game)
        self.nivel = NIVELES_POR_ID[id_nivel]
        self.dificultad = dificultad
        self.director = Director(self.nivel, dificultad)
        self.ancho_mundo = self.nivel.get("ancho", C.ANCHO_MUNDO)
        self.terreno = Terreno(self.nivel.get("terreno"), self.ancho_mundo, self.nivel.get("suelos"))
        terreno.ACTUAL = self.terreno   # para que enemigos, muros y barriles conozcan el suelo
        self.camara = CamaraManual(C.ANCHO, C.ALTO, self.ancho_mundo, C.ALTO)
        self.arrastre = None          # arrastre de cámara con clic derecho
        self.dt = 1 / C.FPS
        self.fuente = pygame.font.Font(None, 32)
        self.fuente_chica = pygame.font.Font(None, 24)
        self.mensajes = DialogueManager(self.game.screen, font_size=48, color=(255, 255, 255))
        self.ver_fisica = False

        # --- Mundo físico ---
        self.space = pymunk.Space()
        self.space.gravity = (0, C.GRAVEDAD)
        self.dibujo_debug = pymunk.pygame_util.DrawOptions(self.game.screen)
        self._crear_escenario()
        # Un solo callback para todos los choques: cada objeto decide cómo le afecta
        self.space.on_collision(None, None, begin=self._al_empezar_choque, post_solve=self._al_chocar)
        self._velocidad_choque = {}   # velocidad con la que se acercaban al empezar cada contacto

        # --- Entidades ---
        self.enemigos = pygame.sprite.Group()
        self.bloques = pygame.sprite.Group()
        self.efectos = pygame.sprite.Group()
        self.bombas = pygame.sprite.Group()
        self.agujeros = pygame.sprite.Group()
        self.barriles = pygame.sprite.Group()
        for x in self.nivel["barriles"]:
            self.barriles.add(Barril(self.space, x))
        self.rocas = pygame.sprite.Group()
        for x in self.nivel.get("rocas", []):
            self.rocas.add(Roca(self.space, x))
        self.cristales = pygame.sprite.Group()
        for x in self.nivel.get("cristales", []):
            self.cristales.add(Cristal(self.space, x))

        # --- Mano, energía y poderes ---
        self.mano = Mano(self)
        self.energia = C.ENERGIA_INICIAL
        self.poderes = crear_poderes(self, self.game.progreso.niveles_poderes())
        self.poder_actual = None   # None = sin poder seleccionado (el clic agarra)

        # --- Estado de la partida ---
        self.puntos = 0
        self.vidas_max = self.game.progreso.vidas_base()   # 5, 6 o 7 según la mejora "Base"
        self.vidas_base = self.vidas_max
        self.combo = 0
        self.tiempo_combo = 0.0

        # --- Detalles visuales ---
        # Todo el mundo se dibuja en esta capa (del ancho del nivel); después se recorta
        # la parte que ve la cámara y se sacude si hace falta.
        self.capa_mundo = pygame.Surface((self.ancho_mundo, C.ALTO), pygame.SRCALPHA)
        # Semilla distinta por nivel: cada uno tiene sus propias colinas, montañas y árboles
        self.fondo = Fondo(self.nivel.get("fondo", "pradera"), semilla=sum(map(ord, self.nivel["id"])) * 7)
        self.base = Base(self.terreno, self.game.progreso.nivel_poder("base"), self.vidas_max,
                         self.fondo.color_suelo)
        self.camara_x_anterior = self.camara.x
        self.dibujo_debug = pymunk.pygame_util.DrawOptions(self.capa_mundo)
        self.temblor = Temblor(C.TEMBLOR_AMORTIGUACION)
        self.particulas = ParticleSystem()
        self.textos_combo = []
        self.flash_base = 0.0        # segundos que la base parpadea en rojo
        self.congelado = 0           # cuadros que quedan de congelado de impacto
        self.espera_congelado = 0.0  # para que no se repita muy seguido
        self.alerta_base = False     # hay un enemigo en la zona de peligro
        self.aviso_base_mostrado = False
        self.corazones_perdiendo = {}  # índice de corazón -> segundos de animación al perderlo
        self.bucles = {}             # objeto -> canal de su sonido en bucle (mecha, agujero)
        self.borde_rojo = 0.0        # intensidad del borde rojo de la pantalla
        self.camara_lenta = None     # segundos reales que quedan de cámara lenta final
        self.peligro = 0.0           # 0 a 1: maneja música, latido, borde rojo suave y "Quedan N"
        self.espera_latido = 0.0
        self.narrador = Narrador(self.game.audio)
        self.game.audio.agache_voz = C.NARRADOR_MUSICA
        self.dijo_inicio = False
        self.aviso_ultimos = False
        self.vineta = self._crear_vineta()
        self.cursor_mano = Cursor(normal=cursores.mano_abierta(), hover=cursores.mano_cerrada())
        self.cursores_poder = {p.clave: Cursor(normal=cursores.icono_poder(p.clave),
                                               hover=cursores.icono_poder(p.clave))
                               for p in self.poderes}

        # --- Pausa ---
        self.pausado = False
        self.panel_pausa = Panel((0, 0, C.ANCHO, C.ALTO), color=(0, 0, 0, 150))
        click = self.game.assets.sounds.get("click")
        cx = C.ANCHO // 2 - 140
        id_nivel = self.nivel["id"]
        self.botones_pausa = [
            SoundButton(cx, 215, 280, 56, "Continuar", self._reanudar, click),
            SoundButton(cx, 283, 280, 56, "Reiniciar",
                        lambda: self.game.change_scene("juego", id_nivel=id_nivel,
                                                       dificultad=self.dificultad), click),
            SoundButton(cx, 351, 280, 56, "Opciones", self._ver_opciones, click),
            SoundButton(cx, 419, 280, 56, "Controles", self._ver_controles, click),
            SoundButton(cx, 487, 280, 56, "Salir al nivel",
                        lambda: self.game.change_scene("nivel", id_nivel=id_nivel), click),
        ]
        self.viendo_controles = False
        self.boton_volver_controles = SoundButton(20, C.ALTO - 70, 160, 50, "Volver",
                                                  lambda: setattr(self, "viendo_controles", False), click)
        # Opciones dentro de la pausa: volumen de efectos, música y narrador
        self.viendo_opciones = False
        self.filas_volumen = [(230, "Efectos", "volumen_efectos"), (310, "Música", "volumen_musica"),
                              (390, "Narrador", "volumen_voz")]
        self.botones_opciones = [SoundButton(20, C.ALTO - 70, 160, 50, "Volver",
                                             lambda: setattr(self, "viendo_opciones", False), click)]
        for y, _, atributo in self.filas_volumen:
            self.botones_opciones.append(SoundButton(C.ANCHO // 2 - 220, y, 60, 50, "-",
                                                     lambda a=atributo: self._cambiar_volumen(a, -0.1), click))
            self.botones_opciones.append(SoundButton(C.ANCHO // 2 + 160, y, 60, 50, "+",
                                                     lambda a=atributo: self._cambiar_volumen(a, +0.1), click))

        # --- Nivel de prueba (solo desarrollo) ---
        self.es_prueba = bool(self.nivel.get("prueba"))
        self.enemigo_a_crear = None
        self.trucos = dict(energia_infinita=False, sin_recarga=False,
                           base_invencible=False, enemigos_quietos=False)
        self.panel_prueba = PanelPrueba(self) if self.es_prueba else None
        if self.es_prueba:
            # "Salir al nivel" no tiene sentido acá: vuelve a la selección de niveles
            salir = self.botones_pausa[-1]
            salir.text = "Salir"
            salir.callback = lambda: self.game.change_scene("niveles")
            self.mensajes.show_message("Nivel de prueba", 2, position="top")
        else:
            self.mensajes.show_message("¡Defendé la base!", 2, position="top")

    # ---------------- Nivel de prueba ----------------
    def prueba_elegir_enemigo(self, clave):
        self.enemigo_a_crear = None if self.enemigo_a_crear == clave else clave
        self.poder_actual = None

    def prueba_alternar(self, truco):
        self.trucos[truco] = not self.trucos[truco]

    def prueba_borrar_enemigos(self):
        for c in list(self.enemigos):
            self._eliminar(c)

    def prueba_reponer_barriles(self):
        for b in list(self.barriles):
            self._eliminar(b)
        for x in self.nivel["barriles"]:
            self.barriles.add(Barril(self.space, x))
        for r in list(self.rocas):
            self._eliminar(r)
        for x in self.nivel.get("rocas", []):
            self.rocas.add(Roca(self.space, x))

    def prueba_nivel_poder(self, poder, nivel):
        poder.nivel = nivel

    def _prueba_crear_enemigo(self, pos):
        x, y = pos
        radio = C.ENEMIGOS[self.enemigo_a_crear]["radio"]
        y = min(y, terreno.superficie(x) - radio - 1)   # nunca dentro del suelo
        self.enemigos.add(crear_enemigo(self.space, self.enemigo_a_crear, x, y))

    def on_enter(self):
        self.game.audio.musica("partida")

    def on_exit(self):
        pygame.mouse.set_visible(True)   # el cursor propio solo se usa durante la partida
        for canal in self.bucles.values():
            if canal:
                canal.stop()
        self.bucles.clear()

    # ---------------- Sonido ----------------
    def sonido(self, nombre, volumen=1.0):
        return self.game.audio.reproducir(nombre, volumen)

    def _actualizar_bucles(self):
        """Mecha de las bombas encendidas y zumbido de los agujeros negros."""
        activos = {b for b in self.bombas if b.encendida} | set(self.agujeros)
        for obj in activos:
            if obj not in self.bucles:
                nombre = "agujero" if obj in self.agujeros else "mecha"
                self.bucles[obj] = self.game.audio.reproducir(nombre, 0.8, bucle=True)
        for obj in list(self.bucles):
            if obj not in activos:
                canal = self.bucles.pop(obj)
                if canal:
                    canal.stop()

    # ---------------- Escenario ----------------
    def _crear_escenario(self):
        estatico = self.space.static_body
        self.terreno.crear_fisica(self.space)
        pared = pymunk.Segment(estatico, (self.ancho_mundo + 150, -400),
                               (self.ancho_mundo + 150, C.ALTO), C.GROSOR_SUELO)
        pared.friction = 1.0
        pared.elasticity = 0.3
        self.space.add(pared)

    # ---------------- Física ----------------
    def _al_empezar_choque(self, arbitro, space, data):
        """Primer instante de un contacto (antes de resolverlo): guarda a qué velocidad
        se acercaban los dos objetos. Apretar algo contra el suelo da casi 0; un golpe, mucho."""
        puntos = arbitro.contact_point_set.points
        if not puntos:
            return
        a, b = arbitro.bodies
        punto = puntos[0].point_a
        relativa = b.velocity_at_world_point(punto) - a.velocity_at_world_point(punto)
        self._velocidad_choque[arbitro.shapes] = abs(relativa.dot(arbitro.normal))

    def _efecto_suelo(self, arbitro, velocidad):
        """Algo cayó fuerte sobre barro (salpica) o hielo (chispitas)."""
        if velocidad < C.SUELO_VELOCIDAD_EFECTO:
            return
        tipo = next((getattr(f, "tipo_suelo", None) for f in arbitro.shapes
                     if getattr(f, "tipo_suelo", "normal") != "normal"), None)
        if tipo is None or not arbitro.contact_point_set.points:
            return
        p = arbitro.contact_point_set.points[0].point_a
        if tipo == "barro":
            self.particulas.emit(p.x, p.y, count=10, speed=(60, 200), color=(85, 60, 38),
                                 life=(0.3, 0.6), size=(3, 6), gravity=700, angle=-90, spread=70)
        else:
            self.particulas.emit(p.x, p.y, count=8, speed=(50, 160), color=(240, 250, 255),
                                 life=(0.2, 0.5), size=(2, 4), gravity=300, angle=-90, spread=80)

    def _al_chocar(self, arbitro, space, data):
        # Pymunk avisa en CADA cuadro mientras dos cosas se tocan. El daño (y los efectos)
        # solo cuentan en el primer cuadro del contacto: apoyar, arrastrar o apretar algo
        # contra el suelo no lastima; volver a estrellarlo sí (es un contacto nuevo).
        if not arbitro.is_first_contact:
            return
        velocidad = self._velocidad_choque.pop(arbitro.shapes, 0.0)
        if velocidad < C.VELOCIDAD_MINIMA_CHOQUE:
            return   # se tocaron despacio (apoyar, apretar, empujar): no es un golpe
        impulso = arbitro.total_impulse.length
        self._efecto_suelo(arbitro, velocidad)
        a, b = (getattr(forma, "parent", None) for forma in arbitro.shapes)
        if not self._choque_cuenta(a, b):
            return   # se movieron solos (saltar, entrar, amontonarse): no es un golpe tuyo

        # Si un enemigo lanzado golpea fuerte a otro, el golpeado también pasa a contar como
        # lanzado (así las reacciones en cadena siguen haciendo daño)
        enemigos = [o for o in (a, b) if getattr(o, "es_enemigo", False)]
        if len(enemigos) == 2 and max(impulso / e.body.mass for e in enemigos) > C.POLVO_DELTA_V:
            for e in enemigos:
                e.marcar_lanzado()

        for obj, otro in ((a, b), (b, a)):
            if obj is not None and hasattr(obj, "recibir_impacto"):
                golpe = impulso
                if isinstance(otro, Roca) and getattr(obj, "es_enemigo", False):
                    golpe *= C.ROCA["multiplicador_danio"]   # la roca es dura: pega más
                obj.recibir_impacto(golpe, otro)   # 'otro' = con qué chocó (None = suelo)
            # Barril que moviste vos (agarrado o lanzado) contra un enemigo, rápido: explota
            if (isinstance(obj, Barril) and obj.lanzado and getattr(otro, "es_enemigo", False)
                    and velocidad >= C.BARRIL["velocidad_explosion"]):
                obj.explotar = True
            # Enemigo estrellado contra un cristal cargado: daño extra y energía para vos
            if (isinstance(obj, Cristal) and obj.listo and getattr(otro, "es_enemigo", False)
                    and velocidad >= C.CRISTAL["velocidad_minima"]):
                self._activar_cristal(obj, otro)

        # Detalles visuales del choque
        if arbitro.contact_point_set.points:
            if enemigos:
                delta_v = max(impulso / e.body.mass for e in enemigos)
                if delta_v > C.POLVO_DELTA_V:
                    punto = arbitro.contact_point_set.points[0].point_a
                    fuerza = min(1.0, (delta_v - C.POLVO_DELTA_V) / 1200)
                    self.particulas.emit(punto.x, punto.y, count=int(6 + 14 * fuerza),
                                         speed=(40, 160), color=(150, 130, 100), life=(0.3, 0.7),
                                         size=(2, 5), gravity=200, angle=-90, spread=160)
                    self.temblor.agregar(C.TEMBLOR_GOLPE_MAX * fuerza)
                    self.sonido(random.choice(("golpe_1", "golpe_2", "golpe_3")), 0.4 + 0.6 * fuerza)
                if delta_v > C.CONGELADO_DELTA_V:
                    self.congelar()

    @staticmethod
    def _choque_cuenta(a, b):
        """
        ¿Este choque puede hacer daño? Solo se filtran dos casos en los que el enemigo
        se movió por su cuenta:
          - enemigo contra enemigo: hace falta que al menos uno esté lanzado;
          - enemigo contra el suelo: hace falta que el enemigo esté lanzado.
        Todo lo demás (muros, bombas, barriles, bloques que caen...) cuenta como siempre.
        """
        ea, eb = getattr(a, "es_enemigo", False), getattr(b, "es_enemigo", False)
        if ea and eb:
            return a.lanzado or b.lanzado
        if ea and b is None:
            return a.lanzado
        if eb and a is None:
            return b.lanzado
        return True

    def congelar(self):
        """Congelado de impacto: el mundo se detiene unos cuadros (como mucho cada tanto)."""
        if C.CONGELADO_FRAMES > 0 and self.espera_congelado <= 0:
            self.congelado = C.CONGELADO_FRAMES
            self.espera_congelado = C.CONGELADO_ESPERA

    def mouse_mundo(self):
        """Posición del mouse en coordenadas del mundo (la pantalla es solo una parte)."""
        return self.camara.a_mundo(pygame.mouse.get_pos())

    def _crear_enemigo(self, clave):
        """Entra por el borde derecho, lanzado y cayendo (como en Slammings)."""
        radio = C.ENEMIGOS[clave]["radio"]
        x = self.ancho_mundo - radio - 5
        y = terreno.superficie(x) - radio - random.uniform(*C.ENTRADA_ALTURA)
        e = crear_enemigo(self.space, clave, x, y)
        e.body.velocity = (-random.uniform(*C.ENTRADA_VELOCIDAD_X), random.uniform(*C.ENTRADA_VELOCIDAD_Y))
        e.invulnerable = C.ENTRADA_SIN_DANIO   # que la caída al entrar no lo lastime
        e.al_entrar()                          # los voladores entran volando
        self.enemigos.add(e)
        if getattr(e, "es_jefe", False):
            self.mensajes.show_message("¡Se acerca el jefe!", 2.5, position="top")
            self.sonido("alarma")
            self.narrador.decir("jefe")

    def agregar_enemigo(self, clave, x, y, velocidad, invulnerable=0.0):
        """Enemigo que aparece en medio del nivel (ej: los dos que salen del divisor)."""
        e = crear_enemigo(self.space, clave, x, y)
        e.body.velocity = velocidad
        e.invulnerable = invulnerable
        self.enemigos.add(e)
        return e

    def _eliminar(self, obj):
        if obj is self.mano.agarrada:
            self.mano.soltar()
        obj.remove_from_space()

    def explosion(self, centro, radio, fuerza, danio, excluir=None):
        """Explosión genérica (bombas, enemigo explosivo...): empuja, daña y se ve."""
        objetos = [o for o in list(self.enemigos) + list(self.bloques) + list(self.bombas)
                   + list(self.barriles) + list(self.rocas) if o is not excluir]
        aplicar_explosion(objetos, centro, radio, fuerza, danio)
        self.efectos.add(EfectoOnda(centro.x, centro.y, radio, (255, 150, 40)))
        # Chispas y humo (partículas del motor) + sacudida
        self.particulas.emit(centro.x, centro.y, count=30, speed=(120, 380), color=(255, 170, 50),
                             life=(0.2, 0.6), size=(2, 4), gravity=300)
        self.particulas.emit(centro.x, centro.y, count=14, speed=(20, 80), color=(110, 110, 110),
                             life=(0.6, 1.2), size=(5, 10), gravity=-60)
        self.temblor.agregar(C.TEMBLOR_EXPLOSION * (0.6 + 0.4 * min(1.0, radio / 150)))
        self.sonido("explosion", 0.6 + 0.4 * min(1.0, radio / 150))

    def _activar_cristal(self, cristal, enemigo):
        d = C.CRISTAL
        cristal.descargar()
        enemigo.recibir_danio(d["danio"])
        self.energia = min(C.ENERGIA_MAX, self.energia + d["energia"])
        p = cristal.position
        self.efectos.add(EfectoOnda(p.x, p.y, 90, (110, 225, 255), duracion=0.4))
        self.efectos.add(TextoFlotante(p.x, p.y - d["alto"] / 2 - 15, f"+{d['energia']}", (120, 230, 255)))
        self.particulas.emit(p.x, p.y - d["alto"] / 4, count=18, speed=(80, 260), color=(150, 235, 255),
                             life=(0.3, 0.7), size=(2, 4), gravity=250)
        self.sonido("cristal")

    def efecto_cura(self, chaman, curados):
        """El chamán curó: anillo verde que se expande + crucecitas sobre los curados."""
        p = chaman.position
        self.efectos.add(EfectoOnda(p.x, p.y, chaman.datos["radio_cura"], (80, 220, 110), duracion=0.5))
        for c in curados:
            self.efectos.add(EfectoCruz(c.position.x, c.position.y - c.radio - 8))
        self.sonido("curar", 0.6)

    def efecto_animar(self, animador, animados):
        p = animador.position
        self.efectos.add(EfectoOnda(p.x, p.y, animador.datos["radio_animo"], (255, 150, 40), duracion=0.5))
        self.sonido("animar", 0.6)

    def pisoton(self, jefe):
        """El jefe cayó de su salto: onda que daña y empuja muros y barriles, y levanta
        a los demás enemigos sin dañarlos (no cuentan como lanzados)."""
        d = jefe.datos
        centro = jefe.position
        radio = d["radio_pisoton"]
        fuerza = d["fuerza_pisoton"]

        def intensidad(obj):
            dx = obj.position.x - centro.x
            if abs(dx) >= radio or obj.position.y < centro.y - 200:
                return 0.0, 0
            return 1 - abs(dx) / radio, (1 if dx >= 0 else -1)

        for b in list(self.bloques):
            i, lado = intensidad(b)
            if i > 0:
                b.recibir_danio(d["danio_pisoton"] * i)
                b.apply_impulse(pymunk.Vec2d(lado * 0.6, -1) * fuerza * i)
        for obj in list(self.barriles) + list(self.rocas):
            i, lado = intensidad(obj)
            if i > 0:
                obj.apply_impulse(pymunk.Vec2d(lado * 0.5, -1) * fuerza * 0.5 * i)
        for c in self.enemigos:
            if c is jefe or not c.pisando:
                continue
            i, lado = intensidad(c)
            if i > 0:
                c.body.velocity = c.body.velocity + pymunk.Vec2d(lado * 150, -320) * i

        pie = (centro.x, centro.y + jefe.radio)
        self.efectos.add(EfectoOnda(pie[0], pie[1], radio, (150, 110, 70), duracion=0.4))
        for lado in (-1, 1):
            self.particulas.emit(pie[0] + lado * jefe.radio, pie[1], count=14, speed=(60, 220),
                                 color=(150, 130, 100), life=(0.4, 0.8), size=(3, 7), gravity=300,
                                 angle=-90 + lado * 50, spread=60)
        self.temblor.agregar(C.TEMBLOR_PISOTON)
        self.sonido("pisoton")

    def efecto_rayo(self, puntos):
        """Chispas en cada punto que tocó el rayo + sacudida (lo llama el poder Rayo)."""
        for x, y in puntos:
            self.particulas.emit(x, y, count=14, speed=(80, 260), color=(255, 240, 90),
                                 life=(0.2, 0.5), size=(1, 3), gravity=300)
        self.temblor.agregar(C.TEMBLOR_RAYO)
        self.sonido("rayo")

    def _explotar(self, bomba):
        self.explosion(bomba.position, bomba.radio_explosion, bomba.fuerza, bomba.danio, excluir=bomba)
        if bomba.racimo:
            # Nivel 3: suelta 3 bombas chicas que salen volando y explotan al segundo
            for vx in (-350, 0, 350):
                mini = Bomba(self.space, bomba.position.x, bomba.position.y - 10, 1.0,
                             bomba.radio_explosion * 0.6, bomba.fuerza * 0.6, bomba.danio * 0.6,
                             racimo=False, tam=8, encendida=True)
                mini.body.velocity = (vx, -550)
                self.bombas.add(mini)
        self._eliminar(bomba)

    def _enemigo_muerto(self, c):
        if c.con_recompensa:
            # Cada enemigo suma 'valor_combo' eslabones (los pesados valen más).
            # Energía: el primer eslabón da poco; cada eslabón siguiente da más que el anterior.
            energia = 0
            antes = self.combo
            for _ in range(c.valor_combo):
                self.combo += 1
                energia += C.ENERGIA_POR_ENEMIGO if self.combo == 1 else C.ENERGIA_POR_ESLABON * self.combo
            self.tiempo_combo = C.TIEMPO_COMBO
            self.puntos += c.puntos * self.combo
            self.energia = min(C.ENERGIA_MAX, self.energia + energia)
            if self.combo >= 2:
                self.textos_combo = [TextoCombo(self.combo, energia)]   # reemplaza al anterior
                self.sonido(f"combo_{min(self.combo, 6)}")
            evento = evento_combo(self.combo)
            if evento and self.combo > antes:
                self.narrador.decir(evento, retraso=C.NARRADOR_RETRASO_COMBO)
        if c.pesado:
            self.congelar()
        self.sonido("muerte", 0.7)
        # Nubecita del color del enemigo
        color = c.datos["color"]
        self.particulas.emit(c.position.x, c.position.y, count=12, speed=(40, 140), color=color,
                             life=(0.3, 0.6), size=(3, 6), gravity=150)
        self._eliminar(c)
        c.al_morir(self)   # ej: el explosivo explota (después de sacarlo del mundo)
        self.director.enemigo_eliminado(len(self.enemigos))   # puede entrar otro al instante

    # ---------------- Poderes ----------------
    def seleccionar_poder(self, indice):
        """Teclas 1-4. Apretar la misma tecla otra vez cancela la selección."""
        if not 0 <= indice < len(self.poderes):
            return
        poder = self.poderes[indice]
        self.poder_actual = None if poder is self.poder_actual else poder
        self.enemigo_a_crear = None

    def _clic_en_hud(self, pos):
        """Clics sobre la interfaz: casillas de poderes y minimapa. True si se usó."""
        for i, rect in enumerate(hud.rects_poderes(len(self.poderes))):
            if rect.collidepoint(pos):
                self.seleccionar_poder(i)
                sonido = self.game.assets.sounds.get("click")
                if sonido:
                    sonido.play()
                return True
        if hud.MINIMAPA.collidepoint(pos):
            prop = (pos[0] - hud.MINIMAPA.x) / hud.MINIMAPA.w
            self.camara.centrar_en(prop * self.ancho_mundo)
            return True
        return False

    def _clic(self, pos):
        poder = self.poder_actual
        if poder is None:
            self.mano.agarrar_en(pos)
            return
        if poder.usar(pos):
            self.poder_actual = None   # después de usarlo, volvés a la mano
            if poder.clave == "muro":
                self.sonido("muro")
        elif self.energia < poder.costo:
            self.mensajes.show_message("Sin energía suficiente", 1, position="top")
            self.sonido("error")
        elif poder.recarga > 0:
            self.mensajes.show_message(f"{poder.nombre}: recargando...", 1, position="top")
            self.sonido("error")

    # ---------------- Métodos de Scene ----------------
    def _pausar(self):
        self.pausado = True
        self.viendo_controles = False
        self.viendo_opciones = False
        self.mano.soltar()
        for canal in self.bucles.values():
            if canal:
                canal.pause()

    def _reanudar(self):
        self.pausado = False
        self.viendo_controles = False
        self.viendo_opciones = False
        for canal in self.bucles.values():
            if canal:
                canal.unpause()

    def _ver_controles(self):
        self.viendo_controles = True

    def _ver_opciones(self):
        self.viendo_opciones = True

    def _cambiar_volumen(self, atributo, cambio):
        prog = self.game.progreso
        setattr(prog, atributo, getattr(prog, atributo) + cambio)
        self.game.aplicar_volumen()
        if atributo == "volumen_voz":
            self.game.audio.voz("good_job")   # para escuchar cómo queda

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_p, pygame.K_ESCAPE):
                if self.viendo_controles or self.viendo_opciones:
                    self.viendo_controles = False      # Esc en controles u opciones vuelve a la pausa
                    self.viendo_opciones = False
                elif self.pausado:
                    self._reanudar()
                elif self.camara_lenta is None:
                    self._pausar()
                continue
            if self.pausado:
                if self.viendo_controles:
                    self.boton_volver_controles.handle_event(e)
                elif self.viendo_opciones:
                    for b in list(self.botones_opciones):
                        b.handle_event(e)
                else:
                    for b in list(self.botones_pausa):
                        b.handle_event(e)
                continue
            if self.camara_lenta is not None:
                continue   # durante la cámara lenta final no se juega
            if self.es_prueba:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
                    self.panel_prueba.visible = not self.panel_prueba.visible
                    continue
                if e.type == pygame.MOUSEBUTTONDOWN and self.panel_prueba.contiene(e.pos):
                    self.panel_prueba.handle_event(e)
                    continue
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    if self._clic_en_hud(e.pos):
                        pass
                    elif self.es_prueba and self.enemigo_a_crear:
                        self._prueba_crear_enemigo(self.camara.a_mundo(e.pos))
                    else:
                        self._clic(self.camara.a_mundo(e.pos))
                elif e.button == 3:
                    # Clic derecho: si se arrastra mueve la cámara; si es un clic corto cancela el poder
                    self.arrastre = dict(inicio=e.pos[0], camara=self.camara.x, movido=False)
            elif e.type == pygame.MOUSEMOTION and self.arrastre:
                dx = e.pos[0] - self.arrastre["inicio"]
                if abs(dx) > C.ARRASTRE_UMBRAL:
                    self.arrastre["movido"] = True
                if self.arrastre["movido"]:
                    self.camara.ir_a(self.arrastre["camara"] - dx)
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 3:
                if self.arrastre and not self.arrastre["movido"]:
                    self.poder_actual = None
                    self.enemigo_a_crear = None
                self.arrastre = None
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                self.mano.soltar()
            elif e.type == pygame.KEYDOWN:
                if pygame.K_1 <= e.key <= pygame.K_9:
                    self.seleccionar_poder(e.key - pygame.K_1)
                elif e.key == pygame.K_F1 and C.DEBUG:
                    self.ver_fisica = not self.ver_fisica
                elif e.key == pygame.K_F2 and C.DEBUG:
                    # [DEBUG] sube el nivel del poder seleccionado (1 → 2 → 3 → 1)
                    p = self.poder_actual
                    if p is not None:
                        p.nivel = p.nivel % p.nivel_max + 1
                        self.mensajes.show_message(f"[DEBUG] {p.nombre} nivel {p.nivel}", 1, position="top")
                elif e.key == pygame.K_F3 and C.DEBUG:
                    self.energia = C.ENERGIA_MAX   # [DEBUG] energía llena
                    for p in self.poderes:
                        p.recarga = 0                  # [DEBUG] y sin recarga

    def update(self):
        if self.pausado:
            return
        dt_real = self.dt

        # Cámara con teclado (A/D o flechas)
        teclas = pygame.key.get_pressed()
        if self.camara_lenta is None:
            if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
                self.camara.mover(-C.CAMARA_VELOCIDAD * dt_real)
            if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
                self.camara.mover(C.CAMARA_VELOCIDAD * dt_real)

        # Fondo: se mueve según cuánto se movió la cámara (también por arrastre o minimapa)
        self.fondo.update(self.camara.x - self.camara_x_anterior, dt_real)
        self.camara_x_anterior = self.camara.x

        # Peligro, música, latido y narrador (siguen aunque el mundo esté congelado un instante)
        self._actualizar_peligro(dt_real)
        self.base.update(dt_real, self.peligro, self.vidas_base)
        self.narrador.update(dt_real)
        if not self.dijo_inicio and not self.es_prueba:
            self.narrador.decir("inicio")
            self.dijo_inicio = True

        # Congelado de impacto: el mundo no avanza por unos cuadros
        if self.espera_congelado > 0:
            self.espera_congelado -= dt_real
        if self.congelado > 0:
            self.congelado -= 1
            return
        # Cámara lenta final: el mundo avanza más despacio y al terminar se gana
        if self.camara_lenta is not None:
            self.camara_lenta -= dt_real
            if self.camara_lenta <= 0:
                self._ganar()
                return
            dt = dt_real * C.CAMARA_LENTA_ESCALA
        else:
            dt = dt_real

        # El cuerpo del mouse sigue al cursor (con velocidad, para lanzar suave)
        if self.es_prueba:
            if self.trucos["energia_infinita"]:
                self.energia = C.ENERGIA_MAX
            if self.trucos["sin_recarga"]:
                for p in self.poderes:
                    p.recarga = 0
            for c in self.enemigos:
                c.quieto = self.trucos["enemigos_quietos"]

        # La mano lleva lo que tenga agarrado hacia el cursor (antes de avanzar la física)
        self.mano.update(self.mouse_mundo(), dt)

        for p in self.poderes:
            p.update(dt)

        for clave in self.director.update(dt, len(self.enemigos)):
            self._crear_enemigo(clave)

        # Agujeros negros: aplican su atracción antes de avanzar la física
        for c in self.enemigos:
            c.atraida = False
        for a in self.agujeros:
            a.atraer(self.enemigos, dt)

        self.space.step(dt)
        self.enemigos.update(dt)
        for c in list(self.enemigos):
            c.actuar(self, dt)      # curar, animar, pisotón
        self.bloques.update(dt)
        self.bombas.update(dt)
        self.agujeros.update(dt)
        self.barriles.update(dt)
        self.rocas.update()
        self.cristales.update(dt)
        self.efectos.update(dt)
        for r in list(self.rocas):
            if r.position.y > C.ALTO + 200 or r.position.x > self.ancho_mundo + 300:
                self._eliminar(r)

        for barril in list(self.barriles):
            if barril.explotar:
                d = C.BARRIL
                self.explosion(barril.position, d["radio_explosion"], d["fuerza"], d["danio"], excluir=barril)
                self._eliminar(barril)
            elif barril.position.y > C.ALTO + 200 or barril.position.x > self.ancho_mundo + 300:
                self._eliminar(barril)

        for bomba in list(self.bombas):
            if bomba.lista_para_explotar:
                self._explotar(bomba)
            elif bomba.position.y > C.ALTO + 200 or bomba.position.x > self.ancho_mundo + 300:
                self._eliminar(bomba)
        for a in list(self.agujeros):
            if a.terminado:
                a.remove_from_space()

        for b in list(self.bloques):
            if b.destruido or b.position.y > C.ALTO + 200:
                if b.vida <= 0:
                    # Astillas del color del material
                    self.particulas.emit(b.position.x, b.position.y, count=10, speed=(60, 220),
                                         color=b.color, life=(0.4, 0.8), size=(2, 4), gravity=500)
                    self.sonido(f"crujido_{b.material}", 0.7)
                elif b.duracion is not None and b.duracion <= 0:
                    # Se terminó el tiempo del muro: se desvanece en polvo
                    self.particulas.emit(b.position.x, b.position.y, count=5, speed=(10, 50),
                                         color=(200, 200, 200), life=(0.3, 0.6), size=(3, 6),
                                         gravity=-40)
                b.remove_from_space()
        for ef in list(self.efectos):
            if ef.terminado:
                ef.kill()

        if self.tiempo_combo > 0:
            self.tiempo_combo -= dt
            if self.tiempo_combo <= 0:
                self.combo = 0
                for t in self.textos_combo:
                    t.terminar()

        for c in list(self.enemigos):
            if not c.alive():          # ya lo sacó otra explosión en este mismo frame
                continue
            if isinstance(c, Acorazado) and c.armadura_recien_rota:
                c.armadura_recien_rota = False
                self.mensajes.show_message("¡Armadura rota!", 1, position="top")
                self.sonido("armadura")
                self.narrador.decir("armadura")
            if not c.viva:
                self._enemigo_muerto(c)
            elif c.toca_base() or c.position.x < -c.radio:
                # Llegó a la base, o cruzó el borde izquierdo del mapa (aunque sea volando,
                # incluso si lo tiraste vos para atrás): cuenta como que llegó
                antes = self.vidas_base
                if not self.trucos["base_invencible"]:
                    self.vidas_base -= c.danio_base
                for i in range(max(0, self.vidas_base), antes):
                    self.corazones_perdiendo[i] = 0.6   # animación de los corazones perdidos
                self.sonido("base_golpe")
                self.base.golpe(self.particulas)
                if antes > 1 and self.vidas_base == 1:
                    self.narrador.decir("ultima_vida")
                c.al_llegar_a_base(self)
                self._eliminar(c)
                self.flash_base = 0.6
                self.borde_rojo = 1.0
                self.temblor.agregar(C.TEMBLOR_BASE)
            elif c.position.y > C.ALTO + 200:
                self._eliminar(c)

        self.mensajes.update()

        # Alerta: ¿hay algún enemigo en la zona de peligro delante de la base?
        self.alerta_base = False
        for c in self.enemigos:
            if c.position.x < C.BASE_X + C.ZONA_PELIGRO:
                self.alerta_base = True
                if not getattr(c, "alarmado", False):
                    c.alarmado = True              # la alarma suena una vez por enemigo
                    self.sonido("alarma")
                    self.narrador.decir("peligro")
        if self.alerta_base and not self.aviso_base_mostrado and not self.camara.visible(C.BASE_X):
            self.mensajes.show_message("¡Enemigo cerca de la base!", 1.5, position="top")
            self.aviso_base_mostrado = True
        elif not self.alerta_base:
            self.aviso_base_mostrado = False

        # Últimos enemigos
        if not self.es_prueba and not self.aviso_ultimos and self.director.total > C.QUEDAN_ULTIMOS:
            if 0 < self.director.quedan(len(self.enemigos)) <= C.QUEDAN_ULTIMOS:
                self.aviso_ultimos = True
                self.mensajes.show_message("¡Últimos enemigos!", 2, position="top")
                self.narrador.decir("ultimos")

        self._actualizar_bucles()
        for i in list(self.corazones_perdiendo):
            self.corazones_perdiendo[i] -= dt_real
            if self.corazones_perdiendo[i] <= 0:
                del self.corazones_perdiendo[i]

        # Detalles visuales
        self.particulas.update(dt)
        self.temblor.update()
        for t in self.textos_combo:
            t.update(dt_real)
        self.textos_combo = [t for t in self.textos_combo if not t.terminado]
        self.flash_base = max(0.0, self.flash_base - dt_real)
        self.borde_rojo = max(0.0, self.borde_rojo - dt_real * 1.5)

        if self.vidas_base <= 0:
            self.game.change_scene("game_over", id_nivel=self.nivel["id"],
                                     dificultad=self.dificultad, puntos=self.puntos)
        elif (not self.es_prueba and self.camara_lenta is None and self.director.terminado
              and len(self.enemigos) == 0):
            self.camara_lenta = C.CAMARA_LENTA_DURACION
            self.narrador.decir("victoria")
            self.mano.soltar()
            self.poder_actual = None

    def _actualizar_peligro(self, dt):
        """Calcula el nivel de peligro (0 a 1) y con eso mezcla la música y hace sonar el latido."""
        cercania = 0.0
        if self.enemigos:
            x = min(c.position.x for c in self.enemigos)
            cercania = (C.PELIGRO_DISTANCIA - (x - C.BASE_X)) / C.PELIGRO_DISTANCIA
            cercania = max(0.0, min(1.0, cercania))
        vidas = 1 - max(0, self.vidas_base) / self.vidas_max
        cantidad = min(1.0, len(self.enemigos) / getattr(self.director, "max_vivos", 10))
        objetivo = (C.PELIGRO_PESO_CERCANIA * cercania + C.PELIGRO_PESO_VIDAS * vidas
                    + C.PELIGRO_PESO_CANTIDAD * cantidad)
        if any(getattr(c, "es_jefe", False) for c in self.enemigos):
            objetivo = max(objetivo, C.PELIGRO_JEFE)
        objetivo = max(0.0, min(1.0, objetivo))
        velocidad = C.PELIGRO_SUBIDA if objetivo > self.peligro else C.PELIGRO_BAJADA
        cambio = max(-velocidad * dt, min(velocidad * dt, objetivo - self.peligro))
        self.peligro += cambio

        desde, hasta = C.PELIGRO_MUSICA
        tension = (self.peligro - desde) / (hasta - desde)
        percusion = 1.0 if self.peligro >= C.PELIGRO_PERCUSION or self.combo >= 3 else 0.0
        self.game.audio.mezclar_musica(tension, percusion)
        self.game.audio.actualizar_musica(dt)

        if self.vidas_base == 1:
            self.espera_latido -= dt
            if self.espera_latido <= 0:
                self.sonido("latido")
                self.espera_latido = 1.1 - 0.5 * self.peligro   # más rápido con más peligro

    @staticmethod
    def _crear_vineta():
        """Borde rojo degradado (más fuerte en los bordes) para el peligro alto."""
        vineta = pygame.Surface((C.ANCHO, C.ALTO), pygame.SRCALPHA)
        pasos = 55
        for i in range(pasos):
            alfa = int(255 * (1 - i / pasos) ** 2)
            pygame.draw.rect(vineta, (200, 0, 0, alfa), (i, i, C.ANCHO - 2 * i, C.ALTO - 2 * i), 1)
        return vineta

    def _ganar(self):
        # Estrellas de desempeño según cómo quedó la base
        if self.vidas_base == self.vidas_max:
            desempeno = 3
        elif self.vidas_base > self.vidas_max / 2:
            desempeno = 2
        else:
            desempeno = 1
        nuevo = self.game.progreso.registrar_victoria(self.nivel["id"], self.dificultad, desempeno)
        self.game.change_scene("victoria", id_nivel=self.nivel["id"], dificultad=self.dificultad,
                                 puntos=self.puntos, desempeno=desempeno, nuevo_nivel=nuevo)

    # ---------------- Dibujo ----------------
    def draw(self, surface):
        mundo = self.capa_mundo
        self._dibujar_mundo(mundo)
        # Fondo con profundidad (detrás de todo), después el recorte de lo que ve la cámara.
        # El mundo se sacude; el fondo y el HUD no.
        self.fondo.draw(surface)
        vista = pygame.Rect(self.camara.x, 0, C.ANCHO, C.ALTO)
        surface.blit(mundo, self.temblor.offset, area=vista)
        self.fondo.draw_frente(surface)
        self._dibujar_hud(surface)
        if self.pausado:
            self.panel_pausa.draw(surface)
            if self.viendo_controles:
                self.panel_pausa.draw(surface)   # más oscuro para leer mejor
                dibujar_controles(surface, 120)
                self.boton_volver_controles.draw(surface)
            elif self.viendo_opciones:
                self.panel_pausa.draw(surface)
                t = E.titulo("Opciones", 64)
                surface.blit(t, t.get_rect(center=(C.ANCHO // 2, 130)))
                prog = self.game.progreso
                for y, nombre, atributo in self.filas_volumen:
                    t = self.fuente.render(f"{nombre}: {round(getattr(prog, atributo) * 100)}%", True,
                                           (255, 255, 255))
                    surface.blit(t, t.get_rect(center=(C.ANCHO // 2, y + 25)))
                for b in self.botones_opciones:
                    b.draw(surface)
            else:
                t = E.titulo("PAUSA", 80)
                surface.blit(t, t.get_rect(center=(C.ANCHO // 2, 150)))
                for b in self.botones_pausa:
                    b.draw(surface)
            pygame.mouse.set_visible(True)
        else:
            self._dibujar_cursor(surface)

    def _dibujar_sombra(self, surface, x, alto_sobre_suelo, ancho):
        """Elipse en el suelo que se achica y aclara cuanto más alto está el objeto."""
        if alto_sobre_suelo < 4:
            return
        prop = min(1.0, alto_sobre_suelo / 400)
        w = max(6, int(ancho * (1 - 0.6 * prop)))
        h = max(3, w // 4)
        sombra = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(sombra, (0, 0, 0, int(110 * (1 - 0.7 * prop))), sombra.get_rect())
        surface.blit(sombra, sombra.get_rect(center=(x, self.terreno.superficie(x))))

    def _dibujar_mundo(self, surface):
        surface.fill((0, 0, 0, 0))   # transparente: detrás se ve el fondo
        self.terreno.dibujar(surface, self.fondo.color_suelo)
        self.base.dibujar_plaza(surface)
        self.base.dibujar_empalizada(surface)
        self.base.draw(surface, self.flash_base > 0 and int(self.flash_base * 12) % 2 == 0)
        self.base.dibujar_personas(surface)

        # Sombras de lo que está en el aire
        piso = self.terreno.superficie
        for c in self.enemigos:
            x = c.position.x
            self._dibujar_sombra(surface, x, piso(x) - c.position.y - c.radio, c.radio * 2)
        for bomba in self.bombas:
            x = bomba.position.x
            self._dibujar_sombra(surface, x, piso(x) - bomba.position.y - bomba.tam, bomba.tam * 2)
        for barril in self.barriles:
            alto = piso(barril.position.x) - barril.position.y - C.BARRIL["alto"] / 2
            self._dibujar_sombra(surface, barril.position.x, alto, C.BARRIL["ancho"])
        for r in self.rocas:
            x = r.position.x
            self._dibujar_sombra(surface, x, piso(x) - r.position.y - r.radio, r.radio * 2)

        for cristal in self.cristales:
            cristal.draw(surface)
        for b in self.bloques:
            b.draw(surface)
        for c in self.enemigos:
            c.draw(surface)
        for barril in self.barriles:
            barril.draw(surface)
        for r in self.rocas:
            r.draw(surface)
        for a in self.agujeros:
            a.draw(surface)
        for bomba in self.bombas:
            bomba.draw(surface)
        for ef in self.efectos:
            ef.draw(surface)
        self.particulas.draw(surface)
        self.mano.draw(surface)

        if self.ver_fisica:
            self.space.debug_draw(self.dibujo_debug)

    def _dibujar_hud(self, surface):
        # Vista previa del poder seleccionado en el cursor
        mx, my = pygame.mouse.get_pos()
        clave = self.poder_actual.clave if self.poder_actual else None
        if clave == "agujero":
            pygame.draw.circle(surface, (150, 90, 230), (mx, my), self.poder_actual.stats["radio"], 1)
        elif clave == "rayo":
            pygame.draw.circle(surface, (255, 240, 80), (mx, my), self.poder_actual.RADIO_IMPACTO, 1)
        elif clave == "muro":
            t = C.TAM_BLOQUE
            w, h = C.MURO_COLUMNAS * t, C.MURO_FILAS * t
            suelo_y = self.terreno.superficie(self.camara.a_mundo((mx, my))[0])
            pygame.draw.rect(surface, (255, 255, 255), (mx - w // 2, suelo_y - h, w, h), 1)

        self._dibujar_flechas(surface)

        hud.dibujar_corazones(surface, self.vidas_base, self.vidas_max, self.corazones_perdiendo)
        surface.blit(self.fuente.render(f"Puntos: {self.puntos}", True, C.COLOR_TEXTO), (10, 44))
        info = f"{self.nivel['nombre']} · {C.DIFICULTADES[self.dificultad]['nombre']}"
        t = self.fuente_chica.render(info, True, C.COLOR_TEXTO)
        surface.blit(t, t.get_rect(topright=(C.ANCHO - 10, 10)))

        # Barra de enemigos que quedan (arriba al centro; no en el nivel de prueba)
        if not self.es_prueba:
            quedan = self.director.quedan(len(self.enemigos))
            ancho, x, y = 300, C.ANCHO // 2 - 150, 6
            pygame.draw.rect(surface, (40, 40, 40), (x, y, ancho, 10), border_radius=5)
            hechos = max(0.0, 1 - quedan / self.director.total)   # el divisor puede sumar enemigos
            pygame.draw.rect(surface, (200, 80, 60), (x, y, int(ancho * hechos), 10), border_radius=5)
            # Con más peligro el número se pone rojo y late
            p = self.peligro
            color = tuple(int(a + (b - a) * p) for a, b in zip(C.COLOR_TEXTO, (210, 25, 25)))
            t = self.fuente_chica.render(f"Quedan {quedan}", True, color)
            if p > 0.5:
                escala = 1 + 0.12 * (p - 0.5) * 2 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 90))
                t = pygame.transform.smoothscale(t, (int(t.get_width() * escala), int(t.get_height() * escala)))
            surface.blit(t, t.get_rect(midleft=(x + ancho + 10, y + 5)))

        self._dibujar_barra_jefe(surface)

        hud.dibujar_energia(surface, self.fuente_chica, self.energia)
        hud.dibujar_minimapa(surface, self.ancho_mundo, self.camara.x, self.enemigos, self.alerta_base)
        hud.dibujar_poderes(surface, self.fuente_chica, self.poderes, self.poder_actual)
        if self.es_prueba:
            if self.enemigo_a_crear and not self.panel_prueba.contiene((mx, my)):
                # Vista previa: círculo del tamaño del enemigo que se va a crear
                datos = C.ENEMIGOS[self.enemigo_a_crear]
                pygame.draw.circle(surface, datos["color"], (mx, my), datos["radio"], 2)
            self.panel_prueba.draw(surface)
        self.mensajes.draw()
        for t in self.textos_combo:
            t.draw(surface, (C.ANCHO // 2, 105))
        if self.combo >= 2 and self.tiempo_combo > 0:
            # Barrita del tiempo que queda para seguir el combo
            ancho = 160
            prop = self.tiempo_combo / C.TIEMPO_COMBO
            x, y = C.ANCHO // 2 - ancho // 2, 135
            pygame.draw.rect(surface, (40, 40, 40), (x, y, ancho, 6), border_radius=3)
            pygame.draw.rect(surface, (255, 200, 60), (x, y, int(ancho * prop), 6), border_radius=3)

        # Borde rojo suave que late con el peligro alto
        if self.peligro > C.PELIGRO_BORDE:
            fuerza = (self.peligro - C.PELIGRO_BORDE) / (1 - C.PELIGRO_BORDE)
            pulso = 0.7 + 0.3 * math.sin(pygame.time.get_ticks() / 1000 * (4 + 4 * self.peligro))
            self.vineta.set_alpha(int(110 * fuerza * pulso))
            surface.blit(self.vineta, (0, 0))

        # Borde rojo cuando la base pierde vida
        if self.borde_rojo > 0:
            borde = pygame.Surface((C.ANCHO, C.ALTO), pygame.SRCALPHA)
            pygame.draw.rect(borde, (220, 0, 0, int(140 * self.borde_rojo)), borde.get_rect(), 22)
            surface.blit(borde, (0, 0))

    def _dibujar_barra_jefe(self, surface):
        """Barra de vida grande arriba al centro mientras haya un jefe vivo."""
        jefe = next((c for c in self.enemigos if getattr(c, "es_jefe", False) and c.viva), None)
        if jefe is None:
            return
        ancho, alto = 360, 16
        x, y = C.ANCHO // 2 - ancho // 2, 165   # debajo del texto de combo
        nombre = self.fuente_chica.render(jefe.datos["nombre"], True, (255, 230, 120))
        sombra = self.fuente_chica.render(jefe.datos["nombre"], True, (30, 20, 20))
        surface.blit(sombra, sombra.get_rect(midright=(x - 8, y + alto // 2 + 2)))
        surface.blit(nombre, nombre.get_rect(midright=(x - 10, y + alto // 2)))
        pygame.draw.rect(surface, (40, 20, 25), (x, y, ancho, alto), border_radius=6)
        lleno = int(ancho * max(0.0, jefe.vida / jefe.vida_max))
        if lleno > 0:
            pygame.draw.rect(surface, (210, 40, 50), (x, y, lleno, alto), border_radius=6)
        pygame.draw.rect(surface, (255, 220, 120), (x, y, ancho, alto), 2, border_radius=6)

    def _flecha(self, surface, x, y, hacia_derecha, color, escala=1.0):
        largo, alto = 26 * escala, 17 * escala
        if hacia_derecha:
            puntos = [(x, y), (x - largo, y - alto), (x - largo, y + alto)]
        else:
            puntos = [(x, y), (x + largo, y - alto), (x + largo, y + alto)]
        pygame.draw.polygon(surface, color, puntos)
        pygame.draw.polygon(surface, (40, 15, 0), puntos, 2)

    def _dibujar_flechas(self, surface):
        """Flechas a media altura para los enemigos que no están en pantalla."""
        y = C.ALTO // 2 - 30
        pulso = (math.sin(pygame.time.get_ticks() / 90) + 1) / 2
        derecha = [c for c in self.enemigos if c.position.x > self.camara.x + C.ANCHO]
        izquierda = [c for c in self.enemigos if c.position.x < self.camara.x]
        if derecha:
            # Más lejos de la base: amarilla, tranquila
            self._flecha(surface, C.ANCHO - 8, y, True, (255, 220, 60))
        if izquierda:
            cerca_base = [c for c in izquierda if c.position.x < C.BASE_X + C.ZONA_PELIGRO]
            if cerca_base:
                # Peligro: hay enemigos cerca de la base y no los estás viendo
                brillo = pygame.Surface((60, C.ALTO), pygame.SRCALPHA)
                for k in range(60):
                    alfa = int((1 - k / 60) * (70 + 90 * pulso))
                    pygame.draw.line(brillo, (255, 0, 0, alfa), (k, 0), (k, C.ALTO))
                surface.blit(brillo, (0, 0))
                self._flecha(surface, 8, y, False, (255, int(40 + 60 * pulso), 30),
                             escala=1.4 + 0.2 * pulso)
            else:
                # Te pasaron, pero todavía lejos de la base: naranja
                self._flecha(surface, 8, y, False, (255, 150, 40))

    def _dibujar_cursor(self, surface):
        if self.poder_actual is not None:
            self.cursores_poder[self.poder_actual.clave].draw(surface)
        else:
            self.cursor_mano.draw(surface, hovered=self.mano.agarrada is not None)
