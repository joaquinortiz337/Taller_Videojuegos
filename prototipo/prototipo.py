"""
Prototipo del núcleo (inspirado en Slammings)
- Las criaturas aparecen a la derecha y caminan hacia la base (izquierda).
- Clic izquierdo: agarrar una criatura. Movés el mouse y la soltás: sale volando.
- El daño depende de la fuerza del impacto (callback post_solve de Pymunk).
- Si 5 criaturas llegan a la base: Game Over. R = reiniciar. F1 = ver física.
"""
import random
import pygame
import pymunk
import pymunk.pygame_util

ANCHO, ALTO = 1000, 600
SUELO_Y = 540
GROSOR_SUELO = 4      # radio del segmento del suelo
BASE_X = 70
FPS = 60

TIPO_CRIATURA = 1

# Tipos de criatura: radio, masa, vida, velocidad, color
TIPOS = {
    "chica":   dict(radio=14, masa=1, vida=30,  vel=95, color=(70, 110, 170)),
    "mediana": dict(radio=21, masa=3, vida=60,  vel=65, color=(150, 120, 40)),
    "grande":  dict(radio=30, masa=8, vida=130, vel=40, color=(160, 30, 50)),
}

UMBRAL_IMPACTO = 450   # cambio de velocidad (px/s) a partir del cual duele
FACTOR_DANIO = 0.08    # cuánto daño por cada px/s por encima del umbral
VEL_MAX_LANZAMIENTO = 1600


class Criatura:
    def __init__(self, espacio, tipo, x):
        datos = TIPOS[tipo]
        self.tipo = tipo
        self.radio = datos["radio"]
        self.vida_max = datos["vida"]
        self.vida = datos["vida"]
        self.vel = datos["vel"]
        self.color = datos["color"]
        self.agarrada = False
        self.aturdida = 0.0  # segundos sin caminar después de un golpe

        # Momento infinito = no rota (siempre "de pie"), más fácil de dibujar
        self.cuerpo = pymunk.Body(datos["masa"], float("inf"))
        self.cuerpo.position = (x, SUELO_Y - GROSOR_SUELO - self.radio - 1)
        self.forma = pymunk.Circle(self.cuerpo, self.radio)
        self.forma.friction = 0.8
        self.forma.elasticity = 0.3
        self.forma.collision_type = TIPO_CRIATURA
        espacio.add(self.cuerpo, self.forma)

    def en_suelo(self):
        return self.cuerpo.position.y >= SUELO_Y - GROSOR_SUELO - self.radio - 3

    def actualizar(self, dt):
        if self.aturdida > 0:
            self.aturdida -= dt
            return
        # Solo camina si está apoyada, quieta en vertical y nadie la agarra
        if not self.agarrada and self.en_suelo() and abs(self.cuerpo.velocity.y) < 40:
            self.cuerpo.velocity = (-self.vel, self.cuerpo.velocity.y)

    def recibir_danio(self, cantidad):
        self.vida -= cantidad
        self.aturdida = 0.6

    def dibujar(self, pantalla):
        x, y = int(self.cuerpo.position.x), int(self.cuerpo.position.y)
        r = self.radio
        pygame.draw.circle(pantalla, self.color, (x, y), r)
        # ojo amarillo mirando hacia la izquierda
        pygame.draw.circle(pantalla, (240, 220, 40), (x - r // 3, y - r // 4), max(3, r // 4))
        pygame.draw.circle(pantalla, (0, 0, 0), (x - r // 3 - 1, y - r // 4), max(1, r // 8))
        # barra de vida
        ancho = r * 2
        proporcion = max(0, self.vida) / self.vida_max
        pygame.draw.rect(pantalla, (60, 60, 60), (x - r, y - r - 10, ancho, 5))
        pygame.draw.rect(pantalla, (50, 200, 70), (x - r, y - r - 10, int(ancho * proporcion), 5))


class Juego:
    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("Prototipo núcleo - agarrar y revolear")
        self.reloj = pygame.time.Clock()
        self.fuente = pygame.font.SysFont(None, 30)
        self.fuente_grande = pygame.font.SysFont(None, 80)
        self.ver_fisica = False
        self.reiniciar()

    def reiniciar(self):
        self.espacio = pymunk.Space()
        self.espacio.gravity = (0, 900)
        self.dibujo_debug = pymunk.pygame_util.DrawOptions(self.pantalla)

        # Suelo y paredes (estáticos)
        estaticos = [
            pymunk.Segment(self.espacio.static_body, (-100, SUELO_Y), (ANCHO + 200, SUELO_Y), GROSOR_SUELO),
            pymunk.Segment(self.espacio.static_body, (ANCHO + 150, 0), (ANCHO + 150, SUELO_Y), 4),
        ]
        for s in estaticos:
            s.friction = 1.0
            s.elasticity = 0.3
        self.espacio.add(*estaticos)

        # Callback de colisión: daño según el impulso del choque
        self.espacio.on_collision(TIPO_CRIATURA, None, post_solve=self.al_chocar)

        # Cuerpo invisible que sigue al mouse para poder agarrar
        self.cuerpo_mouse = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.union_mouse = None
        self.criatura_agarrada = None

        self.criaturas = {}          # forma -> Criatura
        self.tiempo_spawn = 0.0
        self.puntos = 0
        self.vidas_base = 5
        self.game_over = False

    # ---------- Física ----------
    def al_chocar(self, arbitro, espacio, datos):
        impulso = arbitro.total_impulse.length
        for forma in arbitro.shapes:
            criatura = self.criaturas.get(forma)
            if criatura is None:
                continue
            # cambio de velocidad = impulso / masa (las livianas sufren más)
            delta_v = impulso / criatura.cuerpo.mass
            if delta_v > UMBRAL_IMPACTO:
                criatura.recibir_danio((delta_v - UMBRAL_IMPACTO) * FACTOR_DANIO)

    def crear_criatura(self):
        tipo = random.choices(["chica", "mediana", "grande"], weights=[5, 3, 1])[0]
        c = Criatura(self.espacio, tipo, ANCHO + 40)
        self.criaturas[c.forma] = c

    def eliminar_criatura(self, c):
        if c is self.criatura_agarrada:
            self.soltar()
        self.espacio.remove(c.cuerpo, c.forma)
        del self.criaturas[c.forma]

    # ---------- Mouse ----------
    def agarrar(self, pos):
        info = self.espacio.point_query_nearest(pos, 5, pymunk.ShapeFilter())
        if info is None or info.shape not in self.criaturas:
            return
        c = self.criaturas[info.shape]
        self.cuerpo_mouse.position = pos
        self.union_mouse = pymunk.PivotJoint(self.cuerpo_mouse, c.cuerpo, (0, 0), (0, 0))
        self.union_mouse.max_force = 60000 * c.cuerpo.mass
        self.union_mouse.error_bias = (1 - 0.25) ** 60
        self.espacio.add(self.union_mouse)
        c.agarrada = True
        self.criatura_agarrada = c

    def soltar(self):
        if self.union_mouse is not None:
            self.espacio.remove(self.union_mouse)
            self.union_mouse = None
        c = self.criatura_agarrada
        if c is not None:
            c.agarrada = False
            v = c.cuerpo.velocity
            if v.length > VEL_MAX_LANZAMIENTO:
                c.cuerpo.velocity = v.scale_to_length(VEL_MAX_LANZAMIENTO)
        self.criatura_agarrada = None

    # ---------- Bucle ----------
    def manejar_eventos(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    self.reiniciar()
                elif e.key == pygame.K_F1:
                    self.ver_fisica = not self.ver_fisica
            if not self.game_over:
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.agarrar(e.pos)
                elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    self.soltar()
        return True

    def actualizar(self, dt):
        if self.game_over:
            return
        # El cuerpo del mouse sigue al cursor (con velocidad, para lanzar suave)
        pos_mouse = pygame.mouse.get_pos()
        nueva = pymunk.Vec2d(*pos_mouse)
        self.cuerpo_mouse.velocity = (nueva - self.cuerpo_mouse.position) / dt
        self.cuerpo_mouse.position = nueva

        self.tiempo_spawn -= dt
        if self.tiempo_spawn <= 0:
            self.crear_criatura()
            self.tiempo_spawn = random.uniform(1.2, 2.5)

        for c in list(self.criaturas.values()):
            c.actualizar(dt)

        self.espacio.step(dt)

        for c in list(self.criaturas.values()):
            if c.vida <= 0:
                self.puntos += {"chica": 10, "mediana": 25, "grande": 60}[c.tipo]
                self.eliminar_criatura(c)
            elif c.cuerpo.position.x < BASE_X and c.en_suelo():
                self.vidas_base -= 1
                self.eliminar_criatura(c)
            elif c.cuerpo.position.y > ALTO + 200:   # se cayó del mundo
                self.eliminar_criatura(c)

        if self.vidas_base <= 0:
            self.game_over = True

    def dibujar(self):
        p = self.pantalla
        p.fill((170, 205, 190))
        pygame.draw.rect(p, (70, 90, 60), (0, SUELO_Y, ANCHO, ALTO - SUELO_Y))
        pygame.draw.rect(p, (110, 80, 50), (0, SUELO_Y - 120, BASE_X, 120))  # base

        for c in self.criaturas.values():
            c.dibujar(p)

        if self.union_mouse is not None:
            a = self.criatura_agarrada.cuerpo.position
            pygame.draw.line(p, (255, 255, 255), (a.x, a.y), pygame.mouse.get_pos(), 2)

        if self.ver_fisica:
            self.espacio.debug_draw(self.dibujo_debug)

        p.blit(self.fuente.render(f"Puntos: {self.puntos}", True, (0, 0, 0)), (10, 10))
        p.blit(self.fuente.render(f"Base: {self.vidas_base}", True, (0, 0, 0)), (10, 40))

        if self.game_over:
            t = self.fuente_grande.render("GAME OVER", True, (150, 0, 0))
            p.blit(t, t.get_rect(center=(ANCHO // 2, ALTO // 2 - 30)))
            t2 = self.fuente.render("R para reiniciar", True, (0, 0, 0))
            p.blit(t2, t2.get_rect(center=(ANCHO // 2, ALTO // 2 + 30)))

        pygame.display.flip()

    def ejecutar(self):
        corriendo = True
        while corriendo:
            dt = 1 / FPS
            corriendo = self.manejar_eventos()
            self.actualizar(dt)
            self.dibujar()
            self.reloj.tick(FPS)
        pygame.quit()


if __name__ == "__main__":
    Juego().ejecutar()