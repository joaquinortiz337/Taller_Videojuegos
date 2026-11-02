# juego/scenes/mejoras_scene.py
import pygame

from juego.scenes.base_menu import MenuBase
from juego.ui_extra import SoundButton, dibujar_estrella, dibujar_texto_multilinea
from juego.cursores import icono_poder
from juego import config as C
from juego import estilo as E


class BotonMejora(SoundButton):
    """'Mejorar' con el costo en estrellas. Gris si no alcanzan; dorado 'Máximo' en el último nivel."""

    def __init__(self, x, y, ancho, alto, accion, sonido, sonido_error):
        super().__init__(x, y, ancho, alto, "Mejorar", accion, sonido)
        self.font = E.fuente(22)
        self.sonido_error = sonido_error
        self.costo = None
        self.habilitado = True

    def handle_event(self, event):
        if self.habilitado:
            super().handle_event(event)
        elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
              and self.rect.collidepoint(event.pos) and self.costo is not None and self.sonido_error):
            self.sonido_error.play()   # no alcanzan las estrellas

    def draw(self, surface):
        if self.costo is None:   # nivel máximo
            self.activo = False
            self.color_arriba = self.color_abajo = None
            fondo = E.degrade_redondeado(self.rect.size, (255, 215, 95), (205, 135, 35), 14)
            surface.blit(fondo, self.rect)
            pygame.draw.rect(surface, E.DORADO_CLARO, self.rect, 2, border_radius=14)
            t = self.font.render("Máximo", True, (70, 35, 10))
            surface.blit(t, t.get_rect(center=self.rect.center))
            return
        self.activo = self.habilitado
        r = self.dibujar_base(surface)
        color = E.TEXTO if self.habilitado else (165, 165, 175)
        texto = self.font.render(self.text, True, color)
        costo = self.font.render(str(self.costo), True, color)
        ancho = texto.get_width() + 12 + 20 + costo.get_width()
        x = r.centerx - ancho // 2
        cy = r.centery + 1
        surface.blit(texto, texto.get_rect(midleft=(x, cy)))
        x += texto.get_width() + 12
        dibujar_estrella(surface, (x + 8, cy), 9, llena=self.habilitado)
        surface.blit(costo, costo.get_rect(midleft=(x + 20, cy)))


def _icono_base():
    """Torrecita para la tarjeta de la base."""
    img = pygame.Surface((56, 56), pygame.SRCALPHA)
    pygame.draw.rect(img, (150, 145, 138), (14, 18, 28, 36))
    for x in (14, 25, 36):
        pygame.draw.rect(img, (150, 145, 138), (x, 11, 6, 8))
    pygame.draw.rect(img, (95, 60, 30), (23, 38, 10, 16))
    pygame.draw.rect(img, (255, 210, 110), (24, 24, 8, 8))
    pygame.draw.line(img, (60, 50, 40), (28, 11), (28, 1), 2)
    pygame.draw.polygon(img, (40, 90, 200), [(29, 1), (40, 4), (29, 7)])
    pygame.draw.rect(img, (70, 65, 60), (14, 18, 28, 36), 2)
    return img


class MejorasScene(MenuBase):
    """Gastar las estrellas ganadas en subir el nivel de los poderes."""
    TITULO = "Mejoras"
    ANCHO_TARJETA = 172
    ALTO_TARJETA = 300
    Y_TARJETA = 165

    def __init__(self, game):
        super().__init__(game)
        sonidos = self.game.assets.sounds
        self.prog = self.game.progreso
        self.fuente_nombre = E.fuente(26)
        self.fuente_texto = pygame.font.Font(None, 23)
        self.iconos = {clave: pygame.transform.scale(icono_poder(clave), (56, 56)) for clave in C.ORDEN_PODERES}
        self.iconos["base"] = _icono_base()
        self.brillo = {clave: 0.0 for clave in C.ORDEN_MEJORAS}   # destello al mejorar

        separacion = 14
        cantidad = len(C.ORDEN_MEJORAS)
        total = cantidad * self.ANCHO_TARJETA + (cantidad - 1) * separacion
        x0 = (C.ANCHO - total) // 2
        self.tarjetas = {}
        self.botones_mejora = {}
        for i, clave in enumerate(C.ORDEN_MEJORAS):
            r = pygame.Rect(x0 + i * (self.ANCHO_TARJETA + separacion), self.Y_TARJETA,
                            self.ANCHO_TARJETA, self.ALTO_TARJETA)
            self.tarjetas[clave] = r
            b = BotonMejora(r.x + 15, r.bottom - 57, r.width - 30, 44,
                            lambda c=clave: self._mejorar(c), sonidos.get("click"), sonidos.get("error"))
            self.botones_mejora[clave] = b
            self.botones.append(b)

        self.boton(20, C.ALTO - 70, 160, 50, "Volver", lambda: self.game.change_scene("niveles"))
        self.boton(C.ANCHO - 280, C.ALTO - 70, 260, 50, "Reiniciar mejoras", self._reiniciar)
        self._actualizar_botones()

    def _actualizar_botones(self):
        disponibles = self.prog.estrellas_disponibles()
        for clave, b in self.botones_mejora.items():
            b.costo = self.prog.costo_mejora(clave)
            b.habilitado = b.costo is not None and b.costo <= disponibles

    def _mejorar(self, clave):
        if self.prog.mejorar(clave):
            self.game.audio.reproducir("mejora")
            self.brillo[clave] = 0.5
        self._actualizar_botones()

    def _reiniciar(self):
        self.prog.reiniciar_mejoras()
        self._actualizar_botones()

    def update(self):
        for clave in self.brillo:
            self.brillo[clave] = max(0.0, self.brillo[clave] - 1 / C.FPS)

    def draw(self, surface):
        self.dibujar_fondo(surface)

        # Estrellas disponibles (en una pastilla)
        disponibles = self.prog.estrellas_disponibles()
        texto = self.fuente.render(f"Estrellas disponibles: {disponibles}", True, E.TEXTO)
        ganadas = self.fuente_chica.render(f"de {self.prog.estrellas_ganadas()} ganadas", True, E.TEXTO_SUAVE)
        ancho = texto.get_width() + ganadas.get_width() + 70
        pastilla = pygame.Rect(0, 0, ancho, 40)
        pastilla.center = (C.ANCHO // 2, 132)
        pygame.draw.rect(surface, (20, 14, 45), pastilla, border_radius=20)
        pygame.draw.rect(surface, E.DORADO, pastilla, 2, border_radius=20)
        dibujar_estrella(surface, (pastilla.x + 24, pastilla.centery), 12, llena=True)
        surface.blit(texto, texto.get_rect(midleft=(pastilla.x + 44, pastilla.centery)))
        surface.blit(ganadas, ganadas.get_rect(midleft=(pastilla.x + 54 + texto.get_width(), pastilla.centery + 2)))

        for clave in C.ORDEN_MEJORAS:
            self._dibujar_tarjeta(surface, clave)
        for b in self.botones:
            b.draw(surface)

    def _dibujar_tarjeta(self, surface, clave):
        r = self.tarjetas[clave]
        datos = C.PODERES.get(clave, C.MEJORA_BASE)
        nivel = self.prog.nivel_poder(clave)
        maximo = len(datos["niveles"])

        if self.brillo[clave] > 0:
            ancho = 3 + int(8 * self.brillo[clave])
            pygame.draw.rect(surface, E.DORADO_CLARO, r.inflate(ancho * 2, ancho * 2), ancho, border_radius=18)
        E.panel(surface, r)

        # Círculo detrás del ícono
        pygame.draw.circle(surface, (60, 50, 115), (r.centerx, r.y + 44), 34)
        pygame.draw.circle(surface, E.DORADO, (r.centerx, r.y + 44), 34, 2)
        icono = self.iconos[clave]
        surface.blit(icono, icono.get_rect(center=(r.centerx, r.y + 44)))
        E.texto_sombra(surface, self.fuente_nombre, datos["nombre"], E.TEXTO, (r.centerx, r.y + 96))

        # Nivel actual: puntitos
        for n in range(maximo):
            centro = (r.centerx - (maximo - 1) * 14 + n * 28, r.y + 124)
            if n < nivel:
                pygame.draw.circle(surface, (255, 210, 50), centro, 9)
            pygame.draw.circle(surface, E.DORADO_CLARO if n < nivel else (150, 145, 165), centro, 9, 2)

        if nivel < maximo:
            titulo, descripcion = "Próximo nivel:", datos["niveles"][nivel]["descripcion"]
        else:
            titulo, descripcion = "Nivel máximo:", datos["niveles"][nivel - 1]["descripcion"]
        t = self.fuente_texto.render(titulo, True, E.DORADO_CLARO)
        surface.blit(t, (r.x + 14, r.y + 146))
        dibujar_texto_multilinea(surface, self.fuente_texto, descripcion, E.TEXTO,
                                 r.x + 14, r.y + 168, r.width - 28)

    def on_enter(self):
        self.game.audio.musica("menu")
